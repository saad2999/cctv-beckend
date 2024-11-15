import json
import cv2
import base64
import threading
import time
import os
import logging
from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from ultralytics import YOLO
from django.conf import settings
from .models import Camera, DetectedFrame

logger = logging.getLogger('custom_logger')

class VideoStreamConsumer(WebsocketConsumer):
    def connect(self):
        self.camera_id = self.scope['url_route']['kwargs']['camera_id']
        self.camera_group_name = f'camera_{self.camera_id}'
        
        logger.info(f"Connecting to camera stream: Camera ID {self.camera_id}")

        # Join camera group
        self.channel_layer.group_add(
            self.camera_group_name,
            self.channel_name
        )

        self.accept()
        logger.info(f"WebSocket connection accepted for Camera ID {self.camera_id}")

        # Initialize YOLO model
        self.model = YOLO('yolov8s.pt')
        logger.debug("YOLO model initialized")

        # Create output directory
        output_dir = os.path.join(settings.MEDIA_ROOT, 'detected_frames')
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory created: {output_dir}")

        # Create a unique filename for this stream
        output_filename = f'output_camera_{self.camera_id}.mp4'
        self.output_path = os.path.join(output_dir, output_filename)
        logger.info(f"Output file path set: {self.output_path}")

        # Initialize video writer
        self.writer = None

        # Start streaming in a new thread
        self.streaming_thread = threading.Thread(target=self.stream_video)
        self.streaming_thread.daemon = True  # Daemonize thread
        self.streaming_thread.start()
        logger.info(f"Started streaming thread for Camera ID {self.camera_id}")

    def disconnect(self, close_code):
        logger.warning(f"Disconnecting from camera stream: Camera ID {self.camera_id}, Close code: {close_code}")
        
        # Leave camera group
        self.channel_layer.group_discard(
            self.camera_group_name,
            self.channel_name
        )
        
        if hasattr(self, 'writer') and self.writer:
            self.writer.release()
            logger.info("Video writer released")

        logger.info(f"WebSocket connection closed for Camera ID {self.camera_id}")
        raise StopConsumer()

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        logger.info(f"Received message: {message}")

        if message == 'stop_stream':
            logger.warning("Stopping video stream as per request")
            self.close()

    def stream_video(self):
        logger.info(f"Starting video stream for Camera ID {self.camera_id}")

        try:
            camera = self.get_camera()
            cap = cv2.VideoCapture(0)  # Open the webcam

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(self.output_path, fourcc, 20.0, 
                                          (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                                           int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
            logger.debug(f"Video writer initialized with output path: {self.output_path}")

            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to read frame from webcam")
                    break

                # Perform object detection
                results = self.model(frame)

                # If the model detects objects, it will be in the results object
                # results[0] refers to the first result, usually, in the format of a list of detections
                annotated_frame = results[0].plot()  # Annotate the frame
                logger.debug("Object detection and annotation complete")

                # Save detection results to the database
                detection_result = self.get_detection_result(results)

                # Create DetectedFrame entry in the database
                detected_frame = DetectedFrame(
                    camera=camera,
                    frame_image=self.save_frame_to_file(annotated_frame),
                    detection_result=detection_result
                )
                detected_frame.save()
                logger.debug("Detection saved to the database")

                # Write frame to video file
                self.writer.write(annotated_frame)
                logger.debug("Frame written to video file")

                # Encode frame to base64 for sending over WebSocket
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                self.send(text_data=json.dumps({
                    'frame': frame_base64
                }))
                logger.debug("Frame sent to WebSocket")

                time.sleep(0.1)  # Adjust this value to control frame rate

        except Exception as e:
            logger.error(f"Error in stream_video: {str(e)}")
        finally:
            if cap.isOpened():
                cap.release()
                logger.debug("Webcam resource released")
            if self.writer:
                self.writer.release()
                logger.info("Video writer released")
            self.close()

    def get_camera(self):
        logger.debug(f"Fetching camera information for Camera ID {self.camera_id}")
        return Camera.objects.get(id=self.camera_id)

    def get_detection_result(self, results):
        """Extract and return the detection results in a readable format."""
        detection_result = []
        for result in results:
            for detection in result.boxes:
                label = detection.cls[0]
                confidence = detection.conf[0]
                detection_result.append(f"Label: {label}, Confidence: {confidence:.2f}")
        return "\n".join(detection_result)

    def save_frame_to_file(self, frame):
        """Save the frame as an image and return the image path."""
        output_dir = os.path.join(settings.MEDIA_ROOT, 'detected_frames')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.time()
        frame_filename = f"frame_{timestamp}.jpg"
        frame_path = os.path.join(output_dir, frame_filename)

        cv2.imwrite(frame_path, frame)
        return frame_path

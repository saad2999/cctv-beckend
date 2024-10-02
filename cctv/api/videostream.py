import cv2
import threading
import logging
from ultralytics import YOLO
import os
from django.conf import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VideoStream:
    def __init__(self, video_source=0, output_path=None):
        logger.info(f"Initializing VideoStream with source {video_source}")
        self.video = cv2.VideoCapture(video_source)
        
        if not self.video.isOpened():
            logger.error(f"Unable to open video source: {video_source}")
            raise ValueError("Unable to open video source", video_source)
        
        self.running = True
        self.lock = threading.Lock()
        self.frame = None
        self.output_path = output_path
        self.writer = None
        
        # Initialize YOLO model
        logger.info("Loading YOLO model")
        self.model = YOLO('yolov8s.pt')
        
        threading.Thread(target=self.update, args=()).start()
        logger.debug("VideoStream thread started")

    def __del__(self):
        logger.info("Releasing VideoStream resources")
        self.running = False
        if self.writer:
            self.writer.release()
            logger.info("Video writer released")
        self.video.release()
        logger.debug("Video source released")

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                logger.debug("Returning current frame")
                return self.frame
            logger.warning("No frame available")
            return None

    def update(self):
        logger.info("Starting video capture update loop")
        while self.running:
            success, frame = self.video.read()
            if not success:
                logger.error("Failed to read frame from video source")
                self.running = False
                break
            
            logger.debug("Frame read successfully")

            # Perform object detection
            logger.info("Performing object detection")
            results = self.model(frame)
            
            # Draw bounding boxes on the frame
            for r in results:
                annotated_frame = r.plot()
                logger.debug("Object detection complete, frame annotated")
            
            with self.lock:
                self.frame = annotated_frame
                logger.debug("Frame updated in memory")
            
            # Write frame to video file if output path is specified
            if self.output_path:
                if self.writer is None:
                    logger.info(f"Initializing video writer with output path: {self.output_path}")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    self.writer = cv2.VideoWriter(self.output_path, fourcc, 20.0, 
                                                  (self.frame.shape[1], self.frame.shape[0]))
                    logger.debug("Video writer initialized")
                
                self.writer.write(self.frame)
                logger.debug("Frame written to video file")
        
        logger.info("VideoStream update loop ended")
        if self.writer:
            self.writer.release()
            logger.info("Video writer released after loop completion")

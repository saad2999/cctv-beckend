import asyncio
import base64
import json
import cv2
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from channels.routing import URLRouter
from django.urls import re_path
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import logging

from .consumer import VideoStreamConsumer, CameraStreamConsumer
from .models import Camera

User = get_user_model()
logger = logging.getLogger(__name__)

@patch('cv2.VideoCapture')
@patch('cv2.VideoWriter')
@patch('ultralytics.YOLO')
async def test_video_recording(self, mock_yolo, mock_video_writer, mock_video_capture):
    """Test video recording functionality"""
    # Mock video capture
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cap.get.side_effect = lambda x: 640 if x == cv2.CAP_PROP_FRAME_WIDTH else 480
    mock_video_capture.return_value = mock_cap

    # Mock YOLO model
    mock_model = MagicMock()
    mock_model.return_value = [MagicMock(plot=lambda: np.zeros((480, 640, 3), dtype=np.uint8))]
    mock_yolo.return_value = mock_model

    # Mock video writer
    mock_writer = MagicMock()
    mock_video_writer.return_value = mock_writer

    # Connect to WebSocket
    communicator = self.create_communicator()
    connected, _ = await communicator.connect()
    self.assertTrue(connected)

    try:
        # Wait for some frames to be processed
        for _ in range(5):  # Try to receive 5 frames
            try:
                response = await communicator.receive_json_from(timeout=2.0)
                self.assertIn('frame', response)
                logger.info(f"Received frame: {response}")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for frames")
                self.fail("Timeout waiting for frames")

        # Verify video writer was called
        mock_writer.write.assert_called()
        logger.info(f"Video writer write call count: {mock_writer.write.call_count}")

    finally:
        await communicator.disconnect()

        # Wait for a short time to allow for cleanup
        await asyncio.sleep(0.1)

        # Verify cleanup
        self.assertTrue(mock_writer.release.called, "Video writer release method was not called")
        self.assertTrue(mock_cap.release.called, "Video capture release method was not called")

    # Additional assertions
    self.assertGreater(mock_writer.write.call_count, 0, "No frames were written")
    self.assertEqual(mock_cap.release.call_count, 1, "Video capture release should be called once")
    self.assertEqual(mock_writer.release.call_count, 1, "Video writer release should be called once")
"""
Face Detection Service
Uses MediaPipe Face Landmarker to detect faces and extract skin regions
"""

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from typing import Optional, List
import os


class FaceDetectionService:
    """Service for detecting faces and extracting skin regions"""
    
    def __init__(self):
        """Initialize MediaPipe Face Landmarker"""
        try:
            # Download model if needed
            model_path = self._get_model_path()
            
            # Create FaceLandmarker options
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            self.detector = vision.FaceLandmarker.create_from_options(options)
            self.is_available = True
        except Exception as e:
            print(f"\n⚠️  WARNING: MediaPipe not available: {e}")
            print("ℹ️  MediaPipe requires Python 3.12 or earlier")
            print("ℹ️  Face detection will not work, but the server will run")
            print("ℹ️  To fix: Use Python 3.12 or wait for MediaPipe update\n")
            self.detector = None
            self.is_available = False
        
        # Define landmark indices for skin regions
        # These are based on MediaPipe Face Mesh topology
        self.skin_regions = {
            'forehead': list(range(10, 67)),
            'left_cheek': [123, 116, 117, 118, 119, 120, 121, 128, 234, 227, 137, 177, 215],
            'right_cheek': [352, 345, 346, 347, 348, 349, 350, 357, 454, 447, 366, 401, 435],
            'nose_bridge': [6, 168, 197, 195, 5],
            'chin': [152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162],
        }
    
    def _get_model_path(self) -> str:
        """Get or download the face landmarker model"""
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, 'face_landmarker.task')
        
        if not os.path.exists(model_path):
            import urllib.request
            print("📥 Downloading MediaPipe face landmarker model...")
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            urllib.request.urlretrieve(url, model_path)
            print("✅ Model downloaded successfully!")
        
        return model_path
    
    def detect_face(self, image: np.ndarray) -> Optional[any]:
        """
        Detect face in image using MediaPipe Face Landmarker
        
        Args:
            image: BGR image from OpenCV
            
        Returns:
            Face landmarks or None if no face detected
        """
        if not self.is_available:
            raise RuntimeError("MediaPipe is not available. Please use Python 3.12 or earlier.")
        
        # Convert BGR to RGB for MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        
        # Detect face landmarks
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.face_landmarks:
            return None
        
        # Return first face detected
        return detection_result.face_landmarks[0]
    
    def extract_skin_regions(self, image: np.ndarray, face_landmarks: List) -> np.ndarray:
        """Sample small cheek patches, avoiding broad landmark polygons.

        Earlier code filled convex polygons using unordered landmark indices.
        That could include background, hair, eyes and lips. Two conservative
        cheek regions are a better starting point, but photos remain uncalibrated.
        """
        h, w = image.shape[:2]
        if not face_landmarks:
            return np.empty((0, 3), dtype=np.uint8)
        landmarks = face_landmarks
        if len(landmarks) <= 425:
            return np.empty((0, 3), dtype=np.uint8)
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        face_width = max(1, np.hypot((left_eye.x - right_eye.x) * w,
                                      (left_eye.y - right_eye.y) * h))
        radius = max(3, int(face_width * 0.11))
        samples = []
        for idx in (205, 425):
            p = landmarks[idx]
            x, y = int(p.x * w), int(p.y * h)
            x0, x1 = max(0, x - radius), min(w, x + radius + 1)
            y0, y1 = max(0, y - radius), min(h, y + radius + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            patch = image[y0:y1, x0:x1].reshape(-1, 3)
            if len(patch):
                samples.append(patch)
        return np.concatenate(samples) if samples else np.empty((0, 3), dtype=np.uint8)

    def get_bounding_box(self, image: np.ndarray, face_landmarks: any) -> tuple:
        """
        Get bounding box coordinates for detected face
        
        Args:
            image: BGR image from OpenCV
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            Tuple of (x_min, y_min, x_max, y_max)
        """
        height, width = image.shape[:2]
        
        x_coords = [landmark.x * width for landmark in face_landmarks.landmark]
        y_coords = [landmark.y * height for landmark in face_landmarks.landmark]
        
        x_min = int(min(x_coords))
        x_max = int(max(x_coords))
        y_min = int(min(y_coords))
        y_max = int(max(y_coords))
        
        return (x_min, y_min, x_max, y_max)
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()

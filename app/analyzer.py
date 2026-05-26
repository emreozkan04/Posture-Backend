import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math

class PostureAnalyzer:
    def __init__(self, model_path: str = 'pose_landmarker_full.task'):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def evaluate_posture(self, landmarks):
        warnings = []
        
        # We only need the nose and the shoulders for a desk-bound posture check
        nose = landmarks[0]
        l_sh = landmarks[11]
        r_sh = landmarks[12]

        # Ensure the upper body is actually visible before running heuristics
        if nose.visibility < 0.5 or l_sh.visibility < 0.5 or r_sh.visibility < 0.5:
            return ["Low Visibility - Please sit in frame"]

        # 1. Calculate the reference scale (Shoulder Width)
        shoulder_width = math.hypot(
            l_sh.x - r_sh.x, 
            l_sh.y - r_sh.y
        )
        
        # Prevent division by zero
        if shoulder_width < 1e-5:
            return warnings

        # 2. Check for Uneven Shoulders
        y_diff = abs(l_sh.y - r_sh.y)
        tilt_ratio = y_diff / shoulder_width
        
        if tilt_ratio > 0.08:  # 8% tilt threshold
            warnings.append("Uneven Shoulders")

        # 3. Check for Slouching (Forward Head Posture)
        shoulder_midpoint_y = (l_sh.y + r_sh.y) / 2.0
        neck_height = shoulder_midpoint_y - nose.y
        posture_ratio = neck_height / shoulder_width
        
        if posture_ratio < 0.7:  # 70% height-to-width threshold
            warnings.append("Slouching Detected")

        return warnings

    def process_frame(self, bgr_image, timestamp_ms: int):
        image_rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if results.pose_landmarks:
            return self.evaluate_posture(results.pose_landmarks[0])
        return []
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

class PostureAnalyzer:
    def __init__(self, model_path: str = 'pose_landmarker_lite.task'):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    @staticmethod
    def calculate_angle(a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)

        if angle > 180.0:
            angle = 360 - angle
        return angle

    def evaluate_posture(self, landmarks):
        warnings = []
        
        l_ear, r_ear = landmarks[7], landmarks[8]
        l_sh, r_sh = landmarks[11], landmarks[12]
        l_hip, r_hip = landmarks[23], landmarks[24]

        avg_shoulder_z = (l_sh.z + r_sh.z) / 2
        avg_hip_z = (l_hip.z + r_hip.z) / 2
        if (avg_shoulder_z - avg_hip_z) < -0.25:
            warnings.append("Slouching Detected (Depth)")
        
        shoulder_width = abs(l_sh.x - r_sh.x)
        avg_torso_length = (abs(l_sh.y - l_hip.y) + abs(r_sh.y - r_hip.y)) / 2
        compression_ratio = avg_torso_length / shoulder_width if shoulder_width > 0 else 100 
        
        if compression_ratio < 1.0:
            warnings.append("Slouching Detected (Compression)")

        if abs(l_sh.y - r_sh.y) > 0.04: 
            warnings.append("Uneven Shoulders")

        left_neck_angle = self.calculate_angle([l_ear.x, l_ear.y], [l_sh.x, l_sh.y], [l_hip.x, l_hip.y])
        right_neck_angle = self.calculate_angle([r_ear.x, r_ear.y], [r_sh.x, r_sh.y], [r_hip.x, r_hip.y])
        
        if ((left_neck_angle + right_neck_angle) / 2) < 150:
            warnings.append("Forward Head Posture")

        return warnings

    def process_frame(self, bgr_image, timestamp_ms: int):
        image_rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if results.pose_landmarks:
            return self.evaluate_posture(results.pose_landmarks[0])
        return []
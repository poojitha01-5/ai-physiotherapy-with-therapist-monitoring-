import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler, LabelEncoder
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import tensorflow as tf
import threading
import base64
import os
import numpy as np
import asyncio
import json
from collections import deque
import time
import websockets
import base64
import time
from typing import Dict, List, Optional
import joblib
from tensorflow.keras.models import load_model
import logging
import mediapipe as mp
import numpy as np
import pandas as pd
import asyncio
import threading
import time
import base64
import logging
import websockets
from functools import partial
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SquatState(Enum):
    """States for squat repetition state machine"""
    STANDING = "STANDING"
    DESCENDING = "DESCENDING"
    SQUATTING = "SQUATTING"
    ASCENDING = "ASCENDING"
    COMPLETED = "COMPLETED"


class AngleSmoother:
    """Smooth angle values using exponential moving average"""
    def __init__(self, alpha=0.3, window_size=5):
        self.alpha = alpha  # Smoothing factor (0-1)
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
    
    def smooth(self, value: float) -> float:
        """Apply exponential moving average smoothing"""
        self.history.append(value)
        if len(self.history) < 2:
            return value
        
        # Calculate exponential moving average
        smoothed = self.history[-1]
        for i in range(len(self.history) - 2, -1, -1):
            smoothed = self.alpha * self.history[i] + (1 - self.alpha) * smoothed
        
        return smoothed
    
    def reset(self):
        """Reset smoothing history"""
        self.history.clear()


class LandmarkVisibilityChecker:
    """Check visibility of required landmarks with configurable thresholds"""
    def __init__(self, mp_pose):
        self.mp_pose = mp_pose
        # Per-landmark visibility thresholds
        self.visibility_thresholds = {
            'critical': 0.5,  # Hips, knees, ankles - must be highly visible
            'important': 0.3,  # Shoulders - moderately visible
            'optional': 0.1   # Other landmarks - can be less visible
        }
        
        # Landmark categories
        self.landmark_categories = {
            'critical': [
                mp_pose.PoseLandmark.LEFT_HIP,
                mp_pose.PoseLandmark.RIGHT_HIP,
                mp_pose.PoseLandmark.LEFT_KNEE,
                mp_pose.PoseLandmark.RIGHT_KNEE,
                mp_pose.PoseLandmark.LEFT_ANKLE,
                mp_pose.PoseLandmark.RIGHT_ANKLE
            ],
            'important': [
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.RIGHT_SHOULDER
            ],
            'optional': [
                mp_pose.PoseLandmark.NOSE
            ]
        }
    
    def check_visibility(self, landmarks) -> tuple[bool, str]:
        """
        Check if all required landmarks are visible
        Returns (is_visible, error_message)
        """
        # Check critical landmarks
        for landmark in self.landmark_categories['critical']:
            visibility = landmarks.landmark[landmark].visibility
            if visibility < self.visibility_thresholds['critical']:
                return False, f"Critical landmark {landmark.name} not visible (visibility: {visibility:.2f})"
        
        # Check important landmarks
        for landmark in self.landmark_categories['important']:
            visibility = landmarks.landmark[landmark].visibility
            if visibility < self.visibility_thresholds['important']:
                return False, f"Important landmark {landmark.name} not visible (visibility: {visibility:.2f})"
        
        return True, ""
    
    def get_average_visibility(self, landmarks, category='critical') -> float:
        """Get average visibility for a category of landmarks"""
        landmarks_to_check = self.landmark_categories.get(category, [])
        if not landmarks_to_check:
            return 1.0
        
        visibilities = [
            landmarks.landmark[lm].visibility 
            for lm in landmarks_to_check
        ]
        return sum(visibilities) / len(visibilities)


class SquatAnalyzer:
#    def __init__(self, model_path = r"E:\IMPORTED FROM C\Desktop\Website_PhysioVision\PhysioVision\Backend_Vision\models_vision\best_squat_model.keras", scaler_path = r"E:\IMPORTED FROM C\Desktop\Website_PhysioVision\PhysioVision\Backend_Vision\models_vision\preprocessed_data_label_encoder.joblib", label_encoder_path = r"E:\IMPORTED FROM C\Desktop\Website_PhysioVision\PhysioVision\Backend_Vision\models_vision\preprocessed_data_scaler.joblib" , window_size=30):
    def __init__(self, model_path = r"models_vision/best_squat_model.keras", scaler_path = r"models_vision/preprocessed_data_scaler.joblib", label_encoder_path = r"models_vision/preprocessed_data_label_encoder.joblib" , window_size=30):

        """Initialize the squat analyzer with trained model and preprocessing tools"""
        # Load model and preprocessing tools
        self.clients = set()
        self.running = False
        self.event_loop = None
        self.server = None
        self.capture = None
        self.detector_thread = None

        self.model = tf.keras.models.load_model(model_path)
        self.scaler = joblib.load(scaler_path)
        self.label_encoder = joblib.load(label_encoder_path)
        self.window_size = window_size
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize new components
        self.visibility_checker = LandmarkVisibilityChecker(self.mp_pose)
        self.knee_angle_smoother = AngleSmoother(alpha=0.3, window_size=5)
        self.hip_angle_smoother = AngleSmoother(alpha=0.3, window_size=5)
        
        # Create buffer for storing features
        self.features_buffer = deque(maxlen=window_size)
        
        # Store current prediction and confidence
        self.current_prediction = None
        self.prediction_confidence = 0.0
        self.last_predictions = deque(maxlen=5)  # Store last 5 predictions for smoothing
        
        
        # Feature names for the processed angles
        self.feature_names = [
            'left_knee_angle', 'right_knee_angle', 
            'left_hip_angle', 'right_hip_angle',
            'torso_vertical_angle', 'head_torso_angle',
            'knee_distance_normalized', 'ankle_distance_normalized',
            'left_squat_depth', 'right_squat_depth',
            'left_knee_angle_velocity', 'right_knee_angle_velocity',
            'left_hip_angle_velocity', 'right_hip_angle_velocity',
            'torso_vertical_angle_velocity', 'head_torso_angle_velocity',
            'knee_distance_normalized_velocity', 'ankle_distance_normalized_velocity',
            'left_squat_depth_velocity', 'right_squat_depth_velocity'
        ]
        
        # Keypoint mapping from MediaPipe to our preprocessing format
        self.keypoint_map = {
            'NOSE': self.mp_pose.PoseLandmark.NOSE,
            'LEFT_SHOULDER': self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            'RIGHT_SHOULDER': self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            'LEFT_HIP': self.mp_pose.PoseLandmark.LEFT_HIP,
            'RIGHT_HIP': self.mp_pose.PoseLandmark.RIGHT_HIP,
            'LEFT_KNEE': self.mp_pose.PoseLandmark.LEFT_KNEE,
            'RIGHT_KNEE': self.mp_pose.PoseLandmark.RIGHT_KNEE,
            'LEFT_ANKLE': self.mp_pose.PoseLandmark.LEFT_ANKLE,
            'RIGHT_ANKLE': self.mp_pose.PoseLandmark.RIGHT_ANKLE
        }
        
        # Error explanations
        self.error_explanations = {
            'bad_back_round': "Your back is rounding.",
            'bad_back_warp': "Your back is excessively arched",
            'bad_head': "HKeep your neck aligned with your spine.",
            'bad_inner_thigh': "Keep knees aligned with toes.",
            'bad_shallow': "Squat is too shallow.",
            'bad_toe': "Keep feet shoulder-width apart.",
            'good': "Good form! Keep it up."
        }



        # Add rep counting variables with improved state machine
        self.rep_count = 0
        self.state = SquatState.STANDING  # Initial state using enum
        self.depth_history = deque(maxlen=10)  # Store recent squat depths for dynamic thresholding
        self.min_depth = None  # Dynamic minimum depth (updated during exercise)
        self.max_depth = None  # Dynamic maximum depth (updated during exercise)
        self.depth_threshold_factor = 0.5  # Percentage of depth range to consider a state change
        
        # State machine timing
        self.state_duration = 0  # Frames spent in current state
        self.min_state_duration = 3  # Minimum frames before state transition (debouncing)
        
        # Hold detection at bottom position (0.3-0.5 seconds)
        self.hold_duration = 0  # Frames spent in SQUATTING
        self.min_hold_frames = int(0.4 * 30)  # 0.4 seconds minimum hold (assuming 30fps)
        
        # Cooldown after successful rep (prevent double-counting)
        self.cooldown_frames = 0
        self.cooldown_duration = int(0.5 * 30)  # 0.5 seconds cooldown
        
        # Low-confidence frame filtering
        self.min_landmark_confidence = 0.3
        
        # Debug logging
        self.debug_mode = True
        
        # Current angles for display
        self.current_knee_angle = 180
        self.current_hip_angle = 180
        
        # Form quality scoring
        self.form_score = 100
        self.depth_score = 100
        self.alignment_score = 100
        self.posture_score = 100
        self.stability_score = 100

        # Add error occurrence tracking
        self.error_counts = {
            'bad_back_round': 0,
            'bad_back_warp': 0,
            'bad_head': 0,
            'bad_inner_thigh': 0,
            'bad_shallow': 0,
            'bad_toe': 0,
            'good': 0  # Track good form too
        }



        
        
        print("Squat Analyzer initialized successfully")

    def _landmarks_to_keypoints_dict(self, landmarks):
        """Convert MediaPipe landmarks to format compatible with preprocessing code"""
        keypoints = {}
        for name, landmark_id in self.keypoint_map.items():
            landmark = landmarks.landmark[landmark_id]
            keypoints[f'{name}_x'] = landmark.x
            keypoints[f'{name}_y'] = landmark.y
            keypoints[f'{name}_z'] = landmark.z
        return keypoints

    def _keypoints_dict_to_df(self, keypoints_dict):
        """Convert keypoints dictionary to DataFrame"""
        return pd.DataFrame([keypoints_dict])

    def _calculate_vector(self, df, point1, point2):
        """Calculate vector between two keypoints"""
        vec = np.zeros((len(df), 3))
        vec[:, 0] = df[f'{point2}_x'].values - df[f'{point1}_x'].values
        vec[:, 1] = df[f'{point2}_y'].values - df[f'{point1}_y'].values
        vec[:, 2] = df[f'{point2}_z'].values - df[f'{point1}_z'].values
        return vec

    def _normalize_vector(self, vec):
        """Normalize a vector to unit length"""
        magnitude = np.sqrt(np.sum(vec**2, axis=1))
        magnitude = np.where(magnitude == 0, 1e-10, magnitude)
        vec_normalized = vec / magnitude[:, np.newaxis]
        return vec_normalized

    def _angle_between_vectors(self, vec1, vec2):
        """Calculate the angle between two 3D vectors in degrees"""
        vec1_norm = self._normalize_vector(vec1)
        vec2_norm = self._normalize_vector(vec2)
        dot_product = np.sum(vec1_norm * vec2_norm, axis=1)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angles = np.degrees(np.arccos(dot_product))
        return angles

    def _extract_anatomical_angles(self, df):
        """Extract biomechanically relevant angles from keypoints"""
        angles_df = pd.DataFrame()
        
        # Calculate vectors
        shoulder_to_hip_left = self._calculate_vector(df, 'LEFT_SHOULDER', 'LEFT_HIP')
        shoulder_to_hip_right = self._calculate_vector(df, 'RIGHT_SHOULDER', 'RIGHT_HIP')
        hip_to_knee_left = self._calculate_vector(df, 'LEFT_HIP', 'LEFT_KNEE')
        hip_to_knee_right = self._calculate_vector(df, 'RIGHT_HIP', 'RIGHT_KNEE')
        knee_to_ankle_left = self._calculate_vector(df, 'LEFT_KNEE', 'LEFT_ANKLE')
        knee_to_ankle_right = self._calculate_vector(df, 'RIGHT_KNEE', 'RIGHT_ANKLE')
        nose_to_shoulder_mid = self._calculate_vector(df, 'NOSE', 'LEFT_SHOULDER')
        
        # Calculate angles
        angles_df['left_knee_angle'] = self._angle_between_vectors(hip_to_knee_left, knee_to_ankle_left)
        angles_df['right_knee_angle'] = self._angle_between_vectors(hip_to_knee_right, knee_to_ankle_right)
        angles_df['left_hip_angle'] = self._angle_between_vectors(shoulder_to_hip_left, hip_to_knee_left)
        angles_df['right_hip_angle'] = self._angle_between_vectors(shoulder_to_hip_right, hip_to_knee_right)
        
        # Back angles (relative to vertical)
        vertical = np.zeros_like(shoulder_to_hip_left)
        vertical[:, 1] = 1  # Y axis is usually vertical in pose estimation
        angles_df['torso_vertical_angle'] = self._angle_between_vectors(shoulder_to_hip_left, vertical)
        
        # Head angle relative to torso
        angles_df['head_torso_angle'] = self._angle_between_vectors(nose_to_shoulder_mid, shoulder_to_hip_left)
        
        # Knee distance (for detecting knee valgus/varus)
        hip_width = np.sqrt(
            (df['RIGHT_HIP_x'] - df['LEFT_HIP_x'])**2 + 
            (df['RIGHT_HIP_z'] - df['LEFT_HIP_z'])**2
        )
        knee_distance = np.sqrt(
            (df['RIGHT_KNEE_x'] - df['LEFT_KNEE_x'])**2 + 
            (df['RIGHT_KNEE_z'] - df['LEFT_KNEE_z'])**2
        )
        angles_df['knee_distance_normalized'] = knee_distance / hip_width
        
        # Foot positioning
        ankle_distance = np.sqrt(
            (df['RIGHT_ANKLE_x'] - df['LEFT_ANKLE_x'])**2 + 
            (df['RIGHT_ANKLE_z'] - df['LEFT_ANKLE_z'])**2
        )
        angles_df['ankle_distance_normalized'] = ankle_distance / hip_width
        
        # Squat depth - hip height relative to knee height
        angles_df['left_squat_depth'] = df['LEFT_HIP_y'] - df['LEFT_KNEE_y']
        angles_df['right_squat_depth'] = df['RIGHT_HIP_y'] - df['RIGHT_KNEE_y']
        
        return angles_df

    def _add_velocity_features(self, current_features, prev_features=None, fps=30):
        """Add velocity features based on frame-to-frame changes"""
        # Create a Series with zeros for all velocity features
        velocity_features = pd.Series({f'{col}_velocity': 0.0 for col in current_features.index 
                                    if not col.endswith('_velocity')})
        
        if prev_features is not None:
            # Calculate frame-to-frame changes for non-velocity features
            for col in current_features.index:
                if not col.endswith('_velocity') and col in prev_features:
                    velocity_col = f'{col}_velocity'
                    velocity_features[velocity_col] = (current_features[col] - prev_features[col]) * fps
        
        # Combine current features with velocity features
        # Make sure to only include the original features and their velocities
        result = pd.Series()
        for feature_name in self.feature_names:
            if feature_name in current_features:
                result[feature_name] = current_features[feature_name]
            elif feature_name in velocity_features:
                result[feature_name] = velocity_features[feature_name]
            else:
                # If a feature is missing, set it to 0 to maintain the expected shape
                result[feature_name] = 0.0
                
        return result
    def _process_frame(self, frame):
        """Process a single frame and extract features"""
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image
        results = self.pose.process(image_rgb)
        
        # If no pose detected, return None
        if not results.pose_landmarks:
            return None, frame
        
        # Use improved visibility checker
        is_visible, visibility_error = self.visibility_checker.check_visibility(results.pose_landmarks)
        if not is_visible:
            cv2.putText(frame, visibility_error, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return None, frame, False, 0.0
        
        # Calculate average landmark confidence
        landmark_confidences = [
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP].visibility,
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP].visibility,
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_KNEE].visibility,
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_KNEE].visibility,
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ANKLE].visibility,
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_ANKLE].visibility
        ]
        avg_confidence = sum(landmark_confidences) / len(landmark_confidences)
        
        # Draw pose landmarks on the image
        annotated_image = frame.copy()
        self.mp_drawing.draw_landmarks(
            annotated_image,
            results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        # Convert landmarks to keypoints dictionary
        keypoints_dict = self._landmarks_to_keypoints_dict(results.pose_landmarks)
        
        # Convert to DataFrame
        keypoints_df = self._keypoints_dict_to_df(keypoints_dict)
        
        # Extract angles
        angles_df = self._extract_anatomical_angles(keypoints_df)
        
        # Get the first row as a Series
        feature_series = angles_df.iloc[0]
        
        # Add velocity features if we have previous features
        if len(self.features_buffer) > 0:
            prev_features = self.features_buffer[-1]
            feature_series = self._add_velocity_features(feature_series, prev_features)
        else:
            # No previous features, add zero velocities
            feature_series = self._add_velocity_features(feature_series)
        
        # Add to buffer
        self.features_buffer.append(feature_series)
        
        return feature_series, annotated_image, is_visible, avg_confidence

    def _make_prediction(self):
        """Make a prediction using the current feature buffer"""
        if len(self.features_buffer) < self.window_size:
            return None, 0.0
        
        try:
            # Extract features in correct order
            features_list = []
            for feature in self.features_buffer:
                # Create a row with all required features in the correct order
                feature_row = []
                for feat_name in self.feature_names:
                    if feat_name in feature:
                        feature_row.append(feature[feat_name])
                    else:
                        # If feature is missing, use 0 as a placeholder
                        print(f"Warning: Missing feature {feat_name}")
                        feature_row.append(0.0)
                features_list.append(feature_row)
            
            # Convert to numpy array
            features_array = np.array(features_list)
            
            # Print shape for debugging
            print(f"Features array shape before normalization: {features_array.shape}")
            
            # Apply scaler
            normalized_features = self.scaler.transform(features_array)
            
            # Print shape after normalization
            print(f"Normalized features shape: {normalized_features.shape}")
            
            # Reshape for model input - try using the exact shape the model expects
            # Instead of hard-coding to [1, window_size, num_features], let's try different approaches
            
            # Approach 1: Batch of sequences (typical for LSTM/RNN models)
            model_input = normalized_features.reshape(1, self.window_size, len(self.feature_names))
            print(f"Model input shape (approach 1): {model_input.shape}")
            
            # Get prediction with explicit batch size
            prediction_probs = self.model.predict(model_input, batch_size=1, verbose=1)[0]
            predicted_class_idx = np.argmax(prediction_probs)
            confidence = prediction_probs[predicted_class_idx]
            
            # Get class name
            predicted_class = self.label_encoder.classes_[predicted_class_idx]
            
            return predicted_class, confidence
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0
    def _smooth_predictions(self, new_prediction, new_confidence):
        """Smooth predictions to avoid flickering"""
        if new_prediction is None:
            return self.current_prediction, self.prediction_confidence
        
        # Add to recent predictions
        self.last_predictions.append((new_prediction, new_confidence))
        
        # Count occurrences of each prediction
        prediction_counts = {}
        total_confidence = {}
        
        for pred, conf in self.last_predictions:
            if pred not in prediction_counts:
                prediction_counts[pred] = 0
                total_confidence[pred] = 0
            
            prediction_counts[pred] += 1
            total_confidence[pred] += conf
        
        # Get the most common prediction
        if prediction_counts:
            most_common = max(prediction_counts.items(), key=lambda x: x[1])[0]
            avg_confidence = total_confidence[most_common] / prediction_counts[most_common]
            return most_common, avg_confidence
        
        return None, 0.0



    def _update_rep_count(self, current_depth, landmarks_visible=True, landmark_confidence=1.0):
        """Update squat state and count reps based on squat depth using improved state machine with hold detection and cooldown."""
        # Skip if landmarks not visible or confidence too low
        if not landmarks_visible or landmark_confidence < self.min_landmark_confidence:
            logger.debug(f"Skipping frame - visible: {landmarks_visible}, confidence: {landmark_confidence:.2f}")
            return
        
        # Use average of left and right squat depth for consistency
        avg_depth = (current_depth['left_squat_depth'] + current_depth['right_squat_depth']) / 2
        self.depth_history.append(avg_depth)

        # Decrease cooldown if active
        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            if self.cooldown_frames == 0:
                logger.debug("Cooldown ended, ready for next rep")
            return  # Don't process state transitions during cooldown

        # Update min and max depths dynamically
        if len(self.depth_history) == self.depth_history.maxlen:
            current_min = min(self.depth_history)
            current_max = max(self.depth_history)
            
            if self.min_depth is None or current_min < self.min_depth:
                self.min_depth = current_min
            if self.max_depth is None or current_max > self.max_depth:
                self.max_depth = current_max

            # Calculate dynamic threshold
            if self.min_depth is not None and self.max_depth is not None:
                depth_range = self.max_depth - self.min_depth
                
                # Require a minimum range of motion to avoid counting noise as a rep
                if depth_range > 0.10:
                    threshold = self.min_depth + (depth_range * self.depth_threshold_factor)

                    # State machine with debouncing
                    self.state_duration += 1
                    
                    # Debug logging
                    if self.debug_mode and self.state_duration % 10 == 0:
                        logger.debug(f"State: {self.state.value}, Depth: {avg_depth:.3f}, Duration: {self.state_duration}")
                    
                    # State transitions with minimum duration check (debouncing)
                    if self.state == SquatState.STANDING and avg_depth < threshold:
                        if self.state_duration >= self.min_state_duration:
                            self.state = SquatState.DESCENDING
                            self.state_duration = 0
                            self.hold_duration = 0
                            logger.info(f"State transition: STANDING -> DESCENDING")
                    elif self.state == SquatState.DESCENDING and avg_depth < self.min_depth + 0.02:
                        if self.state_duration >= self.min_state_duration:
                            self.state = SquatState.SQUATTING
                            self.state_duration = 0
                            logger.info(f"State transition: DESCENDING -> SQUATTING")
                    elif self.state == SquatState.SQUATTING:
                        self.hold_duration += 1
                        if avg_depth > threshold and self.hold_duration >= self.min_hold_frames:
                            if self.state_duration >= self.min_state_duration:
                                self.state = SquatState.ASCENDING
                                self.state_duration = 0
                                logger.info(f"State transition: SQUATTING -> ASCENDING (held for {self.hold_duration} frames)")
                    elif self.state == SquatState.ASCENDING and avg_depth > self.max_depth - 0.02:
                        if self.state_duration >= self.min_state_duration:
                            self.state = SquatState.STANDING
                            self.state_duration = 0
                            self.rep_count += 1  # Count a rep when returning to standing
                            self.cooldown_frames = self.cooldown_duration
                            logger.info(f"Rep counted. Total reps: {self.rep_count}, hold: {self.hold_duration} frames, cooldown started")
                else:
                    # Reset state duration if range is too small
                    self.state_duration = 0

    def calculate_form_score(self, knee_angle, hip_angle, torso_angle, errors):
        """Calculate form quality score based on depth, alignment, posture, and stability."""
        # Depth score (based on knee angle - ideal is 70-110° for squats)
        if 70 <= knee_angle <= 110:
            self.depth_score = 100
        else:
            depth_diff = min(abs(knee_angle - 70), abs(knee_angle - 110))
            self.depth_score = max(0, 100 - (depth_diff * 2))
        
        # Alignment score (based on hip angle - ideal is 70-110°)
        if 70 <= hip_angle <= 110:
            self.alignment_score = 100
        else:
            alignment_diff = min(abs(hip_angle - 70), abs(hip_angle - 110))
            self.alignment_score = max(0, 100 - (alignment_diff * 2))
        
        # Posture score (based on torso angle - ideal is 0-30° from vertical)
        if 0 <= torso_angle <= 30:
            self.posture_score = 100
        else:
            posture_diff = min(abs(torso_angle - 0), abs(torso_angle - 30))
            self.posture_score = max(0, 100 - (posture_diff * 2))
        
        # Stability score (based on error count - fewer errors = higher score)
        error_penalty = len(errors) * 15
        self.stability_score = max(0, 100 - error_penalty)
        
        # Overall form score (weighted average)
        weights = {'depth': 0.4, 'alignment': 0.25, 'posture': 0.2, 'stability': 0.15}
        self.form_score = (
            self.depth_score * weights['depth'] +
            self.alignment_score * weights['alignment'] +
            self.posture_score * weights['posture'] +
            self.stability_score * weights['stability']
        )
        
        return self.form_score
    
    def get_form_feedback(self):
        """Get form feedback based on current scores."""
        feedback = []
        
        if self.form_score >= 80:
            feedback.append("Good form")
        elif self.depth_score < 70:
            feedback.append("Go deeper into the squat")
        if self.posture_score < 70:
            feedback.append("Keep your back straighter")
        if self.alignment_score < 70:
            feedback.append("Check your knee alignment")
        if self.stability_score < 70:
            feedback.append("Focus on stability")
        
        return feedback if feedback else ["Maintain current form"]

    def _update_error_counts(self, prediction):
        """Update the count of the current prediction/error"""
        if prediction in self.error_counts:
            self.error_counts[prediction] += 1



    
    def draw_feedback(self, image, prediction, confidence):
        h, w, _ = image.shape
        
        # Background for text (make it larger to fit rep counter)
        cv2.rectangle(image, (0, h-140), (w, h), (0, 0, 0), -1)
        
        # Draw form feedback (existing code)
        if prediction is None:
            cv2.putText(image, "Getting ready...", (10, h-100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            # Determine text color based on prediction
            if prediction == 'good':
                text_color = (0, 255, 0)  # Green for good form
            else:
                text_color = (0, 0, 255)  # Red for errors
            
            # Add prediction and confidence
            cv2.putText(image, f"Form: {prediction}", (10, h-100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            cv2.putText(image, f"Confidence: {confidence:.2f}", (10, h-70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            
            # Add explanation for errors
            if prediction in self.error_explanations:
                explanation = self.error_explanations[prediction]
                cv2.putText(image, explanation, (w//4, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)





        # Add rep count display
        cv2.putText(image, f"Reps: {self.rep_count}", (10, h-40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return image

    async def process_video(self, frame):
        """Process a single frame and return data to broadcast."""
        # Process the frame
        if frame is None:
            print("Warning: Received None frame")
            return None

        features, annotated_frame, is_visible, avg_confidence = self._process_frame(frame)

        # If no pose detected
        if features is None:
            frame_base64 = self._encode_frame(frame)
            return {
                "type": "frame",
                "data": frame_base64,
                "prediction": None,
                "confidence": None,
                "rep_count": self.rep_count
            }

        # Make prediction if enough frames collected
        if len(self.features_buffer) >= self.window_size:
            print("line k oooper")
            new_prediction, new_confidence = self._make_prediction()
            print("line k neeche")
            self.current_prediction, self.prediction_confidence = self._smooth_predictions(
                new_prediction, new_confidence)
            if self.current_prediction is not None:
                self._update_error_counts(self.current_prediction)

        # Update rep count with current features and visibility
        self._update_rep_count(features, is_visible, avg_confidence)

        ### TEXT TO SPEECH
        error_text = self.current_prediction

        # Add None check here
        if error_text is None:
            error_text = "Processing..."
        elif error_text == "good":
            error_text = "You are doing well" 
        elif error_text in self.error_explanations:
            error_text = self.error_explanations[error_text]
            # Add safety check for the dictionary value
            if error_text is None:
                error_text = "Unknown error"
        
        # Encode frame as base64 and return data
        # Draw feedback on the frame BEFORE encoding
        if annotated_frame is not None:
            annotated_frame = self.draw_feedback(annotated_frame, self.current_prediction, self.prediction_confidence)
            frame_base64 = self._encode_frame(annotated_frame)

        return None  # If no data to broadcast
    
    def generate_report(self):
        """Generate a report summarizing reps and error occurrences"""
        report = f"Squat Analysis Report - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 50 + "\n"
        report += f"Total Reps Performed: {self.rep_count}\n\n"
        report += "Form Analysis:\n"
        report += "-" * 20 + "\n"
        
        total_frames_with_prediction = sum(self.error_counts.values())
        if total_frames_with_prediction > 0:
            for error, count in self.error_counts.items():
                percentage = (count / total_frames_with_prediction) * 100
                explanation = self.error_explanations.get(error, "No explanation available")
                report += f"{error}: {count} occurrences ({percentage:.1f}%)\n"
                report += f"  - {explanation}\n"
        else:
            report += "No form predictions recorded.\n"
        
        report += "=" * 50
        return report

    def reset_counters(self):
        """Reset rep count and error counts"""
        self.rep_count = 0
        self.state = SquatState.STANDING
        self.depth_history.clear()
        self.min_depth = None
        self.max_depth = None
        self.state_duration = 0
        self.hold_duration = 0
        self.cooldown_frames = 0
        self.form_score = 100
        self.depth_score = 100
        self.alignment_score = 100
        self.posture_score = 100
        self.stability_score = 100
        for error in self.error_counts:
            self.error_counts[error] = 0
        # Reset angle smoothers
        self.knee_angle_smoother.reset()
        self.hip_angle_smoother.reset()
        print("Counters reset")

    def rescale_frame(self, frame, scale_percent=50):
        """
        Rescale the input frame to improve processing speed.
        
        Args:
            frame: Input frame to be rescaled
            scale_percent: Percentage of original size (default: 50%)
            
        Returns:
            Rescaled frame
        """
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        
        # Resize image
        resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        return resized

    def _encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')        
    
    async def process_video(self, frame):
        """Process a single frame and return data to broadcast."""
        # Process the frame
        
        features, annotated_frame = self._process_frame(frame)

        # If no pose detected
        if features is None:
            frame_base64 = self._encode_frame(frame)
            return {
                "type": "frame",
                "data": frame_base64,
                "prediction": None,
                "confidence": None,
                "rep_count": self.rep_count
            }

        # Make prediction if enough frames collected
        if len(self.features_buffer) >= self.window_size:
            print("line k oooper")
            new_prediction, new_confidence = self._make_prediction()
            print("line k neeche")
            self.current_prediction, self.prediction_confidence = self._smooth_predictions(
                new_prediction, new_confidence)
            if self.current_prediction is not None:
                self._update_error_counts(self.current_prediction)

        # Update rep count with current features
        self._update_rep_count(features)

        ### TEXT TO SPEECH
        error_text = self.current_prediction
        if error_text == "good":
            error_text = "You are doing well"
        elif error_text in self.error_explanations:
            error_text = self.error_explanations[error_text]

        
        # Encode frame as base64 and return data
        if annotated_frame is not None:
            frame_base64 = self._encode_frame(annotated_frame)
            return {
                "type": "frame",
                "data": frame_base64,
                "prediction": error_text,
                "confidence": self.prediction_confidence,
                "rep_count": self.rep_count,
                "error_text": error_text,
                "form_score": self.form_score,
                "state": str(self.state),
                "knee_angle": self.current_knee_angle,
                "hip_angle": self.current_hip_angle
            }

        return None  # If no data to broadcast

                
        
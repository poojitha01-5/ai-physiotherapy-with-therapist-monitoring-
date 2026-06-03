Summarize all code changes already made for tasks 1–9.

Show:
- Files modified
- Functions added
- Calibration implementation
- Form score implementation
- Rep counting improvements

Do not make further code changes.import cv2
import mediapipe as mp
import numpy as np
from collections import defaultdict, deque
from enum import Enum
import logging
import base64
# import asyncio

logger = logging.getLogger(__name__)


class LungeState(Enum):
    """States for lunge repetition state machine"""
    STANDING = "STANDING"
    DESCENDING = "DESCENDING"
    LUNGE_POSITION = "LUNGE_POSITION"
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
            'optional': []
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
class LungesAnalyzer:
    def __init__(self, exercise="Lunges", delay_seconds=3, target_reps=8, fps=30):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize new components
        self.visibility_checker = LandmarkVisibilityChecker(self.mp_pose)
        self.knee_angle_smoother = AngleSmoother(alpha=0.3, window_size=5)
        self.hip_angle_smoother = AngleSmoother(alpha=0.3, window_size=5)

        self.error_counters = {
            "Perform a full lunge.": 0,
            "Bend front knee more": 0,
            "Front knee bent too much": 0,
            "Front knee past toes": 0,
            "Bend back knee more": 0,
            "Back knee bent too much": 0,
        }
        self.error_threshold = 5  # e.g., must persist for 5 frames

        
        # Initialize model components
        self.scaler = None
        self.pca = None
        self.model = None
        self.is_trained = False

         # Rep counting variables with improved state machine
        self.reps = 0
        self.state = LungeState.STANDING  # Initial state using enum
        self.lunge_depth_threshold = 0.05  # Threshold for detecting rep
        self.prev_knee_angle = None
        self.start_frame = 0
        
        # Depth tracking
        self.max_knee_bend = 180
        self.shallow_rep_detected = False
        
        # State machine timing
        self.state_duration = 0  # Frames spent in current state
        self.min_state_duration = 3  # Minimum frames before state transition (debouncing)
        
        # Hold detection at bottom position (0.3-0.5 seconds)
        self.hold_duration = 0  # Frames spent in LUNGE_POSITION
        self.min_hold_frames = int(0.4 * fps)  # 0.4 seconds minimum hold
        
        # Cooldown after successful rep (prevent double-counting)
        self.cooldown_frames = 0
        self.cooldown_duration = int(0.5 * fps)  # 0.5 seconds cooldown
        
        # Low-confidence frame filtering
        self.min_landmark_confidence = 0.3
        
        # Debug logging
        self.debug_mode = True
        
        # Current angles for display
        self.current_front_knee_angle = 180
        self.current_back_knee_angle = 180
        
        # Form quality scoring
        self.form_score = 100
        self.depth_score = 100
        self.alignment_score = 100
        self.posture_score = 100
        self.stability_score = 100
        
        # Define the landmarks we're interested in (hip, knee, ankle only)
        self.target_landmarks = [
            'LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE',
            'RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE'
        ]

        # Set exercise type
        self.exercise = exercise

        # Thresholds for lunges
        self.LUNGE_THRESHOLDS = {
            "knee_angle": (75, 110),  # Front knee should be around 90 degrees
            "back_knee_angle": (75, 120),  # Back knee angle
            "torso_uprightness": (70, 110),  # Torso should be upright
            "stance_width": (0.2, 0.6),  # Distance between feet (normalized)
            "hip_level": (0, 0.15),  # Hip should be level (relative displacement)
        }

        # Recording and rep counting settings
        self.fps = fps
        self.delay_frames = delay_seconds * fps  # delay before correction
        self.target_reps = target_reps  # Number of reps to detect
        self.frame_count = 0
        self.recording = False  # Now indicates correction active
        self.report = {
            "good_form_frames": 0,
            "error_counts": defaultdict(int)
        }
        self.standing_error_counter = 0
        self.standing_error_threshold = int(5 * self.fps)
           
        
    def extract_keypoints(self, frame):
        """Extract hip, knee, and ankle keypoints from a single frame."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.pose.process(frame_rgb)
        
        if not results.pose_landmarks:
            return None, None
        
        # Extract only hip, knee, ankle keypoints
        keypoints = []
        landmark_dict = {}
        
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            name = self.mp_pose.PoseLandmark(i).name
            if name in self.target_landmarks:
                landmark_dict[name] = [landmark.x, landmark.y, landmark.z]
        
        # Determine leading leg
        knee_r = landmark_dict['RIGHT_KNEE'][:2]  # Just x,y for position comparison
        knee_l = landmark_dict['LEFT_KNEE'][:2]
        
        # Lower y-value means higher in the image (closer to top of frame)
        if knee_r[1] < knee_l[1]:  # Right knee is higher in the frame
            leading_leg = "Right"  # Right leg is forward
        else:
            leading_leg = "Left"  # Left leg is forward
            
        # Extract features in a consistent order
        for name in self.target_landmarks:
            keypoints.extend(landmark_dict[name])
            
        return np.array(keypoints), leading_leg
    
    def normalize_side(self, keypoints, leading_leg):
        """
        Normalize left/right sides to treat them as the same movement pattern.
        This maps all lunges to a standardized form regardless of which leg is forward.
        """
        # Reshape keypoints to have landmarks as rows with [x,y,z] columns
        # We have 6 landmarks (L/R hip, knee, ankle) with 3 coordinates each
        landmarks = keypoints.reshape(6, 3)
        
        # Standardize to always have the same leg configuration
        # If right leg is forward but we want left leg to be our standard (or vice versa)
        if leading_leg == "Right":
            # Swap left and right sides
            temp = np.copy(landmarks[0:3])
            landmarks[0:3] = landmarks[3:6]
            landmarks[3:6] = temp
        
        # Return flattened normalized keypoints
        return landmarks.flatten()
    
    def calculate_lunge_features(self, keypoints, original_leading_leg):
        """Calculate important angles and distances for lunge form assessment."""
        # Reshape keypoints to have landmarks as rows with [x,y,z] columns
        landmarks = keypoints.reshape(6, 3)
        
        # Extract individual landmarks
        front_hip = landmarks[0]    # Using left as front leg (after normalization)
        front_knee = landmarks[1]
        front_ankle = landmarks[2]
        
        # Calculate angle between three points
        def calculate_angle(a, b, c):
            a = np.array(a)
            b = np.array(b)
            c = np.array(c)
            
            ba = a - b
            bc = c - b
            
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            # Clip to avoid numerical errors
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            angle = np.arccos(cosine_angle)
            return np.degrees(angle)
        
        # Calculate relevant angles and distances
        features = {}
        
        # Front leg angles
        features['front_knee_angle'] = calculate_angle(front_hip, front_knee, front_ankle)
        
        # Store the original leading leg for reference
        features['leading_leg'] = original_leading_leg
        
        return features
    
    def load_model(self, model_path):
        try:
            print("Attempting to load model...")
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.scaler = model_data['scaler']
                self.pca = model_data['pca']
                self.model = model_data['model']
                self.feature_means = model_data['feature_means']
                self.feature_stds = model_data['feature_stds']
            self.is_trained = True
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")

    def reset_counters(self):
        """Reset counters and data storage."""
        self.frame_count = 0
        self.frames_keypoints = []
        self.features_data = []


    def _encode_frame(self, frame):
        """Encode frame as base64."""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

  
    
    def detect_form(self, frame):
        """Detect lunge form in a single frame."""
        if not self.is_trained:
            raise ValueError("Model not trained. Please train or load a model first.")
        
        keypoints, leading_leg = self.extract_keypoints(frame)
        if keypoints is None:
            return False, "No person detected", None, None
        
        # Normalize based on which leg is leading
        normalized_keypoints = self.normalize_side(keypoints, leading_leg)
        
        # Calculate features for specific feedback
        features = self.calculate_lunge_features(normalized_keypoints, leading_leg)
        
        # Prepare keypoints for prediction
        keypoints_scaled = self.scaler.transform(normalized_keypoints.reshape(1, -1))
        keypoints_pca = self.pca.transform(keypoints_scaled)
        
        # Make prediction
        prediction = self.model.predict(keypoints_pca)[0]
        score = self.model.score_samples(keypoints_pca)[0]
        
        # Check if form is correct
        is_correct = prediction == 1
        
        # Prepare feedback
        feedback = ""
        errors = {}
        
        if not is_correct:
            for feature_name, feature_value in features.items():
                if feature_name == 'leading_leg':
                    continue
                    
                if "front_knee_angle" in feature_name:
                    if feature_value < 70:
                        message = f"{leading_leg} leg: Bend your knee more."
                        errors[feature_name] = {"message": message, "value": feature_value, "ideal": 90}
                        feedback += message + " "
                    elif feature_value > 110:
                        message = f"{leading_leg} leg: Don't bend your knee too much."
                        errors[feature_name] = {"message": message, "value": feature_value, "ideal": 90}
                        feedback += message + " "

            if not feedback:
                feedback = "Form needs improvement. Check your overall posture."
        else:
            feedback = "Good form!"
        
        return is_correct, feedback, features, errors
    

    def calculate_angle(self, p1, p2, p3):
        """Calculate the angle between three points in degrees."""
        a = np.array(p1)
        b = np.array(p2)
        c = np.array(p3)
        
        ba = a - b
        bc = c - b
        
        # Handle zero vectors
        if np.linalg.norm(ba) < 1e-6 or np.linalg.norm(bc) < 1e-6:
            return 0
            
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)  # Avoid numerical errors
        angle = np.arccos(cosine_angle) * 180 / np.pi
        return angle

    def check_landmark_visibility(self, landmarks, landmark_indexes):
        """Check if landmarks are visible."""
        for idx in landmark_indexes:
            if landmarks[idx].visibility < self.visibility_threshold:
                return False
        return True

    def check_lunges_form(self, landmarks):
        """Analyze lunges exercise and return errors."""
        errors = []

        # Use improved visibility checker
        is_visible, visibility_error = self.visibility_checker.check_visibility(landmarks)
        if not is_visible:
            return [visibility_error], 180

        # Extract key landmarks
        l_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y]
        r_hip = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y]
        l_knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].y]
        r_knee = [landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].y]
        l_ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE].y]
        r_ankle = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y]
        l_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y]
        r_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
        
        # Calculate leg angles
        left_knee_angle = self.calculate_angle(l_hip, l_knee, l_ankle)
        right_knee_angle = self.calculate_angle(r_hip, r_knee, r_ankle)

        # Fix for NaN angles
        if np.isnan(left_knee_angle):
            left_knee_angle = 180
        if np.isnan(right_knee_angle):
            right_knee_angle = 180
            
        # Determine which leg is front (has smaller angle = more bent)
        if left_knee_angle < right_knee_angle:
            front_knee_angle = left_knee_angle
            back_knee_angle = right_knee_angle
            front_is_left = True
        else:
            front_knee_angle = right_knee_angle
            back_knee_angle = left_knee_angle
            front_is_left = False
            
        # Calculate torso angle (relative to vertical)
        mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        # Angle with vertical (0 is perfectly upright)
        torso_angle = self.calculate_angle([mid_hip[0], mid_hip[1] + 1], mid_hip, mid_shoulder)
        
        # Calculate stance width
        stance_width = np.linalg.norm(np.array(l_ankle) - np.array(r_ankle))
        
        # Calculate hip level (should be level in a good lunge)
        hip_level_diff = abs(l_hip[1] - r_hip[1])
        
        # Front knee should not extend past ankle (knee-over-toe check)
        if front_is_left:
            knee_past_toe = l_knee[0] < l_ankle[0]
            front_hip, front_knee, front_ankle = l_hip, l_knee, l_ankle
        else:
            knee_past_toe = r_knee[0] > r_ankle[0]
            front_hip, front_knee, front_ankle = r_hip, r_knee, r_ankle

        
        
        # Form checks - use thresholds from the LUNGE_THRESHOLDS dictionary
        min_knee_angle, max_knee_angle = self.LUNGE_THRESHOLDS["knee_angle"]

        # Persistent check for full lunge
        if front_knee_angle > 150:
            self.error_counters["Perform a full lunge."] += 1
        else:
            self.error_counters["Perform a full lunge."] = 0

            # Front knee angle range errors
            if front_knee_angle > max_knee_angle:
                self.error_counters["Bend front knee more"] += 1
            else:
                self.error_counters["Bend front knee more"] = 0

            if front_knee_angle < min_knee_angle:
                self.error_counters["Front knee bent too much"] += 1
            else:
                self.error_counters["Front knee bent too much"] = 0

            # Knee past toe
            #if knee_past_toe:
            #    self.error_counters["Front knee past toes"] += 1
            #else:
            #    self.error_counters["Front knee past toes"] = 0

            # Back knee angle
            min_back_knee, max_back_knee = self.LUNGE_THRESHOLDS["back_knee_angle"]
            if back_knee_angle > max_back_knee:
                self.error_counters["Bend back knee more"] += 1
            else:
                self.error_counters["Bend back knee more"] = 0

            if back_knee_angle < min_back_knee:
                self.error_counters["Back knee bent too much"] += 1
            else:
                self.error_counters["Back knee bent too much"] = 0

        # Collect persistent errors only
        for msg, count in self.error_counters.items():
            if count >= self.error_threshold:
                errors.append(msg)
            
        
            
        
        
        # Track front knee angle for rep detection
        self.knee_angles_history.append(front_knee_angle)
        if len(self.knee_angles_history) > 10:  # Keep history manageable
            self.knee_angles_history.pop(0)
        
        # Store current angles for display
        self.current_front_knee_angle = front_knee_angle
        self.current_back_knee_angle = back_knee_angle
        
        # Calculate average landmark confidence
        landmark_confidences = [
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].visibility,
            landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].visibility,
            landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].visibility,
            landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].visibility,
            landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE].visibility,
            landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE].visibility
        ]
        avg_confidence = sum(landmark_confidences) / len(landmark_confidences)
        
        # Use a smoother method for rep counting with visibility validation
        self._update_rep_counting(front_knee_angle, is_visible, avg_confidence)
        
        # Calculate form quality score
        self.calculate_form_score(front_knee_angle, back_knee_angle, torso_angle, errors)
            
        return errors[:3], front_knee_angle  # Return top 3 errors and knee angle

    def calculate_form_score(self, front_knee_angle, back_knee_angle, torso_angle, errors):
        """Calculate form quality score based on depth, alignment, posture, and stability."""
        # Depth score (based on front knee angle - ideal is 90°)
        depth_ideal = 90
        depth_diff = abs(front_knee_angle - depth_ideal)
        self.depth_score = max(0, 100 - (depth_diff * 2))  # 2 points per degree deviation
        
        # Alignment score (based on back knee angle - ideal is 90-120°)
        if 90 <= back_knee_angle <= 120:
            self.alignment_score = 100
        else:
            alignment_diff = min(abs(back_knee_angle - 90), abs(back_knee_angle - 120))
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
            feedback.append("Go deeper into the lunge")
        if self.posture_score < 70:
            feedback.append("Keep your back straighter")
        if self.alignment_score < 70:
            feedback.append("Bend your back knee more")
        if self.stability_score < 70:
            feedback.append("Focus on stability")
        
        return feedback if feedback else ["Maintain current form"]

    def _update_rep_counting(self, knee_angle, landmarks_visible=True, landmark_confidence=1.0):
        """Improved rep counting logic with hold detection, cooldown, and visibility validation."""
        # Skip if landmarks not visible or confidence too low
        if not landmarks_visible or landmark_confidence < self.min_landmark_confidence:
            logger.debug(f"Skipping frame - visible: {landmarks_visible}, confidence: {landmark_confidence:.2f}")
            return
        
        # Apply angle smoothing
        smoothed_angle = self.knee_angle_smoother.smooth(knee_angle)
        
        # Decrease cooldown if active
        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            if self.cooldown_frames == 0:
                logger.debug("Cooldown ended, ready for next rep")
            return  # Don't process state transitions during cooldown
        
        # State machine with debouncing
        self.state_duration += 1
        
        # Debug logging
        if self.debug_mode and self.state_duration % 10 == 0:
            logger.debug(f"State: {self.state.value}, Angle: {smoothed_angle:.1f}°, Duration: {self.state_duration}")
        
        # State transitions with minimum duration check (debouncing)
        if self.state == LungeState.STANDING and smoothed_angle < 140:
            if self.state_duration >= self.min_state_duration:
                self.state = LungeState.DESCENDING
                self.state_duration = 0
                self.max_knee_bend = 180
                self.shallow_rep_detected = False
                self.hold_duration = 0
                logger.info(f"State transition: STANDING -> DESCENDING")
        elif self.state == LungeState.DESCENDING and smoothed_angle < 110:
            if self.state_duration >= self.min_state_duration:
                self.state = LungeState.LUNGE_POSITION
                self.state_duration = 0
                logger.info(f"State transition: DESCENDING -> LUNGE_POSITION")
        elif self.state == LungeState.LUNGE_POSITION:
            # Track deepest bend
            self.max_knee_bend = min(self.max_knee_bend, smoothed_angle)
            self.hold_duration += 1
            
            # Require minimum hold at bottom position
            if smoothed_angle > 110 and self.hold_duration >= self.min_hold_frames:
                if self.state_duration >= self.min_state_duration:
                    self.state = LungeState.ASCENDING
                    self.state_duration = 0
                    logger.info(f"State transition: LUNGE_POSITION -> ASCENDING (held for {self.hold_duration} frames)")
        elif self.state == LungeState.ASCENDING and smoothed_angle > 150:
            if self.state_duration >= self.min_state_duration:
                self.state = LungeState.STANDING
                self.state_duration = 0
                
                # Count rep if it was deep enough
                if self.max_knee_bend < 110:
                    self.reps += 1
                    self.cooldown_frames = self.cooldown_duration
                    logger.info(f"Rep {self.reps} counted, depth: {self.max_knee_bend:.1f}°, hold: {self.hold_duration} frames, cooldown started")
                else:
                    self.shallow_rep_detected = True
                    logger.info(f"Shallow rep detected: {self.max_knee_bend:.1f}°, hold: {self.hold_duration} frames")

    def reset_counters(self):
        """Reset counters and recording state."""
        self.frame_count = 0
        self.recording = False
        self.start_frame = 0
        self.reps = 0
        self.state = LungeState.STANDING
        self.state_duration = 0
        self.max_knee_bend = 180
        self.shallow_rep_detected = False
        self.hold_duration = 0
        self.cooldown_frames = 0
        self.form_score = 100
        self.depth_score = 100
        self.alignment_score = 100
        self.posture_score = 100
        self.stability_score = 100
        self.report = {
            "good_form_frames": 0,
            "error_counts": defaultdict(int)
        }
        # Reset angle smoothers
        self.knee_angle_smoother.reset()
        self.hip_angle_smoother.reset()
        print(f"{self.exercise} analyzer counters reset")

    async def process_video(self, frame):
        """Process a single frame and return data to broadcast."""
        
        try:
            # Process the frame with MediaPipe Pose
            results = self.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            annotated_frame = frame.copy()  # Create a copy to annotate
            error_text = ""
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(annotated_frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                self.frame_count += 1

                # Display countdown during delay
                if self.frame_count <= self.delay_frames:
                    countdown = int(self.delay_frames / self.fps) - int(self.frame_count / self.fps)
                    cv2.putText(annotated_frame, f"Starting in: {countdown}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                else:
                    # Start correction after delay
                    if not self.recording:
                        self.recording = True
                        self.start_frame = self.frame_count

                    # Call form check method
                    errors, knee_angle = self.check_lunges_form(results.pose_landmarks.landmark)

                    # Record form data during correction
                    if self.recording:
                        if not errors:
                            self.report["good_form_frames"] += 1
                        for error in errors:
                            self.report["error_counts"][error] += 1

                    # Display feedback after delay
                    if self.recording:
                        if errors:
                            for i, error in enumerate(errors):
                                cv2.putText(annotated_frame, error, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        else:
                            cv2.putText(annotated_frame, "Correct Form", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Display rep count
                    cv2.putText(annotated_frame, f"Reps: {self.reps}/{self.target_reps}", (10, annotated_frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    
                    # Display current state
                    cv2.putText(annotated_frame, f"State: {self.state.value}", (10, annotated_frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    
                    # Display front knee angle
                    cv2.putText(annotated_frame, f"Front Knee: {self.current_front_knee_angle:.1f}°", (10, annotated_frame.shape[0] - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # Display back knee angle
                    cv2.putText(annotated_frame, f"Back Knee: {self.current_back_knee_angle:.1f}°", (10, annotated_frame.shape[0] - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    ## TEXT TO SPEECH PORTION
                    error_text = errors[0] if errors else "You are doing well"#



            
            # Encode frame as base64 and return data
            frame_base64 = self._encode_frame(annotated_frame)
            return {
                "type": "frame",
                "data": frame_base64,
                "reps": self.reps,
                "target_reps": self.target_reps,
                "good_form_frames": self.report["good_form_frames"],
                "error_counts": dict(self.report["error_counts"]),  # Convert defaultdict to dict for serialization
                "recording": self.recording,
                "frame_count": self.frame_count - self.start_frame if self.recording else 0,
                "error_text": error_text,
                "form_score": self.form_score,
                "state": self.state.value,
                "front_knee_angle": self.current_front_knee_angle,
                "back_knee_angle": self.current_back_knee_angle
            }
        except Exception as e:
            logger.error(f"Error processing video frame: {str(e)}")
            # Return a minimal response on error
            return {
                "type": "error",
                "error": f"Processing error: {str(e)}"
            }

    def _encode_frame(self, frame):
        """Encode frame as base64."""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    def generate_report(self):
        """Generate and return an exercise report."""
        if not self.recording or self.frame_count <= self.start_frame:
            return "No exercise session recorded yet."
            
        total_recorded_frames = self.frame_count - self.start_frame  # Frames from start of correction
        if total_recorded_frames <= 0:
            return "No frames recorded yet."
            
        good_form_seconds = self.report["good_form_frames"] / self.fps
        total_seconds = total_recorded_frames / self.fps
    
        report_text = f"\n--- {self.exercise} Exercise Report ---\n"
        report_text += f"Total Recorded Time: {total_seconds:.2f} seconds\n"
        report_text += f"Good Form Duration: {good_form_seconds:.2f} seconds ({(good_form_seconds / total_seconds) * 100:.1f}%)\n"
        report_text += f"Repetitions Completed: {self.reps}/{self.target_reps}\n"
        
        if self.reps >= self.target_reps:
            report_text += "Goal achieved! 🎉\n"
        
        report_text += "\nErrors Detected:\n"
        if self.report["error_counts"]:
            # Sort errors by frequency
            sorted_errors = sorted(
                self.report["error_counts"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for error, count in sorted_errors:
                error_seconds = count / self.fps
                report_text += f"  - '{error}': {count} frames ({error_seconds:.2f} seconds, {(count / total_recorded_frames) * 100:.1f}%)\n"
        else:
            report_text += "  - No errors detected! Perfect form!\n"
        
        report_text += "\nAreas to Focus On:\n"
        if self.report["error_counts"]:
            # Get top frequent error
            top_errors = sorted_errors[:1]
            for error, _ in top_errors:
                if "knee" in error.lower():
                    report_text += "  - Work on proper knee alignment and depth\n"
                elif "torso" in error.lower():
                    report_text += "  - Practice maintaining an upright torso position\n"
                elif "hip" in error.lower():
                    report_text += "  - Focus on keeping hips level throughout the movement\n"
                elif "stance" in error.lower():
                    report_text += "  - Adjust your stance width for better stability\n"
                else:
                    report_text += f"  - Practice proper form for: {error}\n"
        else:
            report_text += "  - Continue with your excellent form!\n"
            
        report_text += "--------------------------------\n"
        
        # Print the report too
        print(report_text)
        
        return report_text

    def __del__(self):
        """Clean up resources when the object is deleted."""
        try:
            if hasattr(self, 'pose'):
                self.pose.close()
        except Exception as e:
            print(f"Error closing pose: {e}")
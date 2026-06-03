# slr_analyzer.py
import cv2
import mediapipe as mp
import numpy as np
from collections import defaultdict, deque
from enum import Enum
import logging
import base64

logger = logging.getLogger(__name__)


class LegRaiseState(Enum):
    """States for leg raise repetition state machine"""
    STARTING = "STARTING"
    RAISING = "RAISING"
    AT_TOP = "AT_TOP"
    LOWERING = "LOWERING"
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

class SLRExerciseAnalyzer:
    def __init__(self, exercise="straight_leg_raises_rehab", delay_seconds=3, target_reps = 8, fps=30):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose()
        
        # Initialize new components
        self.visibility_checker = LandmarkVisibilityChecker(self.mp_pose)
        self.leg_angle_smoother = AngleSmoother(alpha=0.3, window_size=5)
        self.knee_angle_smoother = AngleSmoother(alpha=0.3, window_size=5)

        # Thresholds for rehab straight leg raises
        self.THRESHOLDS = {
            "affected_leg_target_angle": (10, 30),  # Tolerance around target angle
            "affected_leg_straightness": (160, 180),  # Affected leg should be straight
            "non_affected_knee_angle": (60, 120),  # Knee bend range
            "torso_angle": (0, 30),  # Torso flat on ground
            "hip_movement": (0, 0.15)  # Max allowed hip movement (normalized units)
        }

        # Recording and rep counting settings
        self.fps = fps
        self.delay_frames = delay_seconds * fps  # 3-second delay before correction
        self.target_reps = target_reps  # Number of reps to detect
        self.frame_count = 0
        self.recording = False  # Now indicates correction active
        self.report = {
            "good_form_frames": 0,
            "error_counts": defaultdict(int)
        }

        self.is_above_30 = False

        # Rep counting variables with improved state machine
        self.reps = 0
        self.state = LegRaiseState.STARTING  # Initial state using enum
        self.prev_affected_angle = None
        self.target_angle = None

        self.peak_leg_angle = 180
        self.shallow_rep_detected = False

        # Hip movement tracking
        self.initial_hip_y = None  # Baseline hip position
        
        # State machine timing
        self.state_duration = 0  # Frames spent in current state
        self.min_state_duration = 3  # Minimum frames before state transition (debouncing)
        
        # Hold detection at top position (0.3-0.5 seconds)
        self.hold_duration = 0  # Frames spent in AT_TOP
        self.min_hold_frames = int(0.4 * fps)  # 0.4 seconds minimum hold
        
        # Cooldown after successful rep (prevent double-counting)
        self.cooldown_frames = 0
        self.cooldown_duration = int(0.5 * fps)  # 0.5 seconds cooldown
        
        # Low-confidence frame filtering
        self.min_landmark_confidence = 0.3
        
        # Debug logging
        self.debug_mode = True
        
        # Current angles for display
        self.current_leg_angle = 180
        self.current_knee_angle = 180
        
        # Form quality scoring
        self.form_score = 100
        self.depth_score = 100
        self.alignment_score = 100
        self.posture_score = 100
        self.stability_score = 100

    def calculate_angle(self, p1, p2, p3):
        """Calculate the angle between three points in degrees."""
        a = np.array(p1)
        b = np.array(p2)
        c = np.array(p3)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle) * 180 / np.pi
        return angle

    def check_straight_leg_raises_rehab(self, landmarks):
        """Analyze straight leg raises with improved visibility checking and angle smoothing."""
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

        # Calculate torso angle
        mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        torso_angle = self.calculate_angle(mid_hip, mid_shoulder, [mid_hip[0] + 1, mid_hip[1]])  # Horizontal

        # Set initial hip position (once at start)
        if self.initial_hip_y is None:
            self.initial_hip_y = mid_hip[1]

        # Check hip movement
        hip_deviation = abs(mid_hip[1] - self.initial_hip_y)
        #if not self.THRESHOLDS["hip_movement"][0] <= hip_deviation <= self.THRESHOLDS["hip_movement"][1]:
        #    errors.append("Keep your hips on the ground")

        # Determine affected and non-affected legs
        left_knee_angle = self.calculate_angle(l_hip, l_knee, l_ankle)
        right_knee_angle = self.calculate_angle(r_hip, r_knee, r_ankle)
        if left_knee_angle < right_knee_angle:  # Left leg is non-affected (bent)
            non_affected_hip, non_affected_knee, non_affected_ankle = l_hip, l_knee, l_ankle
            affected_hip, affected_knee, affected_ankle = r_hip, r_knee, r_ankle
            affected_leg_angle = self.calculate_angle(r_hip, r_knee, r_ankle)
            non_affected_leg_angle = self.calculate_angle(l_hip, l_knee, mid_hip)
        else:  # Right leg is non-affected (bent)
            non_affected_hip, non_affected_knee, non_affected_ankle = r_hip, r_knee, r_ankle
            affected_hip, affected_knee, affected_ankle = l_hip, l_knee, l_ankle
            affected_leg_angle = self.calculate_angle(l_hip, l_knee, l_ankle)
            non_affected_leg_angle = self.calculate_angle(r_hip, r_knee, mid_hip)
            
        target_angle = self.calculate_angle(mid_hip, non_affected_hip, non_affected_knee)
        self.target_angle = target_angle if self.target_angle is None else self.target_angle

        # Affected leg angle relative to torso
        affected_torso_angle = self.calculate_angle(mid_hip, affected_hip, affected_knee)

        leg_angle = self.calculate_angle(r_shoulder, r_hip, r_knee)
        
        # Apply angle smoothing
        leg_angle = self.leg_angle_smoother.smooth(leg_angle)

        # Store current angles for display
        self.current_leg_angle = leg_angle
        self.current_knee_angle = affected_leg_angle
        
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
        
        if affected_leg_angle < 160:
            errors.append("Keep your leg straight.")
        if leg_angle < 120:
            errors.append("Leg is too high.")

        if self.is_above_30:
            self.peak_leg_angle = min(self.peak_leg_angle, leg_angle)

        if self.shallow_rep_detected == True:
            errors.append("Shallow rep, raise leg higher next time.")
        
        # Rep counting logic with improved state machine
        # Skip if landmarks not visible or confidence too low
        if not is_visible or avg_confidence < self.min_landmark_confidence:
            logger.debug(f"Skipping frame - visible: {is_visible}, confidence: {avg_confidence:.2f}")
            return errors[:3], leg_angle
        
        # Decrease cooldown if active
        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            if self.cooldown_frames == 0:
                logger.debug("Cooldown ended, ready for next rep")
            return errors[:3], leg_angle  # Don't process state transitions during cooldown
        
        self.state_duration += 1
        
        # Debug logging
        if self.debug_mode and self.state_duration % 10 == 0:
            logger.debug(f"State: {self.state.value}, Angle: {leg_angle:.1f}°, Duration: {self.state_duration}")
        
        # State transitions with minimum duration check (debouncing)
        if self.state == LegRaiseState.STARTING and leg_angle < 140:
            if self.state_duration >= self.min_state_duration:
                self.state = LegRaiseState.RAISING
                self.state_duration = 0
                self.peak_leg_angle = 180
                self.shallow_rep_detected = False
                self.hold_duration = 0
                logger.info(f"State transition: STARTING -> RAISING")
        elif self.state == LegRaiseState.RAISING and leg_angle < 120:
            if self.state_duration >= self.min_state_duration:
                self.state = LegRaiseState.AT_TOP
                self.state_duration = 0
                logger.info(f"State transition: RAISING -> AT_TOP")
        elif self.state == LegRaiseState.AT_TOP:
            # Track peak leg angle
            self.peak_leg_angle = min(self.peak_leg_angle, leg_angle)
            self.hold_duration += 1
            if leg_angle > 120 and self.hold_duration >= self.min_hold_frames:
                if self.state_duration >= self.min_state_duration:
                    self.state = LegRaiseState.LOWERING
                    self.state_duration = 0
                    logger.info(f"State transition: AT_TOP -> LOWERING (held for {self.hold_duration} frames)")
        elif self.state == LegRaiseState.LOWERING and leg_angle > 140:
            if self.state_duration >= self.min_state_duration:
                self.state = LegRaiseState.STARTING
                self.state_duration = 0
                
                # Count rep if it was deep enough
                if self.peak_leg_angle < 130:
                    self.reps += 1
                    self.cooldown_frames = self.cooldown_duration
                    logger.info(f"Rep counted. Total reps: {self.reps}, depth: {self.peak_leg_angle:.1f}°, hold: {self.hold_duration} frames, cooldown started")
                else:
                    self.shallow_rep_detected = True
                    logger.info(f"Shallow rep detected: {self.peak_leg_angle:.1f}°, hold: {self.hold_duration} frames")
                
                self.peak_leg_angle = 180
        
        # Calculate form quality score
        self.calculate_form_score(leg_angle, affected_leg_angle, torso_angle, errors)
        
        return errors[:3], leg_angle

    def calculate_form_score(self, leg_angle, knee_angle, torso_angle, errors):
        """Calculate form quality score based on depth, alignment, posture, and stability."""
        # Depth score (based on leg angle - ideal is 120-140° for leg raises)
        if 120 <= leg_angle <= 140:
            self.depth_score = 100
        else:
            depth_diff = min(abs(leg_angle - 120), abs(leg_angle - 140))
            self.depth_score = max(0, 100 - (depth_diff * 2))
        
        # Alignment score (based on knee angle - ideal is 160-180° for straight leg)
        if 160 <= knee_angle <= 180:
            self.alignment_score = 100
        else:
            alignment_diff = min(abs(knee_angle - 160), abs(knee_angle - 180))
            self.alignment_score = max(0, 100 - (alignment_diff * 2))
        
        # Posture score (based on torso angle - ideal is 0-30° from horizontal)
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
            feedback.append("Raise your leg higher")
        if self.posture_score < 70:
            feedback.append("Keep your back flat on ground")
        if self.alignment_score < 70:
            feedback.append("Keep your leg straight")
        if self.stability_score < 70:
            feedback.append("Focus on stability")
        
        return feedback if feedback else ["Maintain current form"]

    def reset_counters(self):
        """Reset counters and recording state."""
        self.frame_count = 0
        self.recording = False
        self.start_frame = 0
        self.reps = 0
        self.state = LegRaiseState.STARTING
        self.state_duration = 0
        self.peak_leg_angle = 180
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
            "error_counts": {}
        }
        # Reset angle smoothers
        self.leg_angle_smoother.reset()
        self.knee_angle_smoother.reset()

    async def process_video(self, frame):
        """Process a single frame and return data to broadcast."""
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

                errors, affected_torso_angle = self.check_straight_leg_raises_rehab(results.pose_landmarks.landmark)

                # Record form data during correction
                if self.recording:
                    if not errors:
                        self.report["good_form_frames"] += 1
                    for error in errors:
                        if error not in self.report["error_counts"]:
                            self.report["error_counts"][error] = 0
                        self.report["error_counts"][error] += 1

                # Display feedback after delay
                if self.recording:
                    if errors:
                        for i, error in enumerate(errors):
                            cv2.putText(annotated_frame, error, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    elif self.is_above_30:
                        cv2.putText(annotated_frame, "Correct Form", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        cv2.putText(annotated_frame, "Ready - Raise your leg", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                # Display rep count
                cv2.putText(annotated_frame, f"Reps: {self.reps}/{self.target_reps}", (10, annotated_frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Display current state
                cv2.putText(annotated_frame, f"State: {self.state.value}", (10, annotated_frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Display leg angle
                cv2.putText(annotated_frame, f"Leg Angle: {self.current_leg_angle:.1f}°", (10, annotated_frame.shape[0] - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Display knee angle
                cv2.putText(annotated_frame, f"Knee Angle: {self.current_knee_angle:.1f}°", (10, annotated_frame.shape[0] - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                ### TEXT TO SPEECH PORTION
                if errors:
                    error_text = errors[0]
                    if len(errors) > 1:
                        error_text += " " + errors[1]
                else:
                    error_text = "You are doing well."

        # Encode frame as base64 and return data
        frame_base64 = self._encode_frame(annotated_frame)
        return {
            "type": "frame",
            "data": frame_base64,
            "reps": self.reps,
            "target_reps": self.target_reps,
            "good_form_frames": self.report["good_form_frames"],
            "error_counts": self.report["error_counts"],
            "recording": self.recording,
            "frame_count": self.frame_count - self.start_frame if self.recording else 0,
            "error_text": error_text,
            "form_score": self.form_score,
            "state": self.state.value,
            "leg_angle": self.current_leg_angle,
            "knee_angle": self.current_knee_angle
        }

    def _encode_frame(self, frame):
        """Encode frame as base64."""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    def generate_report(self):
        """Generate and print an exercise report."""
        total_recorded_frames = self.frame_count - self.start_frame  # Frames from start of correction
        good_form_seconds = self.report["good_form_frames"] / self.fps
        total_seconds = total_recorded_frames / self.fps
    
        print("\n--- Straight Leg Raises (Rehab) Exercise Report ---")
        print(f"Total Recorded Time: {total_seconds:.2f} seconds")
        print(f"Good Form Duration: {good_form_seconds:.2f} seconds ({(good_form_seconds / total_seconds) * 100:.1f}%)")
        print(f"Repetitions Completed: {self.reps}")
        print("Errors Detected:")
        if self.report["error_counts"]:
            for error, count in self.report["error_counts"].items():
                error_seconds = count / self.fps
                print(f"  - '{error}': {count} frames ({error_seconds:.2f} seconds, {(count / total_recorded_frames) * 100:.1f}%)")
        else:
            print("  - No errors detected!")
        print("--------------------------------\n")

    def run(self):
        """Run the analyzer with webcam input."""
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
    
            frame = self.process_frame(frame)
            cv2.imshow("Straight Leg Raises (Rehab) Correction", frame)
    
            if self.recording and self.reps >= self.target_reps:
                self.generate_report()
                break
    
            if cv2.waitKey(1) & 0xFF == ord('q'):
                if self.recording:
                    self.generate_report()
                break
    
        cap.release()
        cv2.destroyAllWindows()
        self.pose.close()

    def __del__(self):
        self.pose.close()
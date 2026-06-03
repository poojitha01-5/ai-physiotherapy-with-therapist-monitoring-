"use client";
import React, { useState, useEffect, useRef } from "react";
import { Sidebar } from "../../sidebar/sidebar";
import { useAudio } from "@/contexts/AudioContexts";
import { useUser } from "@/contexts/AppContext";

export default function SquatVision() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [frameSrc, setFrameSrc] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<
    "connected" | "connecting" | "disconnected"
  >("disconnected");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [formStatus, setFormStatus] = useState<"good" | "bad" | null>(null);
  const [repCount, setRepCount] = useState<number>(0);
  const [prediction, setPrediction] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const audioRef = useRef<HTMLAudioElement | null>(null); // Ref for audio element
  const isRunningRef = useRef(false); // Ref to track running state inside WS closures
  const MAX_RECONNECT_ATTEMPTS = 5;
  const { audiobot } = useAudio();
  const { username } = useUser();

  // New state for calibration, form score, and exercise data
  const [calibrationStatus, setCalibrationStatus] = useState<"pending" | "passed" | "failed">("pending");
  const [calibrationMessage, setCalibrationMessage] = useState<string>("");
  const [formScore, setFormScore] = useState<number>(100);
  const [exerciseState, setExerciseState] = useState<string>("");
  const [kneeAngle, setKneeAngle] = useState<number>(180);
  const [hipAngle, setHipAngle] = useState<number>(180);

  // Keep isRunningRef in sync with isRunning state
  useEffect(() => {
    isRunningRef.current = isRunning;
  }, [isRunning]);

  // Initialize audio element
  useEffect(() => {
    audioRef.current = new Audio();
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus("connecting");
    setErrorMessage(null);

    const ws = new WebSocket("ws://localhost:8765");

    ws.onopen = () => {
      console.log("WebSocket connected");
      setConnectionStatus("connected");
      reconnectAttemptsRef.current = 0;

      ws.send(JSON.stringify({ action: "connect", client: "squatvision" }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received WebSocket message:", data);

        if (data.type === "frame") {
          setFrameSrc(`data:image/jpeg;base64,${data.data}`);
          setPrediction(data.prediction || null);
          setConfidence(data.confidence || null);
          setRepCount(data.rep_count || 0);
          
          // Update new fields from backend
          setFormScore(data.form_score || 100);
          setExerciseState(data.state || "");
          setKneeAngle(data.knee_angle || 180);
          setHipAngle(data.hip_angle || 180);

          // Only show error_text feedback when exercise is actually running
          if (data.error_text && isRunningRef.current) {
            setErrorMessage(data.error_text);
          } else if (!isRunningRef.current) {
            setErrorMessage(null);
          } else {
            setErrorMessage(null);
          }

          if (data.prediction) {
            setFeedback(
              data.prediction === "good"
                ? "Good form! Keep it up."
                : `Form issue: ${data.prediction}`
            );
            setFormStatus(data.prediction === "good" ? "good" : "bad");
          } else {
            setFeedback(null);
            setFormStatus(null);
          }
        } else if (data.type === "calibration") {
          // Handle calibration messages
          if (data.status === "passed") {
            setCalibrationStatus("passed");
            setCalibrationMessage("Calibration passed - Starting exercise");
          } else if (data.status === "failed") {
            setCalibrationStatus("failed");
            setCalibrationMessage(data.message || "Calibration failed");
          }
        } else if (data.type === "audio") {
          if (data.audio_data && audiobot === "on") {
            const audioBlob = base64ToBlob(data.audio_data, "audio/mpeg");
            const audioUrl = URL.createObjectURL(audioBlob);
            if (audioRef.current) {
              audioRef.current.src = audioUrl;
              audioRef.current.play().catch((e) => {
                console.error("Audio playback error:", e);
                setErrorMessage("Failed to play audio feedback.");
              });
              audioRef.current.onended = () => {
                URL.revokeObjectURL(audioUrl);
                audioRef.current!.onended = null;
              };
            }
          }
        } else if (data.status) {
          if (data.status === "started") {
            setIsRunning(true);
          } else if (data.status === "stopped") {
            setIsRunning(false);
            setFrameSrc(null);
            setFeedback(null);
            setFormStatus(null);
            setErrorMessage(null);
          }
        } else if (data.error) {
          setErrorMessage(data.error);
          setIsRunning(false);
          setFrameSrc(null);
          setFeedback(null);
          setFormStatus(null);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
        setErrorMessage("Error processing server message.");
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket disconnected with code ${event.code}`);
      setConnectionStatus("disconnected");

      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const timeout = Math.min(
          3000 * (reconnectAttemptsRef.current + 1),
          15000
        );
        console.log(`Reconnecting in ${timeout / 1000} seconds...`);

        setTimeout(() => {
          reconnectAttemptsRef.current += 1;
          connectWebSocket();
        }, timeout);
      } else {
        setErrorMessage("Failed to connect. Please try manually reconnecting.");
      }
    };

    ws.onerror = () => {
      setErrorMessage("Connection error. Retrying...");
    };

    wsRef.current = ws;
  };

  // Convert base64 to Blob for audio playback
  const base64ToBlob = (base64: string, mimeType: string) => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };

  const startSquats = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setErrorMessage(null);
      setCalibrationStatus("pending");
      setCalibrationMessage("Starting calibration...");
      setFormScore(100);
      setExerciseState("");
      setRepCount(0);
      
      wsRef.current.send(
        JSON.stringify({
          action: "start",
          exercise: "Squats",
          audiobot,
          username: username || localStorage.getItem("username") || "",
        })
      );
    } else {
      setErrorMessage("Not connected to server. Trying to reconnect...");
      connectWebSocket();
    }
  };

  const stopSquats = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    } else {
      setIsRunning(false);
      setFrameSrc(null);
      setFeedback(null);
      setFormStatus(null);
    }
    
    setIsRunning(false);
    setCalibrationStatus("pending");
    setCalibrationMessage("");
    setFormScore(100);
    setExerciseState("");
    setRepCount(0);
  };

  const manualReconnect = () => {
    reconnectAttemptsRef.current = 0;
    setCalibrationStatus("pending");
    setCalibrationMessage("");
    setFormScore(100);
    setExerciseState("");
    setRepCount(0);
    connectWebSocket();
  };

  return (
    <div className="flex min-h-screen overflow-hidden bg-black">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="flex-1 container mx-auto px-10 py-[1.4%] bg-black">
        <div className="h-16 w-full bg-gray-800 rounded-lg mb-4 flex items-center justify-center">
          <h1 className="text-4xl font-bold text-white">Squat Exercise</h1>
        </div>

        {errorMessage && (
          <div className="mb-4 p-4 bg-red-500 text-white rounded-lg">
            {errorMessage}
          </div>
        )}

        <div className="flex flex-col items-center justify-center h-[80vh] bg-gray-900 rounded-lg overflow-hidden relative">
          {/* Persistent Instruction Panel */}
          <div className="absolute top-4 right-4 bg-black/70 backdrop-blur-md p-4 rounded-lg text-white max-w-xs z-10">
            <h3 className="text-lg font-bold mb-2 text-indigo-400">Instructions</h3>
            <ul className="text-sm space-y-1">
              <li>1. Stand with feet shoulder-width</li>
              <li>2. Lower hips back and down</li>
              <li>3. Keep chest up</li>
              <li>4. Knees track over toes</li>
              <li>5. Squat until thighs parallel</li>
              <li>6. Return to standing</li>
            </ul>
          </div>

          {/* Calibration UI */}
          {calibrationStatus !== "passed" && isRunning && (
            <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-md p-4 rounded-lg text-white z-10">
              <h3 className="text-lg font-bold mb-2 text-yellow-400">Calibration</h3>
              <p className="text-sm">{calibrationMessage || "Calibrating..."}</p>
              {calibrationStatus === "failed" && (
                <p className="text-xs text-red-400 mt-1">Please adjust your position</p>
              )}
            </div>
          )}

          {/* Form Score Display */}
          {calibrationStatus === "passed" && isRunning && (
            <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-md p-4 rounded-lg text-white z-10">
              <h3 className="text-lg font-bold mb-2 text-green-400">Form Score</h3>
              <p className="text-3xl font-bold">{formScore.toFixed(0)}%</p>
              <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                <div 
                  className={`h-2 rounded-full ${formScore >= 80 ? 'bg-green-500' : formScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${formScore}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Exercise State and Angles Display */}
          {calibrationStatus === "passed" && isRunning && (
            <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-md p-4 rounded-lg text-white z-10">
              <h3 className="text-lg font-bold mb-2 text-blue-400">Exercise Data</h3>
              <p className="text-sm">State: <span className="font-semibold">{exerciseState}</span></p>
              <p className="text-sm">Reps: <span className="font-semibold">{repCount}</span></p>
              <p className="text-sm">Knee Angle: <span className="font-semibold">{kneeAngle.toFixed(1)}°</span></p>
              <p className="text-sm">Hip Angle: <span className="font-semibold">{hipAngle.toFixed(1)}°</span></p>
            </div>
          )}

          {frameSrc ? (
            <>
              <img
                src={frameSrc}
                alt="Webcam Feed"
                className="w-full h-full object-contain"
                onError={(e) => {
                  console.error("Error loading image:", e);
                  setFrameSrc(null);
                }}
              />
              {feedback && (
                <div
                  className={`absolute bottom-6 left-1/2 transform -translate-x-1/2 px-6 py-2 max-w-sm w-[90%] rounded-xl text-center text-base font-semibold backdrop-blur-md shadow-lg ${
                    formStatus === "good" ? "bg-green-500/70" : "bg-red-500/70"
                  } text-white`}
                >
                  {feedback}
                </div>
              )}
              {
                <div className="absolute top-4 left-4 bg-black/50 p-2 rounded-lg text-white">
                  <p>Reps: {repCount}</p>
                  {/* <p>Prediction: {prediction || "N/A"}</p> */}
                </div>
              }
            </>
          ) : (
            <div className="text-white text-center">
              <p className="text-gray-400 text-xl mb-4">
                {connectionStatus === "connected"
                  ? "Ready to start exercise detection"
                  : connectionStatus === "connecting"
                  ? "Connecting to server..."
                  : "Disconnected from server"}
              </p>
              <p className="text-gray-500">
                {connectionStatus === "connected"
                  ? 'Click "Start Squats" to begin'
                  : connectionStatus === "connecting"
                  ? "Please wait..."
                  : "Please reconnect to start"}
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-center mt-4 space-x-4">
          <button
            onClick={isRunning ? stopSquats : startSquats}
            disabled={connectionStatus !== "connected"}
            className={`px-6 py-3 text-white rounded-lg transition duration-200 ${
              isRunning
                ? "bg-red-500 hover:bg-red-600"
                : "bg-green-500 hover:bg-green-600"
            } ${
              connectionStatus !== "connected"
                ? "opacity-50 cursor-not-allowed"
                : ""
            }`}
          >
            {isRunning ? "Stop Squats" : "Start Squats"}
          </button>

          {connectionStatus !== "connected" && (
            <button
              onClick={manualReconnect}
              className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition duration-200"
            >
              {connectionStatus === "connecting"
                ? "Reconnecting..."
                : "Reconnect"}
            </button>
          )}
        </div>

        <div className="mt-4 text-center text-gray-500">
          Status:{" "}
          {connectionStatus === "connected" ? (
            <span className="text-green-500">Connected</span>
          ) : connectionStatus === "connecting" ? (
            <span className="text-yellow-500">Connecting...</span>
          ) : (
            <span className="text-red-500">Disconnected</span>
          )}
        </div>
      </div>
    </div>
  );
}

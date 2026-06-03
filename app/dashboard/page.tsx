"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "../sidebar/sidebar";
import { useUser } from "@/contexts/AppContext";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const COLORS = ['#818cf8', '#34d399', '#fbbf24', '#f87171', '#60a5fa'];

// Types for the data
interface User {
  name?: string;
  email?: string;
  sex?: string;
  hypertension?: string;
  diabetes?: string;
  pain_category?: string;
  bmi?: number;
  age?: number;
  height?: number;
}

interface WeeklyPlan {
  username: string;
  weekly_plans: string[];
}

interface ErrorData {
  message: string;
  duration: number;
  percent: number;
}

interface Report {
  exercise: string;
  timestamp: string;
  content: string;
  errors: ErrorData[];
  good_form_duration: number;
  total_duration: number;
  analyzer?: string;
}

interface ExerciseReport {
  username: string;
  exercise_type: string;
  rep_count: number;
  errors: string[];
  raw_report?: string;
  timestamp: string;
}

// API functions
const fetchUserData = async (username: string): Promise<User | null> => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/user/${username}`);
    if (!response.ok) {
      console.error("Failed to fetch user data, status:", response.status);
      return null;
    }
    const data = await response.json();
    console.log("User data fetched:", data);
    return data.success ? data.user : null;
  } catch (error) {
    console.error("Error fetching user data:", error);
    return null;
  }
};

const fetchWeeklyPlan = async (
  username: string
): Promise<WeeklyPlan | null> => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8001/weekly-plan/${username}`
    );
    if (!response.ok) {
      console.error("Failed to fetch weekly plan, status:", response.status);
      return null;
    }
    const data = await response.json();
    console.log("Weekly plan fetched:", data);
    return data;
  } catch (error) {
    console.error("Error fetching weekly plan:", error);
    return null;
  }
};

const Dashboard: React.FC = () => {
  const { username } = useUser(); // Use username from context
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userData, setUserData] = useState<User | null>(null);
  const [weeklyPlanData, setWeeklyPlanData] = useState<WeeklyPlan | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [myReports, setMyReports] = useState<ExerciseReport[]>([]);
  const [progressLoading, setProgressLoading] = useState(false);

  // Appointment system states
  const [doctorsList, setDoctorsList] = useState<any[]>([]);
  const [selectedDoctorUsername, setSelectedDoctorUsername] = useState("");
  const [appointmentDate, setAppointmentDate] = useState("");
  const [appointmentTime, setAppointmentTime] = useState("");
  const [appointmentReason, setAppointmentReason] = useState("");
  const [bookingMessage, setBookingMessage] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [appointmentsList, setAppointmentsList] = useState<any[]>([]);
  const [appointmentsLoading, setAppointmentsLoading] = useState(false);

  const fetchAppointments = async () => {
    if (!username) return;
    setAppointmentsLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/appointments/patient/${username}`);
      const data = await res.json();
      if (data.success) {
        setAppointmentsList(data.appointments);
      }
    } catch (e) {
      console.error("Error fetching appointments:", e);
    } finally {
      setAppointmentsLoading(false);
    }
  };

  const fetchDoctors = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/doctors");
      const data = await res.json();
      if (data.success) {
        setDoctorsList(data.doctors);
        if (data.doctors.length > 0) {
          setSelectedDoctorUsername(data.doctors[0].username);
        }
      }
    } catch (e) {
      console.error("Error fetching doctors:", e);
    }
  };

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !selectedDoctorUsername || !appointmentDate || !appointmentTime) {
      setBookingMessage("Please fill in all required fields.");
      return;
    }
    setBookingLoading(true);
    setBookingMessage("");
    try {
      const selectedDoc = doctorsList.find(d => d.username === selectedDoctorUsername);
      const res = await fetch("http://127.0.0.1:8000/api/appointments/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_username: username,
          doctor_username: selectedDoctorUsername,
          doctor_name: selectedDoc?.name || selectedDoctorUsername,
          date: appointmentDate,
          time: appointmentTime,
          reason: appointmentReason,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setBookingMessage("Appointment booked successfully! Pending confirmation.");
        setAppointmentDate("");
        setAppointmentTime("");
        setAppointmentReason("");
        fetchAppointments();
      } else {
        setBookingMessage(`Failed to book appointment: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Failed to book:", err);
      setBookingMessage("Error occurred while booking appointment. Please try again.");
    } finally {
      setBookingLoading(false);
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  useEffect(() => {
    const fetchData = async () => {
      if (!username) {
        console.log("No username available, skipping data fetch");
        return;
      }

      console.log("Fetching data for username:", username);

      // Fetch user data
      const data = await fetchUserData(username);
      setUserData(data);

      // Fetch weekly plan data
      const weeklyPlan = await fetchWeeklyPlan(username);
      setWeeklyPlanData(weeklyPlan);

      // Fetch latest vision report (no username needed)
      try {
        const res = await fetch(
          `http://127.0.0.1:8001/vision-report/latest` // Fixed: use port 8001 (chatbot backend) instead of 8000
        );
        if (res.ok) {
          const reportData = await res.json();
          console.log("Vision report fetched:", reportData);

          // Parse the content to extract information
          const contentLines = reportData.content.split("\n");
          const totalDurationMatch = contentLines
            .find((line: string) => line.includes("Total Recorded Time"))
            ?.match(/(\d+\.\d+) seconds/);
          const totalDuration = totalDurationMatch
            ? parseFloat(totalDurationMatch[1])
            : 0;

          // Parse actual errors from the report if available
          const errorLines = contentLines.filter((line: string) => line.includes("- '"));
          const actualErrors = errorLines.map((line: string) => {
            const messageMatch = line.match(/- '([^']+)'/);
            const durationMatch = line.match(/(\d+\.\d+) seconds/);
            const percentMatch = line.match(/(\d+\.\d+)%/);
            return {
              message: messageMatch ? messageMatch[1] : "Unknown error",
              duration: durationMatch ? parseFloat(durationMatch[1]) : 0,
              percent: percentMatch ? parseFloat(percentMatch[1]) : 0,
            };
          });

          const errors = actualErrors.length > 0 ? actualErrors : [
            {
              message: "Knee alignment issue",
              duration: totalDuration * 0.2,
              percent: 20,
            },
            {
              message: "Arm position incorrect",
              duration: totalDuration * 0.15,
              percent: 15,
            },
            {
              message: "Torso not straight",
              duration: totalDuration * 0.1,
              percent: 10,
            },
          ];

          const errorTime = errors.reduce(
            (total: number, err: ErrorData) => total + err.duration,
            0
          );
          const goodFormDuration = Math.max(0, totalDuration - errorTime);

          const processedReport: Report = {
            exercise: reportData.exercise,
            timestamp: reportData.timestamp,
            content: reportData.content,
            errors: errors,
            good_form_duration: goodFormDuration,
            total_duration: totalDuration,
            analyzer: reportData.analyzer, // in case backend sends it
          };

          setReport(processedReport);
        } else {
          console.error("Failed to fetch vision report, status:", res.status);
        }
      } catch (error) {
        console.error("Error fetching vision report:", error);
      }
    };

    fetchData();
  }, [username]);

  // Fetch personal exercise reports
  useEffect(() => {
    if (!username) return;
    setProgressLoading(true);
    fetch(`http://127.0.0.1:8000/api/patient/reports/${username}`)
      .then((r) => r.json())
      .then((d) => { if (d.success) setMyReports(d.reports); })
      .catch(console.error)
      .finally(() => setProgressLoading(false));
  }, [username]);

  // WebSocket connection for real-time vision updates
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('WebSocket connected to vision backend');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);

            // Update vision report if new data comes in
            if (data.exercise && data.content) {
              const contentLines = data.content.split("\n");
              const totalDurationMatch = contentLines
                .find((line: string) => line.includes("Total Recorded Time"))
                ?.match(/(\d+\.\d+) seconds/);
              const totalDuration = totalDurationMatch
                ? parseFloat(totalDurationMatch[1])
                : 0;

              // Parse actual errors from the report if available
              const errorLines = contentLines.filter((line: string) => line.includes("- '"));
              const actualErrors = errorLines.map((line: string) => {
                const messageMatch = line.match(/- '([^']+)'/);
                const durationMatch = line.match(/(\d+\.\d+) seconds/);
                const percentMatch = line.match(/(\d+\.\d+)%/);
                return {
                  message: messageMatch ? messageMatch[1] : "Unknown error",
                  duration: durationMatch ? parseFloat(durationMatch[1]) : 0,
                  percent: percentMatch ? parseFloat(percentMatch[1]) : 0,
                };
              });

              const errors = actualErrors.length > 0 ? actualErrors : [];

              const errorTime = errors.reduce(
                (total: number, err: ErrorData) => total + err.duration,
                0
              );
              const goodFormDuration = Math.max(0, totalDuration - errorTime);

              const processedReport: Report = {
                exercise: data.exercise,
                timestamp: data.timestamp || new Date().toISOString(),
                content: data.content,
                errors: errors,
                good_form_duration: goodFormDuration,
                total_duration: totalDuration,
                analyzer: data.analyzer || "Vision Backend",
              };

              setReport(processedReport);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected, attempting to reconnect in 5 seconds...');
          reconnectTimer = setTimeout(connectWebSocket, 5000);
        };
      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    if (username) {
      fetchAppointments();
    }
  }, [username]);

  // Chart data derived from personal reports
  const progressChartData = [...myReports].reverse().map((r, i) => ({
    session: `S${i + 1}`,
    reps: r.rep_count,
    date: new Date(r.timestamp).toLocaleDateString(),
  }));

  const exerciseBreakdown = myReports.reduce<Record<string, number>>((acc, r) => {
    acc[r.exercise_type] = (acc[r.exercise_type] || 0) + r.rep_count;
    return acc;
  }, {});
  const breakdownChartData = Object.entries(exerciseBreakdown).map(([k, v]) => ({
    exercise: k,
    totalReps: v,
  }));

  // Function to parse and display weekly plan
  const renderWeeklyPlan = () => {
    if (
      !weeklyPlanData ||
      !weeklyPlanData.weekly_plans ||
      weeklyPlanData.weekly_plans.length === 0
    ) {
      return <p className="text-sm">No weekly plan available.</p>;
    }

    // Display only up to 4 weeks in the card for space considerations
    const displayWeeks = weeklyPlanData.weekly_plans.slice(0, 4);

    return (
      <>
        {displayWeeks.map((plan, index) => {
          const [exercisePart, nutritionPart] = plan.split("| Nutrition:");

          return (
            <div key={index} className="mb-3 pb-3 border-b border-gray-700">
              <p className="text-sm font-semibold text-indigo-300">
                Week {index + 1}
              </p>
              <p className="text-sm">
                <strong>Exercises:</strong>{" "}
                {exercisePart.replace(/Week \d+: /, "")}
              </p>
              {nutritionPart && (
                <p className="text-sm">
                  <strong>Nutrition:</strong> {nutritionPart}
                </p>
              )}
            </div>
          );
        })}
        <p className="text-sm mt-3">
          <strong>No. of Weeks to Recover:</strong>{" "}
          {weeklyPlanData.weekly_plans.length} Weeks
        </p>
      </>
    );
  };

  // Function to generate circular progress with gradient and attractive styles
  const CircleProgressWithGradient = ({ progress }: { progress: number }) => {
    const radius = 40;
    const stroke = 10;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (progress / 100) * circumference;

    return (
      <svg className="w-32 h-32" viewBox="0 0 120 120">
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop
              offset="0%"
              style={{ stopColor: "#4CAF50", stopOpacity: 1 }}
            />
            <stop
              offset="100%"
              style={{ stopColor: "#FFEB3B", stopOpacity: 1 }}
            />
          </linearGradient>
        </defs>
        <circle
          cx="60"
          cy="60"
          r={radius}
          stroke="rgba(255, 255, 255, 0.2)"
          strokeWidth={stroke}
          fill="none"
          className="transition-all duration-500 ease-out shadow-md"
        />
        <circle
          cx="60"
          cy="60"
          r={radius}
          stroke="url(#grad1)" // Applying the gradient
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500 ease-out transform hover:scale-110 hover:rotate-6"
        />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          stroke="white"
          strokeWidth="1px"
          dy=".3em"
          className="text-2xl font-extrabold tracking-tight"
        >
          {progress}%
        </text>
      </svg>
    );
  };

  return (
    <>
      <div className="flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <div className="flex-1 container mx-auto px-4 py-8">
          <h1 className="text-4xl text-center font-semibold text-white mb-8 tracking-tight">
            Welcome to Smart Rehab System
          </h1>

          {/* Cards Layout */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 justify-center">
            {/* Card 1: Patient Info */}
            <div className="bg-slate-800 text-white p-4 rounded-lg shadow-xl hover:bg-slate-700 transition-transform duration-300 transform hover:scale-105 text-left">
              <h2 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight">
                Patient Info
              </h2>
              <div className="space-y-2">
                <p className="text-sm">
                  <strong>Name:</strong> {userData?.name ?? "N/A"}
                </p>
                <p className="text-sm">
                  <strong>Email:</strong> {userData?.email ?? "N/A"}
                </p>
                <p className="text-sm">
                  <strong>Sex:</strong> {userData?.sex ?? "N/A"}
                </p>
                <p className="text-sm">
                  <strong>Hypertension:</strong>{" "}
                  {userData?.hypertension ?? "N/A"}
                </p>{" "}
                <p className="text-sm">
                  <strong>Diabetes:</strong> {userData?.diabetes ?? "N/A"}
                </p>
                <p className="text-sm">
                  <strong>Mobility:</strong> {userData?.pain_category ?? "N/A"}
                </p>
                <p className="text-sm">
                  <strong>BMI:</strong> {userData?.bmi ?? "N/A"}
                </p>
                <p className="text-sm">
                  <strong>Weight:</strong>{" "}
                  {userData?.age ? userData.age * 0.9 : "N/A"} kg
                </p>
                <p className="text-sm">
                  <strong>Height:</strong> {userData?.height ?? "N/A"} cm
                </p>
              </div>
            </div>

            {/* Card 2: Recovery Plan */}
            <div className="bg-slate-800 text-white p-4 rounded-lg shadow-xl hover:bg-slate-700 transition-transform duration-300 transform hover:scale-105 text-left">
              <h2 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight">
                Recovery Plan
              </h2>
              <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                {renderWeeklyPlan()}
              </div>
            </div>

            {/* Card 3: Exercise Form Score */}
            <div className="bg-slate-800 text-white p-4 rounded-lg shadow-xl hover:bg-slate-700 transition-transform duration-300 transform hover:scale-105 text-left">
              <h2 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight">
                Form Accuracy
              </h2>
              {report ? (
                <div className="flex flex-col items-center">
                  <CircleProgressWithGradient
                    progress={
                      report.total_duration > 0
                        ? Math.round(
                            (report.good_form_duration /
                              report.total_duration) *
                              100
                          )
                        : 0
                    }
                  />
                  <p className="mt-4 text-sm text-center text-gray-300">
                    Good form maintained for{" "}
                    <strong>{report.good_form_duration.toFixed(1)}s</strong> out
                    of <strong>{report.total_duration.toFixed(1)}s</strong>
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-400">Loading report...</p>
              )}
            </div>

            {/* Card 4: Top Errors Feedback */}
            <div className="bg-slate-800 text-white p-4 rounded-lg shadow-xl hover:bg-slate-700 transition-transform duration-300 transform hover:scale-105 text-left">
              <h2 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight">
                Form Feedback
              </h2>
              {report && report.errors && report.errors.length > 0 ? (
                <ul className="space-y-3 max-h-56 overflow-y-auto pr-1">
                  {report.errors
                    .sort((a, b) => b.percent - a.percent)
                    .map((error, index) => (
                      <li
                        key={index}
                        className="text-sm border-l-4 border-red-500 pl-2"
                      >
                        <strong>{error.message}</strong> —{" "}
                        {error.duration.toFixed(1)}s ({error.percent.toFixed(1)}
                        %)
                      </li>
                    ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-400">No feedback available.</p>
              )}
            </div>

            {/* Card 5: Session Summary */}
            <div className="bg-slate-800 text-white p-4 rounded-lg shadow-xl hover:bg-slate-700 transition-transform duration-300 transform hover:scale-105 text-left">
              <h2 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight">
                Session Summary
              </h2>
              {report ? (
                <div className="space-y-2 text-sm">
                  <p>
                    <strong>Exercise:</strong> {report.exercise}
                  </p>
                  <p>
                    <strong>Date:</strong>{" "}
                    {new Date(report.timestamp).toLocaleDateString()}
                  </p>
                  <p>
                    <strong>Analyzer:</strong>{" "}
                    {report.analyzer || "Default Analyzer"}
                  </p>
                  <p>
                    <strong>Total Duration:</strong>{" "}
                    {report.total_duration.toFixed(1)}s
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-400">No session data yet.</p>
              )}
            </div>
          </div>

          {/* ── Appointments & Consultations Section ── */}
          <div className="mt-12 mb-10">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">📅</span> Appointments & Consultations
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Column: Book Appointment Form */}
              <div className="bg-slate-800 text-white p-6 rounded-2xl border border-slate-700/60 shadow-xl hover:bg-slate-800/90 transition-all text-left">
                <h3 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight flex items-center gap-2">
                  <span>📝</span> Book a Session
                </h3>
                
                <form onSubmit={handleBookAppointment} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                      Select Clinician / Doctor
                    </label>
                    {doctorsList.length === 0 ? (
                      <p className="text-sm text-gray-500 italic">No clinicians currently active.</p>
                    ) : (
                      <select
                        value={selectedDoctorUsername}
                        onChange={(e) => setSelectedDoctorUsername(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-750 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
                        required
                      >
                        {doctorsList.map((doc) => (
                          <option key={doc.username} value={doc.username}>
                            {doc.name || doc.username} (@{doc.username})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                        Preferred Date
                      </label>
                      <input
                        type="date"
                        value={appointmentDate}
                        onChange={(e) => setAppointmentDate(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-750 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                        Preferred Time
                      </label>
                      <input
                        type="time"
                        value={appointmentTime}
                        onChange={(e) => setAppointmentTime(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-750 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                      Reason for Session
                    </label>
                    <textarea
                      value={appointmentReason}
                      onChange={(e) => setAppointmentReason(e.target.value)}
                      placeholder="E.g., chronic knee pain during squats, request weekly recovery plan review..."
                      className="w-full bg-slate-900 border border-slate-750 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition h-20 resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={bookingLoading || doctorsList.length === 0}
                    className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl py-3 font-semibold text-sm transition-all duration-200"
                  >
                    {bookingLoading ? "Booking..." : "Submit Booking Request"}
                  </button>

                  {bookingMessage && (
                    <p className={`text-xs mt-2 text-center font-medium ${bookingMessage.includes("successfully") ? "text-green-400" : "text-yellow-400"}`}>
                      {bookingMessage}
                    </p>
                  )}
                </form>
              </div>

              {/* Right Column: Appointment Status Logs */}
              <div className="bg-slate-800 text-white p-6 rounded-2xl border border-slate-700/60 shadow-xl flex flex-col text-left">
                <h3 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight flex items-center gap-2">
                  <span>🗓️</span> My Appointments
                </h3>

                <div className="flex-1 overflow-y-auto max-h-[320px] space-y-3 pr-1">
                  {appointmentsLoading ? (
                    <p className="text-sm text-gray-500 animate-pulse">Loading appointments...</p>
                  ) : appointmentsList.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-gray-500 py-10">
                      <p className="text-sm">No appointments booked yet.</p>
                      <p className="text-xs text-gray-600 mt-1">Submit the form on the left to request a session.</p>
                    </div>
                  ) : (
                    appointmentsList.map((appt) => (
                      <div
                        key={appt._id}
                        className="bg-slate-900/60 border border-slate-750 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:border-slate-700 transition"
                      >
                        <div className="space-y-1">
                          <p className="font-semibold text-sm text-white">
                            {appt.doctor_name || appt.doctor_username}
                          </p>
                          <p className="text-xs text-gray-400">
                            📅 {appt.date} at 🕒 {appt.time}
                          </p>
                          {appt.reason && (
                            <p className="text-xs text-gray-500 italic mt-1 line-clamp-1">
                              "{appt.reason}"
                            </p>
                          )}
                        </div>

                        <div className="shrink-0 flex items-center">
                          {appt.status === "Approved" ? (
                            <span className="bg-green-500/10 text-green-400 border border-green-500/30 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                              Approved
                            </span>
                          ) : appt.status === "Rejected" ? (
                            <span className="bg-red-500/10 text-red-400 border border-red-500/30 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                              Rejected
                            </span>
                          ) : (
                            <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                              Pending
                            </span>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ── My Progress Section ── */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">📈</span> My Progress
            </h2>

            {progressLoading ? (
              <p className="text-gray-500 text-sm animate-pulse">Loading your progress…</p>
            ) : myReports.length === 0 ? (
              <div className="bg-slate-800 rounded-xl p-6 text-center text-gray-500 text-sm">
                No exercise sessions recorded yet. Complete a therapy session to see your progress!
              </div>
            ) : (
              <div className="space-y-6">
                {/* Summary Pills */}
                <div className="flex flex-wrap gap-4">
                  {[
                    { label: "Total Sessions", value: myReports.length },
                    { label: "Total Reps", value: myReports.reduce((s, r) => s + r.rep_count, 0) },
                    { label: "Exercises Done", value: new Set(myReports.map(r => r.exercise_type)).size },
                    { label: "Latest", value: myReports[0] ? new Date(myReports[0].timestamp).toLocaleDateString() : "—" },
                  ].map((item) => (
                    <div key={item.label} className="bg-indigo-600/20 border border-indigo-500/30 rounded-xl px-5 py-3">
                      <p className="text-xs text-indigo-300 mb-1">{item.label}</p>
                      <p className="text-lg font-bold text-white">{item.value}</p>
                    </div>
                  ))}
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-slate-800 rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-indigo-300 mb-4">Reps Per Session</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={progressChartData}>
                        <defs>
                          <linearGradient id="colorReps" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#818cf8" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                        <XAxis dataKey="session" stroke="#6b7280" tick={{ fontSize: 11 }} />
                        <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ background: "#1e293b", border: "1px solid #374151", borderRadius: 8 }}
                          labelStyle={{ color: "#e5e7eb" }}
                        />
                        <Area
                          type="monotone"
                          dataKey="reps"
                          stroke="#818cf8"
                          fillOpacity={1}
                          fill="url(#colorReps)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="bg-slate-800 rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-indigo-300 mb-4">Reps by Exercise Type</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={breakdownChartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="totalReps"
                          nameKey="exercise"
                        >
                          {breakdownChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: "#1e293b", border: "1px solid #374151", borderRadius: 8 }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Session History */}
                <div className="bg-slate-800 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-indigo-300 mb-4">Session History</h3>
                  <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                    {myReports.map((r, i) => (
                      <div
                        key={i}
                        className="bg-slate-700/60 border border-slate-600 rounded-lg px-4 py-3 hover:border-indigo-500/50 transition"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-indigo-300 text-sm">{r.exercise_type}</span>
                          <span className="text-xs text-gray-500">{new Date(r.timestamp).toLocaleString()}</span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-400">
                          <span><strong className="text-white">{r.rep_count}</strong> reps</span>
                          {r.errors?.length > 0 && (
                            <span className="text-yellow-400 text-xs">⚠ {r.errors.length} form issue{r.errors.length !== 1 ? 's' : ''}</span>
                          )}
                        </div>
                        {r.raw_report && (
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300">View AI Report</summary>
                            <pre className="text-xs text-gray-400 mt-2 whitespace-pre-wrap bg-black/30 rounded p-2">{r.raw_report}</pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;

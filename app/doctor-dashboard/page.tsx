"use client";

import React, { useState, useEffect, useRef } from "react";
import { Sidebar } from "../sidebar/sidebar";
import { useUser } from "@/contexts/AppContext";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from "recharts";

interface Patient {
  username: string;
  name?: string;
  email?: string;
  role: string;
  age?: number;
  bmi?: number;
  height?: number;
  sex?: string;
  hypertension?: string;
  diabetes?: string;
  pain_category?: string;
  last_exercise?: ExerciseReport | null;
}

interface ExerciseReport {
  username: string;
  exercise_type: string;
  rep_count: number;
  errors: string[];
  raw_report?: string;
  timestamp: string;
}

export default function DoctorDashboard() {
  const { username } = useUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientReports, setPatientReports] = useState<ExerciseReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const [activeTab, setActiveTab] = useState<"analytics" | "chat" | "appointments">("analytics");
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatInputText, setChatInputText] = useState("");
  const [chatSending, setChatSending] = useState(false);
  const chatMessagesEndRef = useRef<HTMLDivElement>(null);

  // Doctor appointment states
  const [appointmentsList, setAppointmentsList] = useState<any[]>([]);
  const [appointmentsLoading, setAppointmentsLoading] = useState(false);
  const [showGlobalAppointments, setShowGlobalAppointments] = useState(true);

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    if (username) {
      fetchDoctorAppointments();
    }
  }, [username]);

  const fetchDoctorAppointments = async () => {
    if (!username) return;
    setAppointmentsLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/appointments/doctor/${username}`);
      const data = await res.json();
      if (data.success) {
        setAppointmentsList(data.appointments);
      }
    } catch (err) {
      console.error("Failed to fetch appointments:", err);
    } finally {
      setAppointmentsLoading(false);
    }
  };

  const handleUpdateAppointmentStatus = async (appointmentId: string, status: "Approved" | "Rejected") => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/appointments/update_status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          appointment_id: appointmentId,
          status: status,
        }),
      });
      const data = await res.json();
      if (data.success) {
        fetchDoctorAppointments();
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const fetchPatients = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/doctor/patients");
      const data = await res.json();
      if (data.success) setPatients(data.patients);
    } catch (err) {
      console.error("Failed to fetch patients:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientReports = async (patientUsername: string) => {
    setReportsLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/patient/reports/${patientUsername}`
      );
      const data = await res.json();
      if (data.success) setPatientReports(data.reports);
    } catch (err) {
      console.error("Failed to fetch patient reports:", err);
    } finally {
      setReportsLoading(false);
    }
  };

  const fetchChatMessages = async () => {
    if (!username || !selectedPatient) return;
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/messages?user1=${username}&user2=${selectedPatient.username}`
      );
      const data = await res.json();
      if (data.success) setChatMessages(data.messages);
    } catch (err) {
      console.error("Failed to fetch chat messages:", err);
    }
  };

  useEffect(() => {
    if (activeTab !== "chat" || !selectedPatient || !username) return;
    fetchChatMessages();
    const interval = setInterval(fetchChatMessages, 3000);
    return () => clearInterval(interval);
  }, [activeTab, selectedPatient, username]);

  useEffect(() => {
    if (activeTab === "chat") {
      chatMessagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, activeTab]);

  const handleSendChatMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInputText.trim() || !username || !selectedPatient || chatSending) return;

    setChatSending(true);
    const newMessage = {
      sender: username,
      receiver: selectedPatient.username,
      content: chatInputText,
      timestamp: new Date().toISOString(),
    };

    try {
      const res = await fetch("http://127.0.0.1:8000/api/messages/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newMessage),
      });
      const data = await res.json();
      if (data.success) {
        setChatMessages((prev) => [...prev, newMessage]);
        setChatInputText("");
      }
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setChatSending(false);
    }
  };

  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    setShowGlobalAppointments(false);
    setActiveTab("analytics");
    setChatMessages([]);
    setChatInputText("");
    fetchPatientReports(patient.username);
  };

  const handleSelectGlobalAppointments = () => {
    setSelectedPatient(null);
    setShowGlobalAppointments(true);
  };

  // Build chart data from reports
  const chartData = [...patientReports]
    .reverse()
    .map((r, i) => ({
      session: `S${i + 1}`,
      reps: r.rep_count,
      exercise: r.exercise_type,
      date: new Date(r.timestamp).toLocaleDateString(),
    }));

  const exerciseBreakdown = patientReports.reduce<Record<string, number>>(
    (acc, r) => {
      acc[r.exercise_type] = (acc[r.exercise_type] || 0) + r.rep_count;
      return acc;
    },
    {}
  );
  const breakdownData = Object.entries(exerciseBreakdown).map(([k, v]) => ({
    exercise: k,
    totalReps: v,
  }));

  const filteredPatients = patients.filter(
    (p) =>
      p.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.name ?? "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex min-h-screen bg-[#0b0f1a] text-white">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="flex-1 p-6 overflow-y-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              Doctor Dashboard
            </h1>
            <p className="text-gray-400 mt-1 text-sm">
              Logged in as <span className="text-indigo-300 font-medium">{username}</span>
            </p>
          </div>
          <div className="flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full px-4 py-2">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-sm text-indigo-300">Doctor Portal</span>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Patient List Panel */}
          <div className="w-72 shrink-0 flex flex-col gap-4">
            <div>
              <input
                id="doctor-search"
                type="text"
                placeholder="Search patients…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-gray-800/60 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
              />
            </div>

            {/* Global Appointment Inbox Button */}
            <button
              onClick={handleSelectGlobalAppointments}
              className={`w-full text-left px-4 py-3.5 rounded-xl border transition-all duration-200 flex items-center justify-between ${
                showGlobalAppointments
                  ? "bg-indigo-600/30 border-indigo-500 text-indigo-100 shadow-[0_0_15px_rgba(99,102,241,0.15)]"
                  : "bg-gray-800/40 border-gray-700 hover:border-indigo-500/60 hover:bg-gray-800/70 text-gray-300"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">📥</span>
                <div>
                  <p className="font-semibold text-sm">Centralized Inbox</p>
                  <p className="text-[10px] text-gray-500">All requested sessions</p>
                </div>
              </div>
              {appointmentsList.filter((a) => a.status === "Pending").length > 0 && (
                <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full animate-pulse">
                  {appointmentsList.filter((a) => a.status === "Pending").length} New
                </span>
              )}
            </button>

            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
              {filteredPatients.length} patient{filteredPatients.length !== 1 ? "s" : ""}
            </div>

            {loading ? (
              <div className="text-gray-500 text-sm animate-pulse">Loading patients…</div>
            ) : filteredPatients.length === 0 ? (
              <div className="text-gray-500 text-sm">No patients found.</div>
            ) : (
              <div className="flex flex-col gap-2 overflow-y-auto max-h-[calc(100vh-200px)] pr-1">
                {filteredPatients.map((p) => (
                  <button
                    key={p.username}
                    id={`patient-btn-${p.username}`}
                    onClick={() => handleSelectPatient(p)}
                    className={`text-left px-4 py-3 rounded-xl border transition-all duration-200 ${
                      selectedPatient?.username === p.username
                        ? "bg-indigo-600/30 border-indigo-500 text-indigo-100"
                        : "bg-gray-800/40 border-gray-700 hover:border-indigo-500/60 hover:bg-gray-800/70"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
                        {(p.name ?? p.username).charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{p.name ?? p.username}</p>
                        <p className="text-xs text-gray-500">@{p.username}</p>
                      </div>
                    </div>
                    {p.last_exercise && (
                      <p className="text-xs text-gray-500 mt-2 pl-12">
                        Last: {p.last_exercise.exercise_type}
                      </p>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Patient Detail Panel / Centralized Inbox */}
          <div className="flex-1">
            {showGlobalAppointments ? (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 flex flex-col min-h-[500px] text-left">
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-800">
                    <div>
                      <h2 className="text-2xl font-extrabold text-indigo-400 tracking-tight flex items-center gap-2.5">
                        <span>📥</span> Centralized Appointment Requests
                      </h2>
                      <p className="text-xs text-gray-500 mt-1">
                        Review and manage all consultation requests received from patients
                      </p>
                    </div>
                    <div className="bg-indigo-500/10 border border-indigo-500/20 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-indigo-300">
                      {appointmentsList.length} total request{appointmentsList.length !== 1 ? "s" : ""}
                    </div>
                  </div>

                  {appointmentsLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-500 gap-3">
                      <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
                      <p className="text-sm">Fetching clinician inbox...</p>
                    </div>
                  ) : appointmentsList.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center text-gray-500 bg-gray-800/20 rounded-2xl border border-gray-800/40">
                      <span className="text-5xl mb-4">📭</span>
                      <p className="font-semibold text-base text-gray-400">Your inbox is completely clear!</p>
                      <p className="text-xs text-gray-500 mt-1">No appointment requests have been booked yet.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Priority Pending Requests Section */}
                      {appointmentsList.filter(a => a.status === "Pending").length > 0 && (
                        <div className="space-y-3">
                          <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest pl-1">
                            🟡 Pending Action ({appointmentsList.filter(a => a.status === "Pending").length})
                          </h3>
                          <div className="grid grid-cols-1 gap-4">
                            {appointmentsList
                              .filter((appt) => appt.status === "Pending")
                              .map((appt) => {
                                const pt = patients.find(p => p.username === appt.patient_username);
                                const displayName = pt?.name || appt.patient_username;
                                return (
                                  <div
                                    key={appt._id}
                                    className="bg-gradient-to-r from-gray-800/40 to-gray-800/25 border-l-4 border-l-amber-500 border-y border-r border-gray-700/60 rounded-r-xl rounded-l p-5 flex flex-col md:flex-row md:items-center justify-between gap-5 hover:border-gray-600 transition"
                                  >
                                    <div className="flex items-start gap-4">
                                      <button
                                        onClick={() => {
                                          if (pt) handleSelectPatient(pt);
                                        }}
                                        className="w-11 h-11 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white font-bold text-base shrink-0 hover:scale-105 transition"
                                        title="View Patient Progress"
                                      >
                                        {displayName.charAt(0).toUpperCase()}
                                      </button>
                                      <div className="space-y-1 text-left">
                                        <div className="flex items-center gap-2.5 flex-wrap">
                                          <button
                                            onClick={() => {
                                              if (pt) handleSelectPatient(pt);
                                            }}
                                            className="font-bold text-sm text-white hover:text-indigo-400 transition"
                                          >
                                            {displayName}
                                          </button>
                                          <span className="text-xs text-gray-500">@{appt.patient_username}</span>
                                        </div>
                                        <div className="flex items-center gap-3 text-xs text-gray-300 mt-1">
                                          <span>📅 {appt.date}</span>
                                          <span className="text-indigo-400">🕒 {appt.time}</span>
                                        </div>
                                        {appt.reason && (
                                          <p className="text-xs text-gray-400 mt-2 bg-black/25 rounded-lg p-2.5 italic border border-gray-800/40 max-w-xl">
                                            "{appt.reason}"
                                          </p>
                                        )}
                                      </div>
                                    </div>

                                    <div className="shrink-0 flex items-center gap-2 mt-2 md:mt-0">
                                      <button
                                        onClick={() => handleUpdateAppointmentStatus(appt._id, "Approved")}
                                        className="bg-green-600 hover:bg-green-500 text-white rounded-lg px-4 py-2 font-bold text-xs shadow-md transition"
                                      >
                                        Approve
                                      </button>
                                      <button
                                        onClick={() => handleUpdateAppointmentStatus(appt._id, "Rejected")}
                                        className="bg-red-600/90 hover:bg-red-500 text-white rounded-lg px-4 py-2 font-bold text-xs shadow-md transition"
                                      >
                                        Reject
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                        </div>
                      </div>
                    )}

                      {/* Log / History Section */}
                      <div className="space-y-3 pt-4">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest pl-1">
                          📋 Handled / Past Requests
                        </h3>
                        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                          {appointmentsList.filter(a => a.status !== "Pending").length === 0 ? (
                            <div className="text-center py-6 text-xs text-gray-500 bg-gray-800/10 rounded-xl border border-gray-800/40">
                              No previously handled appointment requests.
                            </div>
                          ) : (
                            appointmentsList
                              .filter((appt) => appt.status !== "Pending")
                              .map((appt) => {
                                const pt = patients.find(p => p.username === appt.patient_username);
                                const displayName = pt?.name || appt.patient_username;
                                return (
                                  <div
                                    key={appt._id}
                                    className="bg-gray-800/20 border border-gray-800/60 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-gray-800 transition"
                                  >
                                    <div className="flex items-center gap-3.5 text-left">
                                      <button
                                        onClick={() => {
                                          if (pt) handleSelectPatient(pt);
                                        }}
                                        className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-gray-300 font-semibold text-xs shrink-0 hover:bg-indigo-600/30 hover:text-indigo-300 transition"
                                        title="View Patient Progress"
                                      >
                                        {displayName.charAt(0).toUpperCase()}
                                      </button>
                                      <div>
                                        <div className="flex items-center gap-2">
                                          <button
                                            onClick={() => {
                                              if (pt) handleSelectPatient(pt);
                                            }}
                                            className="font-semibold text-xs text-white hover:text-indigo-400 transition"
                                          >
                                            {displayName}
                                          </button>
                                          <span className="text-[10px] text-gray-500">@{appt.patient_username}</span>
                                        </div>
                                        <div className="flex items-center gap-2.5 text-[10px] text-gray-400 mt-0.5">
                                          <span>📅 {appt.date}</span>
                                          <span>🕒 {appt.time}</span>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="shrink-0">
                                      {appt.status === "Approved" ? (
                                        <span className="bg-green-500/10 text-green-400 border border-green-500/20 text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1">
                                          <span className="w-1 h-1 rounded-full bg-green-400" />
                                          Approved
                                        </span>
                                      ) : (
                                        <span className="bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1">
                                          <span className="w-1 h-1 rounded-full bg-red-400" />
                                          Rejected
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                );
                              })
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : !selectedPatient ? (
              <div className="flex flex-col items-center justify-center h-[60vh] text-center text-gray-600">
                <div className="text-6xl mb-4">🩺</div>
                <p className="text-lg font-semibold text-gray-500">Select a patient</p>
                <p className="text-sm text-gray-600 mt-1">
                  Click on a patient in the list to view their progress
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Patient Profile Card */}
                <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6">
                  <div className="flex items-center gap-4 mb-5">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-2xl font-bold">
                      {(selectedPatient.name ?? selectedPatient.username).charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h2 className="text-xl font-bold">{selectedPatient.name ?? selectedPatient.username}</h2>
                      <p className="text-gray-400 text-sm">@{selectedPatient.username}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: "Age", value: selectedPatient.age ?? "—" },
                      { label: "BMI", value: selectedPatient.bmi ?? "—" },
                      { label: "Sex", value: selectedPatient.sex ?? "—" },
                      { label: "Height", value: selectedPatient.height ? `${selectedPatient.height} cm` : "—" },
                      { label: "Hypertension", value: selectedPatient.hypertension ?? "—" },
                      { label: "Diabetes", value: selectedPatient.diabetes ?? "—" },
                      { label: "Mobility", value: selectedPatient.pain_category ?? "—" },
                      { label: "Total Sessions", value: patientReports.length },
                    ].map((item) => (
                      <div key={item.label} className="bg-gray-800/50 rounded-xl p-3">
                        <p className="text-xs text-gray-500 mb-1">{item.label}</p>
                        <p className="font-semibold text-sm">{item.value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Segmented Control Tabs */}
                <div className="flex gap-4 border-b border-gray-800 pb-px">
                  <button
                    onClick={() => setActiveTab("analytics")}
                    className={`pb-3 font-semibold text-sm transition-all border-b-2 px-1 ${
                      activeTab === "analytics"
                        ? "border-indigo-500 text-indigo-400"
                        : "border-transparent text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    📈 Recovery Progress & History
                  </button>
                  <button
                    onClick={() => setActiveTab("chat")}
                    className={`pb-3 font-semibold text-sm transition-all border-b-2 px-1 ${
                      activeTab === "chat"
                        ? "border-indigo-500 text-indigo-400"
                        : "border-transparent text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    💬 Direct Chat with Patient
                  </button>
                  <button
                    onClick={() => setActiveTab("appointments")}
                    className={`pb-3 font-semibold text-sm transition-all border-b-2 px-1 ${
                      activeTab === "appointments"
                        ? "border-indigo-500 text-indigo-400"
                        : "border-transparent text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    📅 Appointment Requests
                  </button>
                </div>

                {activeTab === "analytics" && (
                  <>
                    {reportsLoading ? (
                      <div className="text-gray-500 text-sm animate-pulse">Loading reports…</div>
                    ) : patientReports.length === 0 ? (
                      <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 text-center text-gray-500 text-sm">
                        No exercise sessions recorded yet for this patient.
                      </div>
                    ) : (
                      <>
                        {/* Progress Charts */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-5">
                            <h3 className="text-sm font-semibold text-gray-300 mb-4">
                              Reps Per Session
                            </h3>
                            <ResponsiveContainer width="100%" height={220}>
                              <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                                <XAxis dataKey="session" stroke="#6b7280" tick={{ fontSize: 11 }} />
                                <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                                <Tooltip
                                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                                  labelStyle={{ color: "#e5e7eb" }}
                                />
                                <Line
                                  type="monotone"
                                  dataKey="reps"
                                  stroke="#6366f1"
                                  strokeWidth={2.5}
                                  dot={{ r: 4, fill: "#6366f1" }}
                                  activeDot={{ r: 6 }}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>

                          <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-5">
                            <h3 className="text-sm font-semibold text-gray-300 mb-4">
                              Total Reps by Exercise
                            </h3>
                            <ResponsiveContainer width="100%" height={220}>
                              <BarChart data={breakdownData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                                <XAxis dataKey="exercise" stroke="#6b7280" tick={{ fontSize: 11 }} />
                                <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                                <Tooltip
                                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                                />
                                <Bar dataKey="totalReps" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Session History Log */}
                        <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-5">
                          <h3 className="text-sm font-semibold text-gray-300 mb-4">
                            Exercise History Log
                          </h3>
                          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                            {patientReports.map((r, i) => (
                              <div
                                key={i}
                                className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 hover:border-indigo-500/50 transition"
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-semibold text-indigo-300 text-sm">
                                    {r.exercise_type}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {new Date(r.timestamp).toLocaleString()}
                                  </span>
                                </div>
                                <div className="flex items-center gap-4 text-sm text-gray-400">
                                  <span>
                                    <strong className="text-white">{r.rep_count}</strong> reps
                                  </span>
                                  {r.errors?.length > 0 && (
                                    <span className="text-yellow-500 text-xs">
                                      ⚠ {r.errors.length} form issue{r.errors.length !== 1 ? "s" : ""}
                                    </span>
                                  )}
                                </div>
                                {r.raw_report && (
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300">
                                      View AI Report
                                    </summary>
                                    <pre className="text-xs text-gray-400 mt-2 whitespace-pre-wrap bg-black/30 rounded p-2">
                                      {r.raw_report}
                                    </pre>
                                  </details>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </>
                )}

                {activeTab === "chat" && (
                  <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 flex flex-col h-[550px] overflow-hidden">
                    {/* Chat Messages */}
                    <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
                      {chatMessages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center text-gray-500">
                          <div className="text-4xl mb-2">💬</div>
                          <p className="font-medium text-gray-400">No message history</p>
                          <p className="text-xs text-gray-500 max-w-xs mt-1">
                            Start the conversation by sending a direct message below.
                          </p>
                        </div>
                      ) : (
                        chatMessages.map((msg, index) => {
                          const isMe = msg.sender === username;
                          return (
                            <div
                              key={index}
                              className={`flex ${isMe ? "justify-end" : "justify-start"}`}
                            >
                              <div className={`max-w-[70%] rounded-2xl px-4 py-2.5 shadow ${
                                isMe
                                  ? "bg-indigo-600 text-white rounded-br-none"
                                  : "bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700/60"
                              }`}>
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                <p className="text-[10px] opacity-60 text-right mt-1">
                                  {new Date(msg.timestamp).toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })}
                                </p>
                              </div>
                            </div>
                          );
                        })
                      )}
                      <div ref={chatMessagesEndRef} />
                    </div>

                    {/* Chat Input Form */}
                    <form onSubmit={handleSendChatMessage} className="flex gap-2 items-center border-t border-gray-800 pt-4 mt-auto">
                      <input
                        type="text"
                        value={chatInputText}
                        onChange={(e) => setChatInputText(e.target.value)}
                        placeholder={`Reply to ${selectedPatient.name || selectedPatient.username}…`}
                        className="flex-1 bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
                      />
                      <button
                        type="submit"
                        disabled={!chatInputText.trim() || chatSending}
                        className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl px-5 py-3 font-semibold text-sm transition shrink-0"
                      >
                        {chatSending ? "Sending…" : "Send"}
                      </button>
                    </form>
                  </div>
                )}

                {activeTab === "appointments" && (
                  <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 flex flex-col min-h-[400px] text-left">
                    <h3 className="text-xl font-bold text-indigo-400 mb-4 tracking-tight flex items-center gap-2">
                      <span>🗓️</span> Appointment Requests
                    </h3>
                    
                    {appointmentsLoading ? (
                      <p className="text-sm text-gray-500 animate-pulse">Loading appointments...</p>
                    ) : (
                      <div className="space-y-4">
                        {appointmentsList.filter(appt => appt.patient_username === selectedPatient.username).length === 0 ? (
                          <div className="text-center py-12 text-gray-500 bg-gray-800/30 rounded-xl border border-gray-800/60">
                            <p className="text-sm">No appointment requests from this patient.</p>
                          </div>
                        ) : (
                          appointmentsList
                            .filter(appt => appt.patient_username === selectedPatient.username)
                            .map((appt) => (
                              <div
                                key={appt._id}
                                className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 hover:border-gray-600 transition"
                              >
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-sm text-white">📅 {appt.date}</span>
                                    <span className="text-xs text-indigo-400">🕒 {appt.time}</span>
                                  </div>
                                  {appt.reason && (
                                    <p className="text-xs text-gray-400 mt-1.5 bg-black/20 rounded p-2.5 italic">
                                      "{appt.reason}"
                                    </p>
                                  )}
                                  <p className="text-[10px] text-gray-500">
                                    Requested: {new Date(appt.timestamp).toLocaleString()}
                                  </p>
                                </div>

                                <div className="shrink-0 flex items-center gap-2">
                                  {appt.status === "Pending" ? (
                                    <div className="flex items-center gap-2">
                                      <button
                                        onClick={() => handleUpdateAppointmentStatus(appt._id, "Approved")}
                                        className="bg-green-600 hover:bg-green-500 text-white rounded-lg px-4 py-2 font-semibold text-xs transition"
                                      >
                                        Approve
                                      </button>
                                      <button
                                        onClick={() => handleUpdateAppointmentStatus(appt._id, "Rejected")}
                                        className="bg-red-600 hover:bg-red-500 text-white rounded-lg px-4 py-2 font-semibold text-xs transition"
                                      >
                                        Reject
                                      </button>
                                    </div>
                                  ) : appt.status === "Approved" ? (
                                    <span className="bg-green-500/10 text-green-400 border border-green-500/30 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                                      Approved
                                    </span>
                                  ) : (
                                    <span className="bg-red-500/10 text-red-400 border border-red-500/30 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                                      <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                                      Rejected
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

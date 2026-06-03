"use client";

import React, { useState, useEffect, useRef } from "react";
import { Sidebar } from "../sidebar/sidebar";
import { useUser } from "@/contexts/AppContext";
import {
  SendOutlined,
  UserOutlined,
  MessageOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";

interface Doctor {
  username: string;
  name?: string;
  email?: string;
  role: string;
}

interface Message {
  sender: string;
  receiver: string;
  content: string;
  timestamp: string;
  is_read?: boolean;
}

export default function AskDoctor() {
  const { username } = useUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Default system/demo doctors in case DB is empty
  const defaultDoctors: Doctor[] = [
    {
      username: "dr_smith",
      name: "Dr. Elizabeth Smith",
      email: "smith@smartrehab.com",
      role: "Doctor",
    },
    {
      username: "dr_alex",
      name: "Dr. Alex Carter (Rehab AI)",
      email: "alex@smartrehab.com",
      role: "Doctor",
    },
  ];

  // Fetch doctors on mount
  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/doctors");
        const data = await res.json();
        if (data.success && data.doctors && data.doctors.length > 0) {
          setDoctors(data.doctors);
          setSelectedDoctor(data.doctors[0]);
        } else {
          // Fallback to default demo doctors
          setDoctors(defaultDoctors);
          setSelectedDoctor(defaultDoctors[0]);
        }
      } catch (err) {
        console.error("Failed to fetch doctors, using defaults:", err);
        setDoctors(defaultDoctors);
        setSelectedDoctor(defaultDoctors[0]);
      } finally {
        setLoading(false);
      }
    };
    fetchDoctors();
  }, []);

  // Fetch messages between patient and selected doctor
  const fetchMessages = async () => {
    if (!username || !selectedDoctor) return;
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/messages?user1=${username}&user2=${selectedDoctor.username}`
      );
      const data = await res.json();
      if (data.success) {
        setMessages(data.messages);
      }
    } catch (err) {
      console.error("Failed to fetch messages:", err);
    }
  };

  // Set up polling interval for new messages
  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, [username, selectedDoctor]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !username || !selectedDoctor || sending) return;

    setSending(true);
    const newMessage = {
      sender: username,
      receiver: selectedDoctor.username,
      content: inputText,
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
        setMessages((prev) => [...prev, newMessage]);
        setInputText("");
      }
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-gray-200 flex overflow-hidden">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="flex-grow flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <div className="bg-slate-900 border-b border-gray-800 px-8 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-xl">
              <MessageOutlined />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Ask Doctor</h1>
              <p className="text-xs text-gray-400">Ask questions and consult recovery guidelines</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full px-4 py-1.5 text-xs text-indigo-300">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span>Consultant Active</span>
          </div>
        </div>

        {/* Main Work Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left panel: Doctor list */}
          <div className="w-80 border-r border-gray-800 bg-slate-950 p-4 flex flex-col gap-4 overflow-y-auto shrink-0">
            <h2 className="text-xs font-semibold uppercase text-gray-500 tracking-wider">
              Available Clinicians
            </h2>
            {loading ? (
              <div className="text-sm text-gray-500 animate-pulse">Loading clinicians…</div>
            ) : (
              <div className="flex flex-col gap-2">
                {doctors.map((doc) => (
                  <button
                    key={doc.username}
                    onClick={() => setSelectedDoctor(doc)}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-left transition ${
                      selectedDoctor?.username === doc.username
                        ? "bg-indigo-600/20 border-indigo-500 text-indigo-100"
                        : "bg-slate-900/40 border-gray-850 hover:border-indigo-500/40 hover:bg-slate-900/60"
                    }`}
                  >
                    <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-indigo-300 font-bold shrink-0 border border-indigo-500/20">
                      <UserOutlined />
                    </div>
                    <div className="overflow-hidden">
                      <p className="font-semibold text-sm truncate text-white">{doc.name || doc.username}</p>
                      <p className="text-xs text-indigo-300/80 truncate">@{doc.username}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right panel: Active Chat view */}
          <div className="flex-1 flex flex-col bg-slate-900/20">
            {selectedDoctor ? (
              <>
                {/* Selected Doc Header Info Bar */}
                <div className="bg-slate-900/60 border-b border-gray-850 px-6 py-3 flex items-center gap-3 shrink-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-300">
                    <UserOutlined />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-white">{selectedDoctor.name || selectedDoctor.username}</h3>
                    <p className="text-xs text-gray-400">Consultation Channel</p>
                  </div>
                </div>

                {/* Messages Box */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-gray-500">
                      <div className="text-4xl mb-2">💬</div>
                      <p className="font-medium text-gray-400">No messages yet</p>
                      <p className="text-xs text-gray-500 max-w-xs mt-1">
                        Send a message below to start consulting with {selectedDoctor.name || selectedDoctor.username}.
                      </p>
                    </div>
                  ) : (
                    messages.map((msg, index) => {
                      const isMe = msg.sender === username;
                      return (
                        <div
                          key={index}
                          className={`flex ${isMe ? "justify-end" : "justify-start"}`}
                        >
                          <div className={`max-w-[70%] rounded-2xl px-4 py-2.5 shadow ${
                            isMe
                              ? "bg-indigo-600 text-white rounded-br-none"
                              : "bg-slate-800 text-gray-200 rounded-bl-none border border-slate-700/60"
                          }`}>
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                            <div className="flex items-center justify-end gap-1.5 mt-1 text-[10px] opacity-60">
                              <span>
                                {new Date(msg.timestamp).toLocaleTimeString([], {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                              </span>
                              {isMe && <CheckCircleOutlined className="text-indigo-200" />}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input box Form */}
                <form onSubmit={handleSend} className="p-4 bg-slate-900/80 border-t border-gray-800 flex gap-2 items-center shrink-0">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder={`Message ${selectedDoctor.name || selectedDoctor.username}…`}
                    className="flex-1 bg-slate-950 border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
                  />
                  <button
                    type="submit"
                    disabled={!inputText.trim() || sending}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl p-3 flex items-center justify-center transition shrink-0"
                  >
                    <SendOutlined />
                  </button>
                </form>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-600">
                <div className="text-6xl mb-4">🩺</div>
                <p className="text-lg font-semibold text-gray-500">Select a clinician</p>
                <p className="text-sm text-gray-600 mt-1">Choose a doctor from the list to start chatting</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

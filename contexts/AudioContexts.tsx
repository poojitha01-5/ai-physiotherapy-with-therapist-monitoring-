import {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
} from "react";

interface AudioContextType {
  audiobot: "on" | "off";
  language: "en" | "ur" | "";
  setAudiobot: (value: "on" | "off") => void;
  setLanguage: (value: "en" | "ur" | "") => void;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

export const AudioProvider = ({ children }: { children: ReactNode }) => {
  const [audiobot, setAudiobotState] = useState<"on" | "off">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("audiobot") as "on" | "off" | null;
      console.log("🎯 [Init] Audiobot loaded from localStorage:", stored);
      return stored || "off";
    }
    return "off";
  });

  const [language, setLanguageState] = useState<"en" | "ur" | "">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("language") as
        | "en"
        | "ur"
        | ""
        | null;
      console.log("🎯 [Init] Language loaded from localStorage:", stored);
      return stored || "";
    }
    return "";
  });

  useEffect(() => {
    console.log("💾 [Effect] Saving audiobot to localStorage:", audiobot);
    localStorage.setItem("audiobot", audiobot);
  }, [audiobot]);

  useEffect(() => {
    console.log("💾 [Effect] Saving language to localStorage:", language);
    localStorage.setItem("language", language);
  }, [language]);

  const setAudiobot = (value: "on" | "off") => {
    console.log("🧠 [Setter] setAudiobot called with:", value);
    setAudiobotState(value);
  };

  const setLanguage = (value: "en" | "ur" | "") => {
    console.log("🧠 [Setter] setLanguage called with:", value);
    setLanguageState(value);
  };

  return (
    <AudioContext.Provider
      value={{ audiobot, language, setAudiobot, setLanguage }}
    >
      {children}
    </AudioContext.Provider>
  );
};

export const useAudio = () => {
  const context = useContext(AudioContext);
  if (!context) {
    throw new Error("useAudio must be used within an AudioProvider");
  }
  console.log("🎧 [Hook] useAudio accessed context →", context);
  return context;
};

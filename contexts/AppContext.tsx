// /contexts/AppContext.tsx
import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
} from "react";

// Define the UserContextType for context state
export interface UserContextType {
  username: string | null;
  setUsername: (username: string | null) => void;
  role: "Patient" | "Doctor" | null;
  setRole: (role: "Patient" | "Doctor" | null) => void;
}

// Create the UserContext with an undefined default value
const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [username, setUsername] = useState<string | null>(null);
  const [role, setRole] = useState<"Patient" | "Doctor" | null>(null);

  // Load the username and role from localStorage when the component mounts
  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    const storedRole = localStorage.getItem("role") as "Patient" | "Doctor" | null;
    if (storedUsername) {
      setUsername(storedUsername);
    }
    if (storedRole) {
      setRole(storedRole);
    }
  }, []);

  // Log the username whenever it changes (for debugging)
  useEffect(() => {
    console.log("Username has been updated:", username);
  }, [username]);

  return (
    <UserContext.Provider value={{ username, setUsername, role, setRole }}>
      {children}
    </UserContext.Provider>
  );
};

// Custom hook to access the UserContext
export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};

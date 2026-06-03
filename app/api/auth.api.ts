// /app/api/auth.api.ts
import { POST } from "@/utils/api.service";
import { UserContextType } from "@/contexts/AppContext"; // Ensure proper import of the context type

interface LoginResponse {
  success: boolean;
  user: {
    username: string;
    role: "Patient" | "Doctor";
  };
}

export const login = async ({
  username,
  password,
  notification,
  setUsername,
  setRole,
}: {
  username: string;
  password: string;
  notification: any;
  setUsername: UserContextType["setUsername"];
  setRole: UserContextType["setRole"];
}) => {
  try {
    // Call the API to sign in
    const response = await POST<
      LoginResponse,
      { username: string; password: string }
    >("/api/signin", {
      username,
      password,
    });

    if (response?.success) {
      const { user } = response;

      // Update the context with the username and role
      setUsername(user.username);
      setRole(user.role ?? "Patient");

      // Store in localStorage
      if (typeof window !== "undefined") {
        localStorage.setItem("username", user.username);
        localStorage.setItem("role", user.role ?? "Patient");
      }

      // Route based on role
      if (user.role === "Doctor") {
        window.location.href = "/doctor-dashboard";
      } else {
        window.location.href = "/dashboard";
      }

      return user;
    } else {
      notification?.error({
        message: "Incorrect username or password!",
      });
    }
  } catch (error) {
    notification?.error({
      message: "Login failed. Please try again.",
    });
  }
};

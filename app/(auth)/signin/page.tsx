"use client";

import { useState } from "react";
import Link from "next/link";
import { login } from "@/app/api/auth.api";
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/AppContext";

export default function SignIn() {
  const [username, setUsernameInput] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const router = useRouter();
  const { setUsername, setRole } = useUser();

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const notification = {
        error: (msg: any) => setErrorMsg(msg.message),
      };

      await login({
        username,
        password,
        notification,
        setUsername: (u: string | null) => setUsername(u),
        setRole: (r: "Patient" | "Doctor" | null) => setRole(r),
      });
    } catch (error) {
      console.error("Authentication failed:", error);
      setErrorMsg("Authentication failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="py-12 md:py-20">
          <div className="pb-12 text-center">
            <h1 className="text-3xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-gray-200 via-indigo-200 to-gray-50 md:text-4xl">
              Welcome back
            </h1>
          </div>
          <form className="mx-auto max-w-[400px]" onSubmit={handleSignIn}>
            <div className="space-y-5">
              <div>
                <label
                  className="mb-1 block text-sm font-medium text-indigo-200/65"
                  htmlFor="signin-username"
                >
                  Username
                </label>
                <input
                  id="signin-username"
                  type="text"
                  className="form-input w-full"
                  placeholder="Your username"
                  required
                  value={username}
                  onChange={(e) => setUsernameInput(e.target.value)}
                />
              </div>
              <div>
                <div className="mb-1 flex items-center justify-between gap-3">
                  <label
                    className="block text-sm font-medium text-indigo-200/65"
                    htmlFor="signin-password"
                  >
                    Password
                  </label>
                  <Link
                    className="text-sm text-white hover:underline"
                    href="/reset-password"
                  >
                    Forgot?
                  </Link>
                </div>
                <input
                  id="signin-password"
                  type="password"
                  className="form-input w-full"
                  placeholder="Your password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {errorMsg && (
              <p className="mt-4 text-center text-sm text-red-400">{errorMsg}</p>
            )}

            <div className="mt-6 space-y-5">
              <button
                id="signin-submit-btn"
                type="submit"
                disabled={isSubmitting}
                className="btn w-full bg-gradient-to-t from-slate-800 to-indigo-500 text-white disabled:opacity-60"
              >
                {isSubmitting ? "Signing in..." : "Sign In"}
              </button>
            </div>
          </form>
          <div className="mt-6 text-center text-sm text-indigo-200/65">
            Don&apos;t have an account?{" "}
            <Link className="font-medium text-indigo-500" href="/signup">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

'use client';
import { useState, ChangeEvent, FormEvent } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import Link from "next/link";

interface FormData {
  name: string;
  username: string;
  email: string;
  password: string;
  role: "Patient" | "Doctor";
}

export default function SignUp() {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    username: "",
    email: "",
    password: "",
    role: "Patient",
  });

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await axios.post("http://127.0.0.1:8000/api/signup", formData);
      if (response.status === 200) {
        console.log("Sign-up successful!", response.data);
        router.push("/signin");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Registration failed.");
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="py-12 md:py-20">
          {/* Section header */}
          <div className="pb-12 text-center">
            <h1 className="animate-[gradient_6s_linear_infinite] bg-[linear-gradient(to_right,theme(colors.gray.200),theme(colors.indigo.200),theme(colors.gray.50),theme(colors.indigo.300),theme(colors.gray.200))] bg-[length:200%_auto] bg-clip-text font-nacelle text-3xl font-semibold text-transparent md:text-4xl">
              Create an account
            </h1>
          </div>

          <form className="mx-auto max-w-[400px]" onSubmit={handleSubmit}>
            <div className="space-y-5">
              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-200/65" htmlFor="name">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  className="form-input w-full"
                  placeholder="Your full name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-200/65" htmlFor="username">
                  Username <span className="text-red-500">*</span>
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  className="form-input w-full"
                  placeholder="Your username"
                  required
                  value={formData.username}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-200/65" htmlFor="email">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="form-input w-full"
                  placeholder="Your email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-indigo-200/65" htmlFor="password">
                  Password <span className="text-red-500">*</span>
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  className="form-input w-full"
                  placeholder="Password (at least 10 characters)"
                  required
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>

              {/* Role Selector */}
              <div>
                <label className="mb-2 block text-sm font-medium text-indigo-200/65">
                  I am signing up as <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-4">
                  {(["Patient", "Doctor"] as const).map((r) => (
                    <label
                      key={r}
                      htmlFor={`role-${r}`}
                      className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg border px-4 py-3 text-sm font-medium transition-all duration-200 ${
                        formData.role === r
                          ? "border-indigo-500 bg-indigo-500/20 text-indigo-300"
                          : "border-gray-700 bg-gray-800/40 text-gray-400 hover:border-gray-500"
                      }`}
                    >
                      <input
                        id={`role-${r}`}
                        type="radio"
                        name="role"
                        value={r}
                        className="sr-only"
                        checked={formData.role === r}
                        onChange={handleChange}
                      />
                      <span>{r === "Patient" ? "🧑‍⚕️" : "👨‍⚕️"}</span>
                      {r}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-5">
              <button
                type="submit"
                id="signup-submit-btn"
                className="btn w-full bg-gradient-to-t from-slate-800 to-indigo-500 bg-[length:100%_100%] bg-[bottom] text-white shadow-[inset_0px_1px_0px_0px_theme(colors.white/.16)] hover:bg-[length:100%_150%]"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Registering..." : "Register"}
              </button>
            </div>
          </form>

          {error && <p className="text-red-500 text-center mt-4">{error}</p>}

          {/* Bottom link */}
          <div className="mt-6 text-center text-sm text-indigo-200/65">
            Already have an account?{" "}
            <Link className="font-medium text-indigo-500" href="/signin">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

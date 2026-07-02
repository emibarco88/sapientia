"use client";

import { useState } from "react";
import { setToken } from "@/lib/api";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function login() {
    setError("");

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error("Invalid login");
      }

      const data = await response.json();
      setToken(data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Invalid username or password");
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
      <div className="w-full max-w-md rounded-2xl bg-slate-900 p-8 shadow-xl border border-slate-800">
        <h1 className="text-3xl font-bold mb-2">Sapientia</h1>
        <p className="text-slate-400 mb-8">Enterprise Intelligence Platform</p>

        <label className="block text-sm mb-2">Username</label>
        <input
          className="w-full mb-4 rounded-lg bg-slate-800 p-3 outline-none"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <label className="block text-sm mb-2">Password</label>
        <input
          className="w-full mb-6 rounded-lg bg-slate-800 p-3 outline-none"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="text-red-400 mb-4">{error}</p>}

        <button
          onClick={login}
          className="w-full rounded-lg bg-blue-600 p-3 font-semibold hover:bg-blue-500"
        >
          Login
        </button>
      </div>
    </main>
  );
}
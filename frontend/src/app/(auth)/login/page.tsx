"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { BarkMindApiError } from "@/lib/api";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      const params = new URLSearchParams(window.location.search);
      router.push(params.get("return") ?? "/dashboard");
    } catch (err) {
      if (err instanceof BarkMindApiError) {
        setError(err.detail);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-zinc-100">Sign in</h1>
        <p className="text-sm text-zinc-500 mt-1">Access your BarkMind account</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="trainer@example.com"
          autoComplete="email"
          required
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="current-password"
          required
        />

        {error && (
          <div className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <Button type="submit" isLoading={loading} className="w-full mt-1" size="lg">
          Sign in
        </Button>
      </form>

      <p className="text-sm text-center text-zinc-500">
        No account?{" "}
        <Link href="/register" className="text-amber-400 hover:underline">
          Register
        </Link>
      </p>
    </div>
  );
}

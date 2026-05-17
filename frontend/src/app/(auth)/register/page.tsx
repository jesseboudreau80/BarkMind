"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { BarkMindApiError } from "@/lib/api";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register(email, username, password, displayName || undefined);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof BarkMindApiError) {
        setError(err.detail);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-zinc-100">Create account</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Join the canine behavioral intelligence community
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          required
        />
        <Input
          label="Username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="trainer_jane"
          autoComplete="username"
          pattern="^[a-zA-Z0-9_-]+$"
          minLength={3}
          maxLength={40}
          required
        />
        <Input
          label="Display Name (optional)"
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Jane Smith, CPDT-KA"
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Min. 8 characters"
          autoComplete="new-password"
          minLength={8}
          required
        />

        {error && (
          <div className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <Button type="submit" isLoading={loading} className="w-full mt-1" size="lg">
          Create Account
        </Button>
      </form>

      <p className="text-sm text-center text-zinc-500">
        Already have an account?{" "}
        <Link href="/login" className="text-amber-400 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

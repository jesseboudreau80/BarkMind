import { Dog, Shield, Database, Users } from "lucide-react";
import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-100 mb-2">About BarkMind</h1>
        <p className="text-zinc-400 leading-relaxed">
          BarkMind is an open canine behavioral intelligence platform built for
          professionals: trainers, daycare leaders, groomers, shelter staff, and
          veterinary teams.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[
          {
            icon: <Dog className="h-5 w-5 text-amber-400" />,
            title: "Behavioral Review",
            body: "Submit documented incidents with media, structured tags, and contextual annotations for community analysis.",
          },
          {
            icon: <Shield className="h-5 w-5 text-amber-400" />,
            title: "Expert Consensus",
            body: "Certified professionals can review cases and submit formal verdicts with structured recommendations.",
          },
          {
            icon: <Database className="h-5 w-5 text-amber-400" />,
            title: "Intelligence Dataset",
            body: "Every annotated case contributes to a growing behavioral intelligence dataset for research and model training.",
          },
          {
            icon: <Users className="h-5 w-5 text-amber-400" />,
            title: "Community Driven",
            body: "Open annotation model with role-based trust — anyone can observe, experts resolve.",
          },
        ].map((card) => (
          <div
            key={card.title}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col gap-2"
          >
            {card.icon}
            <h3 className="font-medium text-zinc-200">{card.title}</h3>
            <p className="text-sm text-zinc-500 leading-relaxed">{card.body}</p>
          </div>
        ))}
      </div>

      <div className="border-t border-zinc-800 pt-6">
        <h2 className="text-lg font-medium text-zinc-200 mb-3">Behavioral Tag Vocabulary</h2>
        <p className="text-sm text-zinc-500 mb-4">
          BarkMind uses a curated vocabulary of behavioral descriptors across five
          categories, each with a severity hint from informational (0) to severe (4).
        </p>
        <Link
          href="/tags"
          className="text-sm text-amber-400 hover:underline"
        >
          Browse the behavioral tag library →
        </Link>
      </div>
    </div>
  );
}

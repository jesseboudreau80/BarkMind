import Navbar from "@/components/layout/Navbar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-zinc-950">
      <Navbar />
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {children}
      </main>
      <footer className="border-t border-zinc-800 py-4 px-4 text-center text-xs text-zinc-600">
        BarkMind · Canine Behavioral Intelligence · Governed by Aegis
      </footer>
    </div>
  );
}

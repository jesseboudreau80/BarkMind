"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Button from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { BookOpen, ChevronDown, Dog, LogOut, PlusCircle, Shield, User } from "lucide-react";
import { useState, useRef, useEffect } from "react";

const navLinks = [
  { href: "/cases", label: "Cases" },
  { href: "/tags", label: "Tags" },
  { href: "/about", label: "About" },
];

export default function Navbar() {
  const { user, logout, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur">
      <nav className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 text-zinc-100 hover:text-amber-400 transition-colors font-semibold"
        >
          <Dog className="h-5 w-5 text-amber-400" />
          <span className="text-sm tracking-tight">BarkMind</span>
        </Link>

        {/* Primary nav links */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "px-3 py-1.5 text-sm rounded-md transition-colors",
                pathname.startsWith(link.href)
                  ? "text-zinc-100 bg-zinc-800"
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50"
              )}
            >
              {link.label}
            </Link>
          ))}
          {user && (user.role === "expert" || user.role === "admin") && (
            <Link
              href="/expert"
              className={cn(
                "px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1.5",
                pathname.startsWith("/expert")
                  ? "text-amber-400 bg-amber-400/10"
                  : "text-zinc-400 hover:text-amber-400 hover:bg-amber-400/5"
              )}
            >
              <Shield className="h-3.5 w-3.5" />
              Expert
            </Link>
          )}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {!isLoading && (
            <>
              {user ? (
                <>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => router.push("/upload")}
                    className="hidden sm:flex"
                  >
                    <PlusCircle className="h-3.5 w-3.5" />
                    Submit Case
                  </Button>

                  {/* User menu */}
                  <div ref={menuRef} className="relative">
                    <button
                      onClick={() => setMenuOpen((v) => !v)}
                      className="flex items-center gap-1.5 px-2 py-1 rounded-md text-sm text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
                    >
                      <span className="w-6 h-6 rounded-full bg-amber-400/20 flex items-center justify-center text-amber-400 text-xs font-bold uppercase">
                        {user.username[0]}
                      </span>
                      <span className="hidden sm:inline text-xs">{user.username}</span>
                      <ChevronDown className="h-3 w-3 text-zinc-500" />
                    </button>

                    {menuOpen && (
                      <div className="absolute right-0 top-full mt-1 w-48 bg-zinc-900 border border-zinc-700 rounded-xl shadow-xl py-1 z-50">
                        <div className="px-3 py-2 border-b border-zinc-800">
                          <p className="text-xs font-medium text-zinc-200">{user.username}</p>
                          <p className="text-xs text-zinc-500">{user.role}</p>
                        </div>
                        <MenuLink href="/dashboard" icon={<BookOpen className="h-3.5 w-3.5" />} onClick={() => setMenuOpen(false)}>
                          Dashboard
                        </MenuLink>
                        <MenuLink href={`/profile/${user.username}`} icon={<User className="h-3.5 w-3.5" />} onClick={() => setMenuOpen(false)}>
                          Profile
                        </MenuLink>
                        {user.role === "admin" && (
                          <>
                            <MenuLink href="/governance" icon={<Shield className="h-3.5 w-3.5" />} onClick={() => setMenuOpen(false)}>
                              Governance
                            </MenuLink>
                            <MenuLink href="/analytics" icon={<Shield className="h-3.5 w-3.5" />} onClick={() => setMenuOpen(false)}>
                              Analytics
                            </MenuLink>
                            <MenuLink href="/moderation" icon={<Shield className="h-3.5 w-3.5" />} onClick={() => setMenuOpen(false)}>
                              Moderation
                            </MenuLink>
                          </>
                        )}
                        <div className="border-t border-zinc-800 mt-1 pt-1">
                          <button
                            onClick={() => { setMenuOpen(false); logout(); }}
                            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-red-400/10 transition-colors"
                          >
                            <LogOut className="h-3.5 w-3.5" />
                            Sign out
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => router.push("/login")}>
                    Sign in
                  </Button>
                  <Button size="sm" onClick={() => router.push("/register")}>
                    Register
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </nav>
    </header>
  );
}

function MenuLink({
  href,
  icon,
  children,
  onClick,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  onClick: () => void;
}) {
  const router = useRouter();
  return (
    <button
      onClick={() => { onClick(); router.push(href); }}
      className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
    >
      {icon}
      {children}
    </button>
  );
}

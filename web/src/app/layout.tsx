import type { Metadata } from "next";
import { Suspense } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { auth, signOut } from "@/auth";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "JobRadar",
  description: "Personal tech job tracker — auto-collected from public job boards",
};

export const instant = false;

async function UserNav() {
  const session = await auth();

  if (!session?.user) {
    return (
      <Link
        href="/api/auth/signin"
        className="text-xs font-medium text-indigo-600 hover:text-indigo-800 border border-indigo-200 px-2.5 py-1 rounded hover:bg-indigo-50 transition-colors"
      >
        Sign In
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      {session.user.image && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={session.user.image}
          alt={session.user.name || "User"}
          className="w-6 h-6 rounded-full border border-slate-200"
        />
      )}
      <span className="font-medium text-slate-700">
        {(session.user as { username?: string }).username || session.user.name || "Logged in"}
      </span>
      <form
        action={async () => {
          "use server";
          await signOut({ redirectTo: "/api/auth/signin" });
        }}
      >
        <button
          type="submit"
          className="text-slate-500 hover:text-rose-600 text-xs px-2 py-1 rounded border border-slate-200 hover:border-rose-200 transition-colors cursor-pointer"
        >
          Sign Out
        </button>
      </form>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/" className="text-xl font-bold tracking-tight text-indigo-600">
                JobRadar
              </Link>
              <nav className="flex items-center gap-4 text-sm font-medium">
                <Link
                  href="/"
                  className="text-slate-600 hover:text-indigo-600 transition-colors"
                >
                  Jobs
                </Link>
                <Link
                  href="/tracker"
                  className="text-slate-600 hover:text-indigo-600 transition-colors"
                >
                  Tracker
                </Link>
                <Link
                  href="/settings"
                  className="text-slate-600 hover:text-indigo-600 transition-colors"
                >
                  Settings
                </Link>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-xs text-slate-400 font-mono hidden sm:inline-block">
                IST (Asia/Kolkata)
              </div>
              <Suspense fallback={<div className="h-6 w-16 bg-slate-100 rounded animate-pulse" />}>
                <UserNav />
              </Suspense>
            </div>
          </div>
        </header>
        <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}

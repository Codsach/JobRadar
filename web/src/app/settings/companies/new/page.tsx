"use client";

/**
 * Add Company — two-step UI:
 *   Step 1: Enter company name (and optionally a careers URL) → probe ATS.
 *   Step 2: Review the preview card → Confirm to save, or Go Back to retry.
 *
 * Authentication is enforced by the server actions; this page itself is public
 * within the app (the layout requires sign-in for navigation).
 */

import { useState, useTransition } from "react";
import Link from "next/link";
import { detectAtsAction, saveCompanyAction, DetectActionResult } from "@/app/actions/companies";
import type { DetectResult } from "@/lib/companies";

type Step = "form" | "preview" | "saved";

const ATS_LABELS: Record<string, string> = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  ashby: "Ashby",
  manual: "Manual (no auto-collection)",
};

function PreviewCard({ result }: { result: DetectResult }) {
  const isManual = result.atsType === "manual";
  return (
    <div className={`rounded-lg border p-4 space-y-2 ${isManual ? "border-amber-200 bg-amber-50" : "border-emerald-200 bg-emerald-50"}`}>
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800 text-sm">{result.companyName}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${isManual ? "bg-amber-200 text-amber-800" : "bg-emerald-200 text-emerald-800"}`}>
          {ATS_LABELS[result.atsType] ?? result.atsType}
        </span>
      </div>

      {!isManual && (
        <p className="text-xs text-slate-600">
          Slug: <code className="font-mono bg-slate-100 px-1 rounded">{result.slug}</code> ·{" "}
          <span className="font-semibold">{result.jobCount.toLocaleString()} jobs</span> found on the board
        </p>
      )}

      {isManual && (
        <p className="text-xs text-amber-700">
          No supported ATS was detected. The company will be saved as a manual source
          {result.careersUrl ? " with the provided careers URL" : ""}. You can visit
          the careers page manually; it will not be auto-collected.
        </p>
      )}

      {result.careersUrl && (
        <p className="text-xs text-slate-500 truncate">
          Careers URL:{" "}
          <a href={result.careersUrl} target="_blank" rel="noopener noreferrer" className="underline text-indigo-600">
            {result.careersUrl}
          </a>
        </p>
      )}
    </div>
  );
}

export default function AddCompanyPage() {
  const [step, setStep] = useState<Step>("form");
  const [companyName, setCompanyName] = useState("");
  const [careersUrl, setCareersUrl] = useState("");
  const [preview, setPreview] = useState<DetectResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleDetect() {
    setError(null);
    startTransition(async () => {
      const res: DetectActionResult = await detectAtsAction(companyName, careersUrl || undefined);
      if (!res.ok || !res.data) {
        setError(res.error ?? "Unknown error.");
        return;
      }
      setPreview(res.data);
      setStep("preview");
    });
  }

  function handleConfirm() {
    if (!preview) return;
    setError(null);
    startTransition(async () => {
      const res = await saveCompanyAction(preview);
      if (!res.ok) {
        setError(res.error ?? "Failed to save.");
        return;
      }
      setStep("saved");
    });
  }

  if (step === "saved") {
    return (
      <div className="max-w-lg mx-auto space-y-4">
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6 text-center space-y-3">
          <p className="text-emerald-700 font-semibold text-base">Company saved ✓</p>
          <p className="text-sm text-slate-600">
            <strong>{preview?.companyName}</strong> has been added
            {preview?.atsType !== "manual"
              ? " and will be collected on the next scheduled run."
              : " as a manual source."}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <Link
              href="/settings"
              className="text-sm text-indigo-600 hover:text-indigo-800 underline"
            >
              ← Back to Settings
            </Link>
            <button
              onClick={() => {
                setCompanyName("");
                setCareersUrl("");
                setPreview(null);
                setError(null);
                setStep("form");
              }}
              className="text-sm text-slate-500 hover:text-slate-800 underline"
            >
              Add another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
          <Link href="/settings" className="hover:text-indigo-600 transition-colors">
            Settings
          </Link>
          <span>›</span>
          <span className="text-slate-800 font-medium">Add Company</span>
        </div>
        <h1 className="text-xl font-bold text-slate-900">Add Company</h1>
        <p className="text-sm text-slate-500 mt-1">
          Enter a company name or paste its careers page URL. JobRadar will probe
          Greenhouse, Lever, and Ashby to find open roles.
        </p>
      </div>

      {step === "form" && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-5">
          <div>
            <label htmlFor="company-name" className="block text-sm font-medium text-slate-700 mb-1">
              Company Name <span className="text-rose-500">*</span>
            </label>
            <input
              id="company-name"
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Cloudflare"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="careers-url" className="block text-sm font-medium text-slate-700 mb-1">
              Careers URL{" "}
              <span className="font-normal text-slate-400">(optional — helps if name is ambiguous)</span>
            </label>
            <input
              id="careers-url"
              type="url"
              value={careersUrl}
              onChange={(e) => setCareersUrl(e.target.value)}
              placeholder="e.g. https://boards.greenhouse.io/cloudflare"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <p className="text-xs text-slate-400 mt-1">
              Supported patterns: boards.greenhouse.io/…, jobs.lever.co/…, jobs.ashbyhq.com/…
            </p>
          </div>

          {error && (
            <p className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleDetect}
              disabled={isPending || !companyName.trim()}
              className="bg-indigo-600 text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {isPending ? "Detecting…" : "Detect ATS"}
            </button>
            <Link href="/settings" className="text-sm text-slate-500 hover:text-slate-800">
              Cancel
            </Link>
          </div>
        </div>
      )}

      {step === "preview" && preview && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-5">
          <div>
            <p className="text-sm font-medium text-slate-700 mb-3">Preview</p>
            <PreviewCard result={preview} />
          </div>

          {error && (
            <p className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleConfirm}
              disabled={isPending}
              className="bg-indigo-600 text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 shadow-sm"
            >
              {isPending ? "Saving…" : "Confirm & Save"}
            </button>
            <button
              onClick={() => {
                setStep("form");
                setPreview(null);
                setError(null);
              }}
              className="text-sm text-slate-500 hover:text-slate-800 border border-slate-200 px-4 py-2 rounded-md"
            >
              ← Go Back
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


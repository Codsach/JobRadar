export type ApplicationStatus = "saved" | "applied" | "interview" | "rejected" | "offer";

export const APPLICATION_STATUSES: { key: ApplicationStatus; label: string; color: string; badgeBg: string }[] = [
  { key: "saved", label: "Saved", color: "text-slate-700 border-slate-300 bg-slate-100", badgeBg: "bg-slate-100 text-slate-800" },
  { key: "applied", label: "Applied", color: "text-blue-700 border-blue-300 bg-blue-50", badgeBg: "bg-blue-100 text-blue-800" },
  { key: "interview", label: "Interview", color: "text-amber-700 border-amber-300 bg-amber-50", badgeBg: "bg-amber-100 text-amber-800" },
  { key: "offer", label: "Offer", color: "text-emerald-700 border-emerald-300 bg-emerald-50", badgeBg: "bg-emerald-100 text-emerald-800" },
  { key: "rejected", label: "Rejected", color: "text-rose-700 border-rose-300 bg-rose-50", badgeBg: "bg-rose-100 text-rose-800" },
];

export interface ApplicationItem {
  id: number;
  job_id: number;
  status: ApplicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  title: string;
  company_name: string;
  location: string | null;
  url: string;
  category: string | null;
  level: string | null;
  posted_at: string | null;
  first_seen_at: string;
}


import Link from "next/link";
import { getApplications, APPLICATION_STATUSES, ApplicationItem, ApplicationStatus } from "@/lib/applications";
import { TrackerCard } from "./TrackerCard";

export const instant = false;

export default async function TrackerPage() {
  const allApplications = await getApplications();

  // Group applications by status
  const grouped: Record<ApplicationStatus, ApplicationItem[]> = {
    saved: [],
    applied: [],
    interview: [],
    offer: [],
    rejected: [],
  };

  for (const app of allApplications) {
    if (grouped[app.status]) {
      grouped[app.status].push(app);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Application Tracker</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track your job search pipeline across Saved, Applied, Interview, Offer, and Rejected.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-md shadow-xs">
            Total Tracked: <span className="font-semibold text-slate-900">{allApplications.length}</span>
          </div>
          <Link
            href="/"
            className="text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 rounded-md shadow-xs transition-colors"
          >
            Browse Jobs
          </Link>
        </div>
      </div>

      {/* Board columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 items-start">
        {APPLICATION_STATUSES.map((statusMeta) => {
          const items = grouped[statusMeta.key] || [];

          return (
            <div
              key={statusMeta.key}
              className="bg-slate-100/70 border border-slate-200 rounded-xl p-3 flex flex-col gap-3 min-h-[300px]"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusMeta.badgeBg}`}>
                    {statusMeta.label}
                  </span>
                </div>
                <span className="text-xs font-mono font-medium text-slate-400">
                  {items.length}
                </span>
              </div>

              {/* Items in column */}
              <div className="space-y-2.5">
                {items.length === 0 ? (
                  <div className="bg-white/60 border border-dashed border-slate-200 rounded-lg p-4 text-center text-xs text-slate-400">
                    No {statusMeta.label.toLowerCase()} jobs
                  </div>
                ) : (
                  items.map((app) => (
                    <TrackerCard key={app.id} app={app} />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


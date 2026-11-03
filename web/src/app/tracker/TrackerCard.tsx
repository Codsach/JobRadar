"use client";

import { useState, useTransition } from "react";
import { ApplicationItem, ApplicationStatus, APPLICATION_STATUSES } from "@/lib/application-types";
import { updateJobApplicationAction, deleteJobApplicationAction } from "@/app/actions/application";

interface Props {
  app: ApplicationItem;
}

export function TrackerCard({ app }: Props) {
  const [status, setStatus] = useState<ApplicationStatus>(app.status);
  const [notes, setNotes] = useState<string>(app.notes || "");
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [isPending, startTransition] = useTransition();

  const handleStatusChange = (newStatus: ApplicationStatus) => {
    if (newStatus === status) return;
    setStatus(newStatus);
    startTransition(async () => {
      await updateJobApplicationAction(app.job_id, newStatus, notes.trim() || null);
    });
  };

  const handleSaveNotes = () => {
    setIsEditingNotes(false);
    startTransition(async () => {
      await updateJobApplicationAction(app.job_id, status, notes.trim() || null);
    });
  };

  const handleDelete = () => {
    if (confirm(`Untrack application for ${app.title} at ${app.company_name}?`)) {
      startTransition(async () => {
        await deleteJobApplicationAction(app.job_id);
      });
    }
  };

  const levelColor =
    app.level === "fresher"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : app.level === "experienced"
      ? "bg-blue-50 text-blue-700 border-blue-200"
      : "bg-slate-100 text-slate-600 border-slate-200";

  const updatedDateStr = new Date(app.updated_at).toLocaleDateString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
  });

  return (
    <div
      className={`bg-white rounded-lg border border-slate-200 p-3.5 shadow-xs space-y-2.5 transition-all hover:border-slate-300 hover:shadow-sm ${
        isPending ? "opacity-60 pointer-events-none" : ""
      }`}
    >
      {/* Header: Company & Title */}
      <div>
        <div className="flex items-center justify-between text-xs text-slate-500 font-medium mb-0.5">
          <span className="text-slate-800 font-semibold">{app.company_name}</span>
          <span className="text-[11px] text-slate-400">Updated {updatedDateStr}</span>
        </div>
        <a
          href={app.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 hover:underline leading-snug line-clamp-2"
        >
          {app.title}
        </a>
      </div>

      {/* Badges: Location, Level, Category */}
      <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
        {app.location && (
          <span className="text-slate-500 truncate max-w-[150px]" title={app.location}>
            📍 {app.location}
          </span>
        )}
        {app.level && (
          <span className={`px-1.5 py-0.5 rounded border font-medium ${levelColor}`}>
            {app.level}
          </span>
        )}
        {app.category && (
          <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
            {app.category}
          </span>
        )}
      </div>

      {/* Notes section */}
      <div className="text-xs pt-1 border-t border-slate-100">
        {isEditingNotes ? (
          <div className="space-y-1.5 mt-1">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add interview stages, contact, referral, or notes..."
              rows={2}
              autoFocus
              className="w-full p-1.5 text-xs border border-indigo-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-inner"
            />
            <div className="flex items-center justify-end gap-1.5">
              <button
                type="button"
                onClick={() => setIsEditingNotes(false)}
                className="text-[11px] text-slate-500 hover:text-slate-700 px-2 py-0.5"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveNotes}
                className="text-[11px] font-medium px-2 py-0.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors shadow-xs"
              >
                Save Note
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-2">
            <div
              onClick={() => setIsEditingNotes(true)}
              className="cursor-pointer group flex-1"
            >
              {notes ? (
                <div className="text-[11px] text-slate-700 bg-amber-50/70 border border-amber-200/80 rounded p-1.5 group-hover:bg-amber-100/60 transition-colors">
                  <span className="font-semibold text-amber-800 mr-1">Note:</span>
                  <span className="whitespace-pre-wrap">{notes}</span>
                </div>
              ) : (
                <span className="text-[11px] text-slate-400 group-hover:text-indigo-600 transition-colors">
                  + Add note
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Move status & delete actions */}
      <div className="pt-1.5 border-t border-slate-100 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1">
          <label htmlFor={`status-select-${app.id}`} className="text-[11px] text-slate-400 font-medium">
            Move:
          </label>
          <select
            id={`status-select-${app.id}`}
            value={status}
            onChange={(e) => handleStatusChange(e.target.value as ApplicationStatus)}
            className="text-[11px] font-medium bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {APPLICATION_STATUSES.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={handleDelete}
          title="Remove from tracker"
          className="text-[11px] text-slate-400 hover:text-rose-600 transition-colors px-1"
        >
          Untrack
        </button>
      </div>
    </div>
  );
}

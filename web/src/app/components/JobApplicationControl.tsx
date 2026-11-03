"use client";

import { useState, useTransition } from "react";
import { ApplicationStatus, APPLICATION_STATUSES } from "@/lib/application-types";
import { updateJobApplicationAction, deleteJobApplicationAction } from "@/app/actions/application";

interface Props {
  jobId: number;
  initialStatus: ApplicationStatus | null;
  initialNotes: string | null;
}

export function JobApplicationControl({ jobId, initialStatus, initialNotes }: Props) {
  const [status, setStatus] = useState<ApplicationStatus | null>(initialStatus);
  const [notes, setNotes] = useState<string>(initialNotes || "");
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [isPending, startTransition] = useTransition();

  const handleStatusChange = (newStatus: ApplicationStatus) => {
    // If clicking same status, remove tracking
    if (status === newStatus) {
      setStatus(null);
      startTransition(async () => {
        await deleteJobApplicationAction(jobId);
      });
      return;
    }

    setStatus(newStatus);
    startTransition(async () => {
      await updateJobApplicationAction(jobId, newStatus, notes.trim() || null);
    });
  };

  const handleSaveNotes = () => {
    setIsEditingNotes(false);
    startTransition(async () => {
      if (status) {
        await updateJobApplicationAction(jobId, status, notes.trim() || null);
      } else if (notes.trim()) {
        // If no status was set yet, default to 'saved' when notes are added
        setStatus("saved");
        await updateJobApplicationAction(jobId, "saved", notes.trim());
      }
    });
  };

  return (
    <div className="space-y-1.5 py-1">
      {/* Status Buttons */}
      <div className="flex flex-wrap items-center gap-1">
        {APPLICATION_STATUSES.map((s) => {
          const isActive = status === s.key;
          return (
            <button
              key={s.key}
              type="button"
              disabled={isPending}
              onClick={() => handleStatusChange(s.key)}
              title={isActive ? `Click to untrack (${s.label})` : `Set as ${s.label}`}
              className={`px-2 py-0.5 text-[11px] font-medium rounded border transition-all ${
                isActive
                  ? `${s.color} font-semibold ring-2 ring-indigo-500/20 shadow-xs`
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900"
              } ${isPending ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
            >
              {s.label}
            </button>
          );
        })}
      </div>

      {/* Notes trigger or input */}
      <div className="text-xs">
        {isEditingNotes ? (
          <div className="flex items-center gap-1.5 mt-1">
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add application notes..."
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSaveNotes();
                } else if (e.key === "Escape") {
                  setIsEditingNotes(false);
                }
              }}
              className="px-2 py-0.5 text-xs border border-indigo-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-48 shadow-inner"
            />
            <button
              type="button"
              onClick={handleSaveNotes}
              className="text-[11px] font-medium px-2 py-0.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors shadow-xs"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => setIsEditingNotes(false)}
              className="text-[11px] text-slate-500 hover:text-slate-700 px-1 py-0.5"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-slate-500">
            {notes ? (
              <button
                type="button"
                onClick={() => setIsEditingNotes(true)}
                className="text-left text-[11px] text-slate-700 bg-amber-50 hover:bg-amber-100/80 border border-amber-200 rounded px-1.5 py-0.5 max-w-[220px] truncate transition-colors flex items-center gap-1"
                title={`Note: ${notes} (Click to edit)`}
              >
                <span>📝</span>
                <span className="truncate">{notes}</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setIsEditingNotes(true)}
                className="text-[11px] text-slate-400 hover:text-indigo-600 transition-colors flex items-center gap-0.5"
              >
                <span>+ note</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

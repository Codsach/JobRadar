import { Suspense } from "react";
import Link from "next/link";
import {
  getJobs,
  getTotalJobCount,
  getCounters,
  getFilterOptions,
  formatHonestDate,
  JobFilters,
} from "@/lib/jobs";
import { getPreferences } from "@/lib/preferences";
import { getSourceHealth } from "@/lib/sources";
import { JobApplicationControl } from "@/app/components/JobApplicationControl";

export const instant = false;

interface PageProps {
  searchParams: Promise<{
    level?: string;
    location?: string;
    company?: string;
    category?: string;
    status?: string;
    all?: string;
  }>;
}

async function CountersSection() {
  const prefs = await getPreferences();
  const counters = await getCounters(prefs);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
          New Today
        </div>
        <div className="mt-1 flex items-baseline justify-between">
          <div className="text-2xl font-bold text-slate-900">{counters.newToday}</div>
          <span className="text-xs text-slate-400">by first_seen_at (IST)</span>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
          Matching Jobs
        </div>
        <div className="mt-1 flex items-baseline justify-between">
          <div className="text-2xl font-bold text-indigo-600">{counters.matchingJobs}</div>
          <Link
            href="/settings"
            className="text-xs text-indigo-600 hover:text-indigo-800 underline"
          >
            edit preferences
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
          Applied
        </div>
        <div className="mt-1 flex items-baseline justify-between">
          <div className="text-2xl font-bold text-emerald-600">{counters.appliedCount}</div>
          <span className="text-xs text-slate-400">tracked applications</span>
        </div>
      </div>
    </div>
  );
}

async function SourceHealthPanel() {
  const sources = await getSourceHealth();

  if (sources.length === 0) {
    return null;
  }

  return (
    <details className="mb-6 group bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden" open>
      <summary className="px-4 py-3 cursor-pointer select-none flex items-center justify-between font-medium text-sm text-slate-800 hover:bg-slate-50 transition-colors">
        <span className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
          Source Health ({sources.length} sources)
        </span>
        <span className="text-xs text-slate-400 group-open:rotate-180 transition-transform">
          ▼
        </span>
      </summary>

      <div className="px-4 pb-4 pt-1 border-t border-slate-100">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-2">
          {sources.map((src) => {
            const isManual = src.type === "manual" || !src.enabled;
            const isSuccess = src.last_run_status === "success";
            const isFailed = src.last_run_status === "failed";
            const isRunning = src.last_run_status === "running";
            const careersUrl =
              typeof src.config?.careers_url === "string"
                ? src.config.careers_url
                : typeof src.config?.url === "string"
                ? src.config.url
                : undefined;

            return (
              <div
                key={src.id}
                className="p-3 rounded-md border border-slate-100 bg-slate-50 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 truncate" title={src.slug}>
                    {src.company_name} ({src.slug})
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      isManual
                        ? "bg-slate-200 text-slate-700"
                        : isSuccess
                        ? "bg-emerald-100 text-emerald-700"
                        : isFailed
                        ? "bg-rose-100 text-rose-700"
                        : isRunning
                        ? "bg-amber-100 text-amber-700"
                        : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {isManual ? "Manual — not auto-collected" : src.last_run_status || "Never run"}
                  </span>
                </div>

                <div className="text-slate-500 flex justify-between items-center">
                  <span>Type: {src.type}</span>
                  {isManual ? (
                    careersUrl ? (
                      <a
                        href={careersUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline font-medium"
                      >
                        Open careers ↗
                      </a>
                    ) : (
                      <span className="text-slate-400">Manual review</span>
                    )
                  ) : (
                    <span>
                      {src.last_run_at
                        ? new Date(src.last_run_at).toLocaleString("en-IN", {
                            timeZone: "Asia/Kolkata",
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          }) + " IST"
                        : "Never"}
                    </span>
                  )}
                </div>

                {!isManual && src.last_run_status && (
                  <div className="text-slate-600 flex justify-between pt-1 border-t border-slate-200">
                    <span>Found: <b>{src.jobs_found ?? 0}</b></span>
                    <span>New: <b>{src.new_count ?? 0}</b></span>
                  </div>
                )}

                {!isManual && src.error && (
                  <p className="text-rose-600 truncate text-[11px] pt-1" title={src.error}>
                    Error: {src.error}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </details>
  );
}

function buildModeUrl(filters: JobFilters, all: boolean): string {
  const params = new URLSearchParams();
  if (filters.category && filters.category !== "all") params.set("category", filters.category);
  if (filters.level && filters.level !== "all") params.set("level", filters.level);
  if (filters.company && filters.company !== "all") params.set("company", filters.company);
  if (filters.location) params.set("location", filters.location);
  if (filters.status && filters.status !== "active") params.set("status", filters.status);
  if (all) params.set("all", "true");
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}

async function FilterBar({ filters }: { filters: JobFilters }) {
  const options = await getFilterOptions();

  return (
    <form
      method="GET"
      action="/"
      className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm mb-6 flex flex-wrap items-end gap-3"
    >
      {/* Preserve "all" toggle in form submissions */}
      {filters.all && <input type="hidden" name="all" value="true" />}

      {/* Mode toggle bar: Matching Jobs (default) vs All Jobs */}
      <div className="w-full flex items-center justify-between pb-3 mb-1 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">View:</span>
          <div className="inline-flex rounded-md border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium">
            <Link
              href={buildModeUrl(filters, false)}
              className={`px-3 py-1 rounded transition-colors ${
                !filters.all
                  ? "bg-white text-indigo-600 shadow-xs font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Matching jobs
            </Link>
            <Link
              href={buildModeUrl(filters, true)}
              className={`px-3 py-1 rounded transition-colors ${
                filters.all
                  ? "bg-white text-indigo-600 shadow-xs font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All jobs
            </Link>
          </div>
        </div>
        {!filters.all ? (
          <span className="text-xs text-slate-400">
            Filtered by saved presets & preferences
          </span>
        ) : (
          <span className="text-xs text-slate-400">
            Showing all active jobs
          </span>
        )}
      </div>

      {/* Category filter */}
      <div className="flex-1 min-w-[130px]">
        <label className="block text-xs font-semibold text-slate-600 mb-1">
          Category
        </label>
        <select
          name="category"
          defaultValue={filters.category || "all"}
          className="w-full text-xs rounded border border-slate-300 px-2 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="all">All Categories</option>
          {options.categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Level filter */}
      <div className="flex-1 min-w-[120px]">
        <label className="block text-xs font-semibold text-slate-600 mb-1">
          Level
        </label>
        <select
          name="level"
          defaultValue={filters.level || "all"}
          className="w-full text-xs rounded border border-slate-300 px-2 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="all">All Levels</option>
          {options.levels.map((lvl) => (
            <option key={lvl} value={lvl}>
              {lvl}
            </option>
          ))}
        </select>
      </div>

      {/* Company filter */}
      <div className="flex-1 min-w-[120px]">
        <label className="block text-xs font-semibold text-slate-600 mb-1">
          Company
        </label>
        <select
          name="company"
          defaultValue={filters.company || "all"}
          className="w-full text-xs rounded border border-slate-300 px-2 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="all">All Companies</option>
          {options.companies.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Location filter */}
      <div className="flex-1 min-w-[140px]">
        <label className="block text-xs font-semibold text-slate-600 mb-1">
          Location
        </label>
        <input
          type="text"
          name="location"
          defaultValue={filters.location || ""}
          placeholder="e.g. Remote, Dublin"
          className="w-full text-xs rounded border border-slate-300 px-2 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      {/* Status filter (defaults to active) */}
      <div className="flex-1 min-w-[110px]">
        <label className="block text-xs font-semibold text-slate-600 mb-1">
          Status
        </label>
        <select
          name="status"
          defaultValue={filters.status || "active"}
          className="w-full text-xs rounded border border-slate-300 px-2 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="active">Active only</option>
          <option value="closed">Closed only</option>
          <option value="all">All statuses</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="submit"
          className="bg-indigo-600 text-white text-xs font-medium px-4 py-1.5 rounded hover:bg-indigo-700 transition-colors shadow-sm"
        >
          Filter
        </button>
        <Link
          href="/"
          className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1.5"
        >
          Reset
        </Link>
      </div>
    </form>
  );
}

async function JobList({
  filters,
}: {
  filters: JobFilters;
}) {
  const prefs = await getPreferences();
  const [jobs, total] = await Promise.all([
    getJobs(filters, prefs),
    getTotalJobCount(filters, prefs),
  ]);

  // Determine whether any non-default filter is active
  const hasActiveFilters =
    (filters.level && filters.level !== "all") ||
    (filters.category && filters.category !== "all") ||
    (filters.company && filters.company !== "all") ||
    (filters.location && filters.location !== "all") ||
    (filters.status && filters.status !== "active") ||
    Boolean(filters.all);

  if (jobs.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-500">
        <p className="text-base font-medium">
          {!filters.all
            ? "No jobs matching your saved preferences & filters."
            : "No jobs matching your filter criteria."}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          {!filters.all ? (
            <>
              Try viewing{" "}
              <Link href="/?all=true" className="underline text-indigo-500 hover:text-indigo-700">
                All jobs
              </Link>
              {", "}
              <Link href="/settings" className="underline text-indigo-500 hover:text-indigo-700">
                adjusting role presets
              </Link>
              {", or clearing filters."}
            </>
          ) : (
            <>
              Try{" "}
              <Link href="/" className="underline text-indigo-500 hover:text-indigo-700">
                clearing filters
              </Link>{" "}
              or run <code>python -m collectors.run</code> to fetch new jobs.
            </>
          )}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex justify-between items-center text-xs text-slate-500">
        <span>
          Showing{" "}
          <span className="font-semibold text-slate-700">{jobs.length}</span>
          {" of "}
          <span className="font-semibold text-slate-700">{total.toLocaleString()}</span>{" "}
          {!filters.all ? "matching " : ""}job{total !== 1 ? "s" : ""}
          {jobs.length >= 200 && (
            <span className="text-slate-400"> (limit 200)</span>
          )}
          {hasActiveFilters && (
            <>
              {" "}·{" "}
              <Link
                href="/"
                className="text-indigo-500 hover:text-indigo-700 underline font-medium"
              >
                clear filters ×
              </Link>
            </>
          )}
        </span>
        <span>Times displayed in IST</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/50 text-slate-700 font-semibold text-xs">
              <th className="py-3 px-4">Title</th>
              <th className="py-3 px-3">Company</th>
              <th className="py-3 px-3">Location</th>
              <th className="py-3 px-3">Category</th>
              <th className="py-3 px-3">Level</th>
              <th className="py-3 px-4">Date</th>
              <th className="py-3 px-4 min-w-[280px]">Application Status & Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {jobs.map((job) => {
              const levelColor =
                job.level === "fresher"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : job.level === "experienced"
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : "bg-slate-100 text-slate-600 border-slate-200";

              return (
                <tr key={job.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-medium">
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-800 hover:underline"
                    >
                      {job.title}
                    </a>
                  </td>
                  <td className="py-3 px-3 text-slate-800 whitespace-nowrap">
                    {job.company_name}
                  </td>
                  <td className="py-3 px-3 text-slate-500 text-xs">
                    {job.location || "—"}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className="inline-block px-2 py-0.5 text-xs rounded bg-slate-100 text-slate-700 font-medium">
                      {job.category || "Other Tech"}
                    </span>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span
                      className={`inline-block px-2 py-0.5 text-[11px] rounded border font-medium ${levelColor}`}
                    >
                      {job.level || "unknown"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs whitespace-nowrap">
                    <span
                      className={
                        job.posted_at
                          ? "text-slate-800 font-medium"
                          : "text-slate-500 italic"
                      }
                      title={`first_seen_at: ${job.first_seen_at}`}
                    >
                      {formatHonestDate(job.posted_at, job.first_seen_at)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <JobApplicationControl
                      jobId={job.id}
                      initialStatus={job.application_status}
                      initialNotes={job.application_notes}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default async function HomePage(props: PageProps) {
  const searchParams = await props.searchParams;
  const isAll = searchParams.all === "true" || searchParams.all === "1";
  const filters: JobFilters = {
    level: searchParams.level,
    location: searchParams.location,
    company: searchParams.company,
    category: searchParams.category,
    status: searchParams.status || "active",
    all: isAll,
  };

  return (
    <div className="space-y-4">
      <Suspense fallback={<div className="h-20 bg-slate-100 animate-pulse rounded-lg" />}>
        <CountersSection />
      </Suspense>

      <Suspense fallback={null}>
        <SourceHealthPanel />
      </Suspense>

      <Suspense fallback={<div className="h-14 bg-slate-100 animate-pulse rounded-lg" />}>
        <FilterBar filters={filters} />
      </Suspense>

      <Suspense
        fallback={
          <div className="h-64 bg-slate-100 animate-pulse rounded-lg flex items-center justify-center text-slate-400 text-sm">
            Loading active jobs...
          </div>
        }
      >
        <JobList filters={filters} />
      </Suspense>
    </div>
  );
}

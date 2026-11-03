/**
 * Fetch jobs, counters, and filter options from the database.
 * Uses parameterized SQL with the `pg` driver — no ORM.
 *
 * Times are stored in UTC; displayed in IST (Asia/Kolkata) per AGENTS.md.
 */
import "server-only";
import { getPool } from "./db";
import { Preferences } from "./preferences";
import { ApplicationStatus } from "./applications";

export interface JobRow {
  id: number;
  title: string;
  company_name: string;
  location: string | null;
  url: string;
  category: string | null;
  level: string | null;
  status: string;
  posted_at: string | null; // ISO string or null
  first_seen_at: string; // ISO string
  posted_at_source: string; // "api" | "parsed" | "none"
  application_status: ApplicationStatus | null;
  application_notes: string | null;
}

export interface JobFilters {
  level?: string;
  location?: string;
  company?: string;
  category?: string;
  status?: string;
}

export interface Counters {
  newToday: number;
  matchingJobs: number;
  appliedCount: number;
}

export interface FilterOptions {
  levels: string[];
  locations: string[];
  companies: string[];
  categories: string[];
}

const IST = "Asia/Kolkata";

/**
 * Honest date display exactly as defined in PRD §4:
 * - If posted_at exists: "Posted 2 Nov"
 * - If not: "Discovered today — posting date unavailable" (or "Discovered 2 Nov — posting date unavailable")
 */
export function formatHonestDate(
  posted_at: string | null,
  first_seen_at: string
): string {
  if (posted_at) {
    const d = new Date(posted_at);
    const day = d.toLocaleDateString("en-IN", { timeZone: IST, day: "numeric" });
    const month = d.toLocaleDateString("en-IN", { timeZone: IST, month: "short" });
    return `Posted ${day} ${month}`;
  }

  const firstSeen = new Date(first_seen_at);
  const now = new Date();

  const firstSeenIST = firstSeen.toLocaleDateString("en-IN", { timeZone: IST });
  const nowIST = now.toLocaleDateString("en-IN", { timeZone: IST });

  if (firstSeenIST === nowIST) {
    return "Discovered today — posting date unavailable";
  }

  const day = firstSeen.toLocaleDateString("en-IN", { timeZone: IST, day: "numeric" });
  const month = firstSeen.toLocaleDateString("en-IN", { timeZone: IST, month: "short" });
  return `Discovered ${day} ${month} — posting date unavailable`;
}

/** Standard date formatter for timestamps. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", {
    timeZone: IST,
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export async function getJobs(filters: JobFilters = {}): Promise<JobRow[]> {
  const pool = getPool();
  const conditions: string[] = [];
  const params: unknown[] = [];

  // Default status: 'active'
  const statusFilter = filters.status || "active";
  if (statusFilter !== "all") {
    params.push(statusFilter);
    conditions.push(`j.status = $${params.length}`);
  }

  if (filters.level && filters.level !== "all") {
    params.push(filters.level);
    conditions.push(`j.level = $${params.length}`);
  }

  if (filters.category && filters.category !== "all") {
    params.push(filters.category);
    conditions.push(`j.category = $${params.length}`);
  }

  if (filters.company && filters.company !== "all") {
    params.push(filters.company);
    conditions.push(`c.name = $${params.length}`);
  }

  if (filters.location && filters.location !== "all") {
    params.push(`%${filters.location}%`);
    conditions.push(`j.location ILIKE $${params.length}`);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  const query = `
    SELECT
      j.id,
      j.title,
      c.name AS company_name,
      j.location,
      j.url,
      j.category,
      j.level,
      j.status,
      j.posted_at AT TIME ZONE 'UTC' AS posted_at,
      j.first_seen_at AT TIME ZONE 'UTC' AS first_seen_at,
      j.posted_at_source,
      a.status AS application_status,
      a.notes AS application_notes
    FROM jobs j
    JOIN companies c ON c.id = j.company_id
    LEFT JOIN applications a ON a.job_id = j.id
    ${whereClause}
    ORDER BY j.first_seen_at DESC
    LIMIT 200
  `;

  const { rows } = await pool.query(query, params);

  return rows.map((r) => ({
    ...r,
    posted_at: r.posted_at ? new Date(r.posted_at).toISOString() : null,
    first_seen_at: new Date(r.first_seen_at).toISOString(),
  }));
}

export async function getFilterOptions(): Promise<FilterOptions> {
  const pool = getPool();

  const [levelsRes, locationsRes, companiesRes, categoriesRes] = await Promise.all([
    pool.query(`SELECT DISTINCT level FROM jobs WHERE level IS NOT NULL ORDER BY level ASC`),
    pool.query(`SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL AND location != '' ORDER BY location ASC LIMIT 50`),
    pool.query(`SELECT DISTINCT c.name FROM companies c JOIN jobs j ON j.company_id = c.id ORDER BY c.name ASC`),
    pool.query(`SELECT DISTINCT category FROM jobs WHERE category IS NOT NULL ORDER BY category ASC`),
  ]);

  return {
    levels: levelsRes.rows.map((r) => r.level),
    locations: locationsRes.rows.map((r) => r.location),
    companies: companiesRes.rows.map((r) => r.name),
    categories: categoriesRes.rows.map((r) => r.category),
  };
}

export async function getCounters(prefs?: Preferences): Promise<Counters> {
  const pool = getPool();

  // 1. New today (by first_seen_at, IST day)
  const newTodayQuery = `
    SELECT COUNT(*)::int AS count
    FROM jobs
    WHERE (first_seen_at AT TIME ZONE 'Asia/Kolkata')::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date
  `;

  // 2. Applied count from applications table
  const appliedQuery = `
    SELECT COUNT(*)::int AS count
    FROM applications
    WHERE status = 'applied'
  `;

  // 3. Matching jobs based on preferences
  let matchingQuery = `
    SELECT COUNT(*)::int AS count
    FROM jobs j
    JOIN companies c ON c.id = j.company_id
    WHERE j.status = 'active'
  `;
  const matchingParams: unknown[] = [];

  if (prefs) {
    if (prefs.levels.length > 0) {
      matchingParams.push(prefs.levels);
      matchingQuery += ` AND j.level = ANY($${matchingParams.length}::text[])`;
    }
    if (prefs.categories.length > 0) {
      matchingParams.push(prefs.categories);
      matchingQuery += ` AND j.category = ANY($${matchingParams.length}::text[])`;
    }
    if (prefs.companies.length > 0) {
      matchingParams.push(prefs.companies);
      matchingQuery += ` AND c.name = ANY($${matchingParams.length}::text[])`;
    }
    if (prefs.locations.length > 0) {
      const locConditions = prefs.locations.map((loc) => {
        matchingParams.push(`%${loc}%`);
        return `j.location ILIKE $${matchingParams.length}`;
      });
      matchingQuery += ` AND (${locConditions.join(" OR ")})`;
    }
    if (prefs.include_keywords.length > 0) {
      const kwConditions = prefs.include_keywords.map((kw) => {
        matchingParams.push(`%${kw}%`);
        return `(j.title ILIKE $${matchingParams.length} OR j.description ILIKE $${matchingParams.length})`;
      });
      matchingQuery += ` AND (${kwConditions.join(" OR ")})`;
    }
    if (prefs.exclude_keywords.length > 0) {
      const exConditions = prefs.exclude_keywords.map((kw) => {
        matchingParams.push(`%${kw}%`);
        return `(j.title ILIKE $${matchingParams.length} OR j.description ILIKE $${matchingParams.length})`;
      });
      matchingQuery += ` AND NOT (${exConditions.join(" OR ")})`;
    }
  }

  const [newTodayRes, appliedRes, matchingRes] = await Promise.all([
    pool.query(newTodayQuery),
    pool.query(appliedQuery),
    pool.query(matchingQuery, matchingParams),
  ]);

  return {
    newToday: newTodayRes.rows[0]?.count ?? 0,
    appliedCount: appliedRes.rows[0]?.count ?? 0,
    matchingJobs: matchingRes.rows[0]?.count ?? 0,
  };
}

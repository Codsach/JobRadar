/**
 * ATS detection and company/source persistence for the "Add Company" UI.
 *
 * Rules (AGENTS.md):
 *  - web/ may write to companies and sources (added in this session).
 *  - Never invent slugs or fabricate job counts.
 *  - Only save a source if the ATS probe returns HTTP 200 with ≥1 real jobs.
 *  - Rate limit probing: max 3 probes per 10 seconds (in-memory, single-user).
 *  - If nothing is found, save as manual source with the careers URL.
 *
 * Python owns the schema; this file only does DML (INSERT ... ON CONFLICT).
 */
import "server-only";
import { getPool } from "./db";

// ---------------------------------------------------------------------------
// Rate limiter (in-memory, adequate for single-user)
// ---------------------------------------------------------------------------
const PROBE_WINDOW_MS = 10_000;
const PROBE_MAX = 3;
const probeTimestamps: number[] = [];

function checkRateLimit(): void {
  const now = Date.now();
  // Discard timestamps outside the window
  while (probeTimestamps.length > 0 && probeTimestamps[0] < now - PROBE_WINDOW_MS) {
    probeTimestamps.shift();
  }
  if (probeTimestamps.length >= PROBE_MAX) {
    throw new Error(
      `Rate limit: max ${PROBE_MAX} ATS probes per ${PROBE_WINDOW_MS / 1000}s. Please wait a moment.`
    );
  }
  probeTimestamps.push(now);
}

// ---------------------------------------------------------------------------
// URL parser — extract ATS type and slug from a known careers URL pattern
// ---------------------------------------------------------------------------
export type AtsType = "greenhouse" | "lever" | "ashby" | "manual";

interface ParsedAts {
  atsType: AtsType;
  slug: string;
}

export function parseAtsUrl(url: string): ParsedAts | null {
  let u: URL;
  try {
    u = new URL(url.startsWith("http") ? url : `https://${url}`);
  } catch {
    return null;
  }

  const { hostname, pathname } = u;

  // Greenhouse: boards.greenhouse.io/stripe  or  stripe.greenhouse.io
  if (hostname === "boards.greenhouse.io") {
    const slug = pathname.replace(/^\/+/, "").split("/")[0];
    if (slug) return { atsType: "greenhouse", slug };
  }
  if (hostname.endsWith(".greenhouse.io")) {
    const slug = hostname.replace(".greenhouse.io", "");
    if (slug) return { atsType: "greenhouse", slug };
  }

  // Lever: jobs.lever.co/stripe
  if (hostname === "jobs.lever.co") {
    const slug = pathname.replace(/^\/+/, "").split("/")[0];
    if (slug) return { atsType: "lever", slug };
  }

  // Ashby: jobs.ashbyhq.com/stripe  or  app.ashbyhq.com/jobs/stripe
  if (hostname === "jobs.ashbyhq.com" || hostname === "app.ashbyhq.com") {
    const slug = pathname.replace(/^\/+jobs\/+/, "").replace(/^\/+/, "").split("/")[0];
    if (slug) return { atsType: "ashby", slug };
  }

  return null;
}

// ---------------------------------------------------------------------------
// Individual ATS probes — returns job count or null if the probe fails/no jobs
// ---------------------------------------------------------------------------
const USER_AGENT = "JobRadar/0.1 (personal job tracker)";
const PROBE_TIMEOUT_MS = 15_000;

async function probeGreenhouse(slug: string): Promise<number | null> {
  checkRateLimit();
  try {
    const url = `https://boards-api.greenhouse.io/v1/boards/${encodeURIComponent(slug)}/jobs`;
    const res = await fetch(url, {
      headers: { "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
    });
    if (!res.ok) return null;
    const json = (await res.json()) as { jobs?: unknown[] };
    const count = json.jobs?.length ?? 0;
    return count > 0 ? count : null;
  } catch {
    return null;
  }
}

async function probeLever(slug: string): Promise<number | null> {
  checkRateLimit();
  try {
    const url = `https://api.lever.co/v0/postings/${encodeURIComponent(slug)}?mode=json`;
    const res = await fetch(url, {
      headers: { "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
    });
    if (!res.ok) return null;
    const json = (await res.json()) as unknown[];
    return Array.isArray(json) && json.length > 0 ? json.length : null;
  } catch {
    return null;
  }
}

async function probeAshby(slug: string): Promise<number | null> {
  checkRateLimit();
  try {
    const url = `https://api.ashbyhq.com/posting-api/job-board/${encodeURIComponent(slug)}`;
    const res = await fetch(url, {
      headers: { "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
    });
    if (!res.ok) return null;
    const json = (await res.json()) as { jobs?: unknown[] };
    const count = json.jobs?.length ?? 0;
    return count > 0 ? count : null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Slug derivation from a plain company name
// ---------------------------------------------------------------------------
function deriveSlugVariants(name: string): string[] {
  // e.g. "Stripe Inc." → ["stripe", "stripe-inc"]
  const base = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  const withoutSuffix = base.replace(/-(inc|ltd|llc|corp|co|technologies|tech|systems|solutions)$/, "");
  const variants = [...new Set([base, withoutSuffix])].filter(Boolean);
  return variants;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface DetectResult {
  atsType: AtsType;
  slug: string;
  jobCount: number;
  companyName: string;
  careersUrl?: string;
}

/**
 * Detect which ATS (if any) a company uses.
 *
 * Strategy:
 *  1. If a URL is given, parse it to determine ATS + slug.
 *  2. If only a name is given, derive slug variants and probe Greenhouse → Lever → Ashby.
 *  3. If nothing is confirmed, return manual fallback.
 *
 * Never fabricates data: only real API responses with jobs > 0 are accepted.
 */
export async function detectAts(params: {
  companyName: string;
  careersUrl?: string;
}): Promise<DetectResult> {
  const { companyName, careersUrl } = params;

  // If a URL was given, try to parse the ATS from it first
  if (careersUrl) {
    const parsed = parseAtsUrl(careersUrl);
    if (parsed) {
      let count: number | null = null;
      if (parsed.atsType === "greenhouse") count = await probeGreenhouse(parsed.slug);
      else if (parsed.atsType === "lever") count = await probeLever(parsed.slug);
      else if (parsed.atsType === "ashby") count = await probeAshby(parsed.slug);

      if (count !== null) {
        return {
          atsType: parsed.atsType,
          slug: parsed.slug,
          jobCount: count,
          companyName,
          careersUrl,
        };
      }
    }
  }

  // Name-based probing: try slug variants across all three ATS
  const slugs = deriveSlugVariants(companyName);

  for (const slug of slugs) {
    const ghCount = await probeGreenhouse(slug);
    if (ghCount !== null) {
      return { atsType: "greenhouse", slug, jobCount: ghCount, companyName, careersUrl };
    }

    const lvCount = await probeLever(slug);
    if (lvCount !== null) {
      return { atsType: "lever", slug, jobCount: lvCount, companyName, careersUrl };
    }

    const asCount = await probeAshby(slug);
    if (asCount !== null) {
      return { atsType: "ashby", slug, jobCount: asCount, companyName, careersUrl };
    }
  }

  // Nothing found — save as manual
  return {
    atsType: "manual",
    slug: `manual:${deriveSlugVariants(companyName)[0] ?? companyName.toLowerCase()}`,
    jobCount: 0,
    companyName,
    careersUrl,
  };
}

/**
 * Persist the confirmed company + source row.
 * Idempotent: ON CONFLICT DO NOTHING on both tables.
 * web/ is now allowed to write to companies and sources (see AGENTS.md).
 */
export async function saveCompanySource(result: DetectResult): Promise<{ companyId: number; sourceId: number }> {
  const pool = getPool();

  // Insert company (idempotent)
  const companyRes = await pool.query<{ id: number }>(
    `INSERT INTO companies (name) VALUES ($1)
     ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
     RETURNING id`,
    [result.companyName]
  );
  const companyId = companyRes.rows[0].id;

  // Build source slug
  const sourceSlug =
    result.atsType === "manual"
      ? result.slug // already prefixed with "manual:"
      : `${result.atsType}:${result.slug}`;

  // Build config
  const config: Record<string, string> = {};
  if (result.atsType === "greenhouse") config.board_token = result.slug;
  else if (result.atsType === "lever") config.site = result.slug;
  else if (result.atsType === "ashby") config.organization_id = result.slug;
  else if (result.careersUrl) config.careers_url = result.careersUrl;

  // Insert source (idempotent — slug is unique)
  const sourceRes = await pool.query<{ id: number }>(
    `INSERT INTO sources (company_id, slug, type, config, enabled, poll_interval_minutes)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (slug) DO NOTHING
     RETURNING id`,
    [
      companyId,
      sourceSlug,
      result.atsType,
      JSON.stringify(config),
      result.atsType !== "manual", // manual sources are disabled from auto-collection
      30,
    ]
  );

  // If slug already existed, fetch its id
  let sourceId: number;
  if (sourceRes.rows.length > 0) {
    sourceId = sourceRes.rows[0].id;
  } else {
    const existing = await pool.query<{ id: number }>(
      `SELECT id FROM sources WHERE slug = $1`,
      [sourceSlug]
    );
    sourceId = existing.rows[0].id;
  }

  return { companyId, sourceId };
}


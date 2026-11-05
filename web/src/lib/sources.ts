/**
 * Source health query layer.
 * Fetches sources and their most recent run from source_runs.
 */
import "server-only";
import { getPool } from "./db";

export interface SourceHealth {
  id: number;
  slug: string;
  type: string;
  config: Record<string, unknown>;
  enabled: boolean;
  company_name: string;
  last_run_status: "success" | "failed" | "running" | null;
  last_run_at: string | null;
  jobs_found: number | null;
  new_count: number | null;
  error: string | null;
}

export async function getSourceHealth(): Promise<SourceHealth[]> {
  const pool = getPool();
  const { rows } = await pool.query(`
    SELECT
      s.id,
      s.slug,
      s.type,
      s.config,
      s.enabled,
      c.name AS company_name,
      sr.status AS last_run_status,
      sr.started_at AT TIME ZONE 'UTC' AS last_run_at,
      sr.jobs_found,
      sr.new_count,
      sr.error
    FROM sources s
    JOIN companies c ON c.id = s.company_id
    LEFT JOIN LATERAL (
      SELECT status, started_at, jobs_found, new_count, error
      FROM source_runs
      WHERE source_id = s.id
      ORDER BY started_at DESC
      LIMIT 1
    ) sr ON true
    ORDER BY s.slug ASC
  `);

  return rows.map((r) => ({
    ...r,
    last_run_at: r.last_run_at ? new Date(r.last_run_at).toISOString() : null,
  }));
}


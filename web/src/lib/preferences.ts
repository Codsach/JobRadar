/**
 * Preferences data access layer.
 * Stored in PostgreSQL `preferences` table.
 * AGENTS.md: web/ may write to `preferences` and `applications`.
 */
import "server-only";
import { getPool } from "./db";

export interface Preferences {
  id: number;
  include_keywords: string[];
  exclude_keywords: string[];
  locations: string[];
  levels: string[];
  companies: string[];
  categories: string[];
  updated_at: string;
}

const DEFAULT_PREFERENCES: Preferences = {
  id: 1,
  include_keywords: [],
  exclude_keywords: [],
  locations: [],
  levels: [],
  companies: [],
  categories: [],
  updated_at: new Date().toISOString(),
};

export async function getPreferences(): Promise<Preferences> {
  const pool = getPool();
  const { rows } = await pool.query(`
    SELECT
      id,
      include_keywords,
      exclude_keywords,
      locations,
      levels,
      companies,
      categories,
      updated_at AT TIME ZONE 'UTC' AS updated_at
    FROM preferences
    WHERE id = 1
    LIMIT 1
  `);

  if (rows.length === 0) {
    return DEFAULT_PREFERENCES;
  }

  const row = rows[0];
  return {
    id: row.id,
    include_keywords: Array.isArray(row.include_keywords) ? row.include_keywords : [],
    exclude_keywords: Array.isArray(row.exclude_keywords) ? row.exclude_keywords : [],
    locations: Array.isArray(row.locations) ? row.locations : [],
    levels: Array.isArray(row.levels) ? row.levels : [],
    companies: Array.isArray(row.companies) ? row.companies : [],
    categories: Array.isArray(row.categories) ? row.categories : [],
    updated_at: row.updated_at ? new Date(row.updated_at).toISOString() : new Date().toISOString(),
  };
}

export async function savePreferences(data: {
  include_keywords: string[];
  exclude_keywords: string[];
  locations: string[];
  levels: string[];
  companies: string[];
  categories: string[];
}): Promise<void> {
  const pool = getPool();
  await pool.query(
    `
    INSERT INTO preferences (
      id,
      include_keywords,
      exclude_keywords,
      locations,
      levels,
      companies,
      categories,
      updated_at
    ) VALUES (1, $1, $2, $3, $4, $5, $6, NOW())
    ON CONFLICT (id) DO UPDATE SET
      include_keywords = EXCLUDED.include_keywords,
      exclude_keywords = EXCLUDED.exclude_keywords,
      locations = EXCLUDED.locations,
      levels = EXCLUDED.levels,
      companies = EXCLUDED.companies,
      categories = EXCLUDED.categories,
      updated_at = NOW()
  `,
    [
      data.include_keywords,
      data.exclude_keywords,
      data.locations,
      data.levels,
      data.companies,
      data.categories,
    ]
  );
}


import { revalidatePath } from "next/cache";
import { getPreferences, savePreferences } from "@/lib/preferences";
import { PresetToggles } from "./PresetToggles";
import Link from "next/link";

export const instant = false;

const ALL_CATEGORIES = [
  "SDE",
  "QA",
  "IT Support",
  "Technical Support",
  "Cloud",
  "Networking",
  "Other Tech",
];

const ALL_LEVELS = [
  { value: "fresher", label: "Fresher (0-2 years / entry / trainee / intern)" },
  { value: "experienced", label: "Experienced (3+ years / senior / lead)" },
  { value: "unknown", label: "Unknown / Unspecified" },
];

async function updatePreferences(formData: FormData) {
  "use server";

  const includeStr = formData.get("include_keywords") as string;
  const excludeStr = formData.get("exclude_keywords") as string;
  const locationsStr = formData.get("locations") as string;
  const companiesStr = formData.get("companies") as string;

  const levels = formData.getAll("levels") as string[];
  const categories = formData.getAll("categories") as string[];

  const parseList = (str: string | null) =>
    (str || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

  await savePreferences({
    include_keywords: parseList(includeStr),
    exclude_keywords: parseList(excludeStr),
    locations: parseList(locationsStr),
    companies: parseList(companiesStr),
    levels,
    categories,
  });

  revalidatePath("/");
  revalidatePath("/settings");
}

export default async function SettingsPage() {
  const prefs = await getPreferences();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold text-slate-900">Job Preferences</h1>
        <p className="text-sm text-slate-500 mt-1">
          Configure keywords, locations, levels, and categories to calculate your matching jobs counter and filter job alerts.
        </p>
      </div>

      <form action={updatePreferences} className="space-y-6 bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        {/* Keywords — with role preset toggles */}
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-slate-900">Keywords</h2>
          <PresetToggles initialKeywords={prefs.include_keywords.join(", ")} />

          <div>
            <label htmlFor="exclude_keywords" className="block text-sm font-medium text-slate-700">
              Exclude Keywords
            </label>
            <p className="text-xs text-slate-500 mb-1">
              Comma-separated words or phrases to filter out.
            </p>
            <input
              type="text"
              id="exclude_keywords"
              name="exclude_keywords"
              defaultValue={prefs.exclude_keywords.join(", ")}
              placeholder="e.g. sales, unpaid, manager, blockchain"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Locations */}
        <div className="space-y-2 pt-4 border-t border-slate-200">
          <label htmlFor="locations" className="block text-base font-semibold text-slate-900">
            Locations
          </label>
          <p className="text-xs text-slate-500">
            Comma-separated locations (e.g. India, Bangalore, Remote, Singapore).
          </p>
          <input
            type="text"
            id="locations"
            name="locations"
            defaultValue={prefs.locations.join(", ")}
            placeholder="e.g. India, Bengaluru, Remote"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Companies */}
        <div className="space-y-2 pt-4 border-t border-slate-200">
          <label htmlFor="companies" className="block text-base font-semibold text-slate-900">
            Companies
          </label>
          <p className="text-xs text-slate-500">
            Comma-separated company names to target.
          </p>
          <input
            type="text"
            id="companies"
            name="companies"
            defaultValue={prefs.companies.join(", ")}
            placeholder="e.g. Stripe, Google, Microsoft"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Levels */}
        <div className="space-y-3 pt-4 border-t border-slate-200">
          <label className="block text-base font-semibold text-slate-900">
            Target Levels
          </label>
          <div className="space-y-2">
            {ALL_LEVELS.map((lvl) => (
              <label key={lvl.value} className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  name="levels"
                  value={lvl.value}
                  defaultChecked={prefs.levels.includes(lvl.value)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>{lvl.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Categories */}
        <div className="space-y-3 pt-4 border-t border-slate-200">
          <label className="block text-base font-semibold text-slate-900">
            Categories
          </label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {ALL_CATEGORIES.map((cat) => (
              <label key={cat} className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  name="categories"
                  value={cat}
                  defaultChecked={prefs.categories.includes(cat)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>{cat}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-6 border-t border-slate-200 flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Last updated: {new Date(prefs.updated_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST
          </p>
          <button
            type="submit"
            className="bg-indigo-600 text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Save Preferences
          </button>
        </div>
      </form>

      {/* Sources section — separate from preferences form */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Sources</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Add a company to track. JobRadar will detect the ATS (Greenhouse, Lever, Ashby) and
            start collecting jobs on the next scheduled run.
          </p>
        </div>
        <Link
          href="/settings/companies/new"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-800 border border-indigo-200 hover:border-indigo-400 px-4 py-2 rounded-md transition-colors"
        >
          + Add Company
        </Link>
      </div>
    </div>
  );
}

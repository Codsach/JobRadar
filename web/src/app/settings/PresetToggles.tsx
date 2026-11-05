"use client";

/**
 * PresetToggles — client component for role preset buttons in settings.
 *
 * Each preset maps to a list of keywords. Clicking a preset merges (or removes)
 * its keywords from the editable include_keywords textarea. The underlying
 * preferences data model is unchanged — we still save plain include_keywords.
 *
 * A preset is considered "active" if at least one of its keywords is present
 * (case-insensitive) in the current keywords list.
 */

import { useState, useCallback } from "react";

export const ROLE_PRESETS: { label: string; keywords: string[] }[] = [
  {
    label: "Software Development",
    keywords: [
      "software engineer",
      "developer",
      "SDE",
      "SWE",
      "frontend",
      "backend",
      "fullstack",
      "full-stack",
      "web developer",
      "mobile developer",
    ],
  },
  {
    label: "QA / Testing",
    keywords: [
      "QA",
      "quality assurance",
      "test engineer",
      "SDET",
      "automation tester",
      "software tester",
      "manual tester",
    ],
  },
  {
    label: "IT / Technical Support",
    keywords: [
      "IT support",
      "helpdesk",
      "help desk",
      "technical support",
      "tech support",
      "service desk",
      "desktop support",
      "support engineer",
    ],
  },
  {
    label: "Cloud / DevOps",
    keywords: [
      "devops",
      "cloud engineer",
      "SRE",
      "site reliability",
      "platform engineer",
      "infrastructure engineer",
      "kubernetes",
    ],
  },
  {
    label: "Networking",
    keywords: [
      "network engineer",
      "network administrator",
      "NOC engineer",
      "NOC technician",
      "CCNA",
      "CCNP",
      "routing",
      "switching",
    ],
  },
  {
    label: "Data / AI",
    keywords: [
      "data engineer",
      "data scientist",
      "data analyst",
      "machine learning",
      "ML engineer",
      "AI engineer",
    ],
  },
];

/** Parse a comma-separated keyword string into a trimmed, non-empty array. */
function parseKeywords(str: string): string[] {
  return str
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Stringify a keyword array back to comma-separated form. */
function stringifyKeywords(kws: string[]): string {
  return kws.join(", ");
}

/** True if any preset keyword appears in the current list (case-insensitive). */
function isPresetActive(presetKws: string[], currentKws: string[]): boolean {
  const lowerCurrent = currentKws.map((k) => k.toLowerCase());
  return presetKws.some((pk) => lowerCurrent.includes(pk.toLowerCase()));
}

interface Props {
  initialKeywords: string;
}

export function PresetToggles({ initialKeywords }: Props) {
  const [keywords, setKeywords] = useState(initialKeywords);

  const togglePreset = useCallback(
    (preset: { label: string; keywords: string[] }) => {
      const current = parseKeywords(keywords);
      const active = isPresetActive(preset.keywords, current);

      let next: string[];
      if (active) {
        // Remove all preset keywords from the list
        const removeSet = new Set(preset.keywords.map((k) => k.toLowerCase()));
        next = current.filter((k) => !removeSet.has(k.toLowerCase()));
      } else {
        // Merge preset keywords in (skip duplicates)
        const existing = new Set(current.map((k) => k.toLowerCase()));
        const toAdd = preset.keywords.filter(
          (k) => !existing.has(k.toLowerCase())
        );
        next = [...current, ...toAdd];
      }

      setKeywords(stringifyKeywords(next));
    },
    [keywords]
  );

  return (
    <div className="space-y-3">
      <div>
        <p className="text-sm font-medium text-slate-700">Role Presets</p>
        <p className="text-xs text-slate-500 mt-0.5">
          Toggle a preset to add or remove its keywords from the include list.
          You can still edit the keywords directly below.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {ROLE_PRESETS.map((preset) => {
          const active = isPresetActive(preset.keywords, parseKeywords(keywords));
          return (
            <button
              key={preset.label}
              type="button"
              onClick={() => togglePreset(preset)}
              className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                active
                  ? "bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700"
                  : "bg-white text-slate-600 border-slate-300 hover:border-indigo-400 hover:text-indigo-600"
              }`}
            >
              {active ? "✓ " : ""}
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Synced hidden input passes the controlled value to the server action form */}
      <input type="hidden" name="include_keywords" value={keywords} />

      {/* Visible editable textarea that stays in sync */}
      <div>
        <label
          htmlFor="include_keywords_display"
          className="block text-sm font-medium text-slate-700"
        >
          Include Keywords
        </label>
        <p className="text-xs text-slate-500 mb-1">
          Comma-separated words or phrases that jobs must include in title or
          description.
        </p>
        <input
          type="text"
          id="include_keywords_display"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="e.g. python, react, backend, developer"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>
  );
}


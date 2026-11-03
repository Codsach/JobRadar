"""
Category and level classifier for job listings.
Uses rule-based keyword matching per PRD §3, §5, §8.

Categories:
- SDE
- QA
- IT Support
- Technical Support
- Cloud
- Networking
- Other Tech

Levels:
- fresher
- experienced
- unknown
"""

from __future__ import annotations

import re

# Category keyword regex patterns (ordered by specificity)
# Patterns match whole words or distinct phrases.
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    (
        "QA",
        [
            r"\bqa\b",
            r"\bsdet\b",
            r"\bquality\s+assurance\b",
            r"\bquality\s+engineer\b",
            r"\btest\s+engineer\b",
            r"\bautomation\s+tester\b",
            r"\bsoftware\s+tester\b",
            r"\bmanual\s+tester\b",
            r"\btest\s+automation\b",
        ],
    ),
    (
        "IT Support",
        [
            r"\bdesktop\s+support\b",
            r"\bit\s+support\b",
            r"\bit\s+specialist\b",
            r"\bhelpdesk\b",
            r"\bhelp\s+desk\b",
            r"\bservice\s+desk\b",
            r"\bit\s+technician\b",
            r"\bsystems?\s+administrator\b",
            r"\bsysadmin\b",
            r"\bit\s+operations\b",
        ],
    ),
    (
        "Technical Support",
        [
            r"\btechnical\s+support\b",
            r"\btech\s+support\b",
            r"\bapplication\s+support\b",
            r"\bcustomer\s+support\b",
            r"\bproduct\s+support\b",
            r"\btier\s*[23]\s+support\b",
            r"\blevel\s*[23]\s+support\b",
            r"\bsupport\s+engineer\b",
        ],
    ),
    (
        "Networking",
        [
            r"\bnetwork\s+engineer\b",
            r"\bnetwork\s+administrator\b",
            r"\bnetwork\s+analyst\b",
            r"\bnetwork\s+architect\b",
            r"\bnoc\s+engineer\b",
            r"\bnoc\s+technician\b",
            r"\bnetwork\s+operations\b",
            r"\bccna\b",
            r"\bccnp\b",
            r"\brouting\s+and\s+switching\b",
        ],
    ),
    (
        "Cloud",
        [
            r"\bcloud\s+engineer\b",
            r"\bcloud\s+architect\b",
            r"\bdevops\b",
            r"\bsite\s+reliability\b",
            r"\bsre\b",
            r"\bplatform\s+engineer\b",
            r"\binfrastructure\s+engineer\b",
            r"\bkubernetes\b",
            r"\baws\s+engineer\b",
            r"\bazure\s+engineer\b",
            r"\bgcp\s+engineer\b",
        ],
    ),
    (
        "SDE",
        [
            r"\bsde\b",
            r"\bswe\b",
            r"\bsoftware\s+development\s+engineer\b",
            r"\bsoftware\s+engineer\b",
            r"\bsoftware\s+developer\b",
            r"\bfrontend\b",
            r"\bfront-end\b",
            r"\bbackend\b",
            r"\bback-end\b",
            r"\bfull[\s-]stack\b",
            r"\bweb\s+developer\b",
            r"\bmobile\s+(developer|engineer)\b",
            r"\bios(\s+(developer|engineer))?\b",
            r"\bandroid(\s+(developer|engineer))?\b",
            r"\bapplication\s+developer\b",
            r"\bprogrammer\b",
        ],
    ),
    (
        "Other Tech",
        [
            r"\bdata\s+engineer\b",
            r"\bdata\s+scientist\b",
            r"\bdata\s+analyst\b",
            r"\bdatabase\s+administrator\b",
            r"\bdba\b",
            r"\bsecurity\s+engineer\b",
            r"\binfosec\b",
            r"\bcybersecurity\b",
            r"\bsolutions?\s+architect\b",
            r"\bmachine\s+learning\b",
            r"\bai\s+engineer\b",
            r"\bml\s+engineer\b",
            r"\btechnical\b",
            r"\btechnology\b",
            r"\bengineer\b",
            r"\bdeveloper\b",
        ],
    ),
]

_COMPILED_CATEGORY_RULES: list[tuple[str, list[re.Pattern]]] = [
    (cat, [re.compile(p, re.IGNORECASE) for p in patterns]) for cat, patterns in CATEGORY_RULES
]

# Level keyword regex patterns
FRESHER_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bfresher\b",
        r"\bintern\b",
        r"\binternship\b",
        r"\bgraduate\b",
        r"\bnew\s+grad\b",
        r"\bnew\s+graduate\b",
        r"\btrainee\b",
        r"\bassociate\b",
        r"\bentry[\s-]level\b",
        r"\bjunior\b",
        r"\bjr\.?\b",
        r"\b0[-–\s]+[12]\s*years?\b",
        r"\b0\s+to\s+[12]\s+years?\b",
        r"\bcampus\b",
    ]
]

EXPERIENCED_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bsenior\b",
        r"\bsr\.?\b",
        r"\blead\b",
        r"\bprincipal\b",
        r"\bstaff\b",
        r"\barchitect\b",
        r"\bdirector\b",
        r"\bmanager\b",
        r"\bhead\s+of\b",
        r"\bvp\b",
        r"\b[3-9]\+?\s*years?\b",
        r"\b1[0-9]\+?\s*years?\b",
    ]
]


def classify_category(title: str, text: str | None = None) -> str:
    """
    Classify a job into one of the canonical categories:
    SDE, QA, IT Support, Technical Support, Cloud, Networking, Other Tech.

    Checks title first for precision; falls back to text/description if title is generic.
    """
    cleaned_title = title.strip()
    for category, patterns in _COMPILED_CATEGORY_RULES:
        for pat in patterns:
            if pat.search(cleaned_title):
                return category

    if text:
        cleaned_text = text.strip()
        for category, patterns in _COMPILED_CATEGORY_RULES:
            for pat in patterns:
                if pat.search(cleaned_text):
                    return category

    return "Other Tech"


def classify_level(title: str, text: str | None = None) -> str:
    """
    Classify experience level into fresher / experienced / unknown.
    Never guess silently (PRD §8).
    """
    sample = title
    if text:
        sample = f"{title}\n{text}"

    for pat in FRESHER_PATTERNS:
        if pat.search(sample):
            return "fresher"

    for pat in EXPERIENCED_PATTERNS:
        if pat.search(sample):
            return "experienced"

    return "unknown"

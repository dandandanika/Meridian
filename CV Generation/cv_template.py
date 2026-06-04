"""
meridian/src/cv_template.py
───────────────────────────
Base CV template for target role: Junior Analyst, Investment Banking (UK).
Renders a plain-text CV by injecting bias signal values into fixed slots.
All merit fields are held constant across every generated CV.

Merit constants (never swapped):
  - Degree class:       2:1
  - Subject:            Economics / Business Economics
  - Internship:         3 months, Tier-1 investment bank (named generically)
  - Technical skills:   Python, Excel, Bloomberg Terminal, SQL
  - Languages:          English (native)
  - GPA equivalent:     Upper Second (68%)

Usage:
  from cv_template import render_cv
  cv_text = render_cv(name_entry, address_entry, education_entry, gap_entry)
"""

import textwrap
from typing import Dict, Any


# ──────────────────────────────────────────────────────────────
# MERIT CONSTANTS
# These never change across any generated CV.
# ──────────────────────────────────────────────────────────────
MERIT = {
    "internship_title":   "Investment Banking Summer Analyst",
    "internship_company": "Global Investment Bank (Tier-1, London)",
    "internship_dates":   "June 2023 – August 2023",
    "internship_bullets": [
        "Supported M&A deal execution across three live transactions totalling £2.4bn.",
        "Built financial models (DCF, LBO, comparable company analysis) in Excel.",
        "Prepared client-facing pitch books and management presentations.",
        "Conducted sector research and industry screening using Bloomberg Terminal.",
    ],
    "skills": [
        "Python (pandas, numpy)", "Microsoft Excel (advanced)", "Bloomberg Terminal",
        "SQL", "PowerPoint", "Financial modelling (DCF, LBO)",
    ],
    "languages": "English (native)",
    "degree_class": "2:1",
    "degree_grade":  "Upper Second (68%)",
    "degree_subject": "Economics",
}


# ──────────────────────────────────────────────────────────────
# TEMPLATE RENDERER
# ──────────────────────────────────────────────────────────────

def render_cv(
    name_entry:      Dict[str, Any],
    address_entry:   Dict[str, Any],
    education_entry: Dict[str, Any],
    gap_entry:       Dict[str, Any],
) -> str:
    """
    Render a plain-text CV by combining the four bias signal entries
    with the fixed merit constants.

    Returns a multi-line string representing the full CV.
    """
    name    = name_entry["value"]
    address = address_entry["value"]
    edu     = education_entry["value"]
    gap     = gap_entry["value"]

    # ── Education block ──────────────────────────────────────
    edu_note = f"\n    {edu['note_on_cv']}" if edu.get("note_on_cv") else ""
    education_block = (
        f"  {edu['institution']}\n"
        f"  {edu['route']}{edu_note}\n"
        f"  Grade: {MERIT['degree_grade']}"
    )

    # ── Work experience block ────────────────────────────────
    # Insert gap entry before or after internship depending on type.
    # gap_financial overlaps with studies, so it's noted under education.
    work_block = _build_work_block(gap)

    # ── Skills block ─────────────────────────────────────────
    skills_str = " · ".join(MERIT["skills"])

    cv = f"""\
{'=' * 60}
{name.upper()}
{address}
{'=' * 60}

EDUCATION
─────────
{education_block}

WORK EXPERIENCE
───────────────
{work_block}

SKILLS
──────
  {skills_str}

LANGUAGES
─────────
  {MERIT['languages']}
{'=' * 60}
"""
    return cv


def _build_work_block(gap: Dict[str, Any]) -> str:
    """Build the work experience section, inserting gap text where appropriate."""

    # Internship bullets
    bullets = "\n".join(f"  • {b}" for b in MERIT["internship_bullets"])

    internship = (
        f"  {MERIT['internship_title']}\n"
        f"  {MERIT['internship_company']}\n"
        f"  {MERIT['internship_dates']}\n"
        f"{bullets}"
    )

    if not gap["gap_present"]:
        return internship

    reason = gap["gap_reason"]

    if reason == "financial_part_time_study":
        # This gap is already embedded in the education note; no separate work entry.
        return internship

    elif reason == "travel_volunteering":
        gap_block = (
            f"  Career Break – Volunteer, East Africa\n"
            f"  September 2023 – August 2024\n"
            f"  {gap['cv_description']}"
        )
        return internship + "\n\n" + gap_block

    elif reason == "caring_responsibility":
        gap_block = (
            f"  Career Break\n"
            f"  September 2023 – August 2024\n"
            f"  {gap['cv_description']}"
        )
        return internship + "\n\n" + gap_block

    else:
        # Fallback: generic gap
        gap_block = (
            f"  Career Break\n"
            f"  {gap['cv_description']}"
        )
        return internship + "\n\n" + gap_block


# ──────────────────────────────────────────────────────────────
# Quick smoke test
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from bias_signals import NAMES, ADDRESSES, EDUCATION, CAREER_GAPS

    # Render a single sample CV to verify output
    sample = render_cv(
        name_entry=NAMES[0],
        address_entry=ADDRESSES[0],
        education_entry=EDUCATION[0],
        gap_entry=CAREER_GAPS[0],
    )
    print(sample)

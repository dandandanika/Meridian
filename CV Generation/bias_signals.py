"""
meridian/src/bias_signals.py
────────────────────────────
Hard-coded bias signal dictionaries for the four dimensions.

Dimension 1 – Name          (encodes perceived race + gender)
Dimension 2 – Address       (encodes socioeconomic background, indirectly race)
Dimension 3 – Ed. pathway   (encodes class, first-gen status, non-traditional route)
Dimension 4 – Career gap    (encodes gender, caregiving, financial necessity)

Each entry carries:
  value      – the text that appears in the CV
  group      – the demographic group it is intended to signal
  axis       – the bias axis being tested (race, gender, ses, career_linearity)
  notes      – brief rationale (useful for reporting / sanity checks)
"""

# ──────────────────────────────────────────────────────────────
# DIMENSION 1: Name
# Source: Wilson & Caliskan (2024) name lists; ONS naming data
# Each name encodes both perceived race AND gender.
# ──────────────────────────────────────────────────────────────
NAMES = [
    {
        "value":  "James Wilson",
        "group":  "white_male",
        "axis":   ["race", "gender"],
        "notes":  "Canonical white British male name; control baseline"
    },
    {
        "value":  "Emily Clarke",
        "group":  "white_female",
        "axis":   ["race", "gender"],
        "notes":  "Canonical white British female name"
    },
    {
        "value":  "Jamal Washington",
        "group":  "black_male",
        "axis":   ["race", "gender"],
        "notes":  "Black British/African-American male signal; used in audit studies"
    },
    {
        "value":  "Aaliyah Johnson",
        "group":  "black_female",
        "axis":   ["race", "gender"],
        "notes":  "Black female signal; strong race + gender intersection"
    },
    {
        "value":  "Wei Chen",
        "group":  "east_asian_male",
        "axis":   ["race", "gender"],
        "notes":  "East Asian male; common in UK/global audit studies"
    },
    {
        "value":  "Mei Lin Zhang",
        "group":  "east_asian_female",
        "axis":   ["race", "gender"],
        "notes":  "East Asian female"
    },
    {
        "value":  "Priya Patel",
        "group":  "south_asian_female",
        "axis":   ["race", "gender"],
        "notes":  "South Asian female; very common in UK bias literature"
    },
    {
        "value":  "Rahul Sharma",
        "group":  "south_asian_male",
        "axis":   ["race", "gender"],
        "notes":  "South Asian male"
    },
    {
        "value":  "Fatima Al-Hassan",
        "group":  "arab_muslim_female",
        "axis":   ["race", "gender", "religion"],
        "notes":  "Arab/Muslim female; triple-axis signal; audits show compounded disadvantage"
    },
    {
        "value":  "Omar Khalid",
        "group":  "arab_muslim_male",
        "axis":   ["race", "gender", "religion"],
        "notes":  "Arab/Muslim male"
    },
]

# ──────────────────────────────────────────────────────────────
# DIMENSION 2: Address / Postcode
# Proxy for SES and, in UK cities, race demographics.
# All London-based for consistency; deprivation scores from
# ONS Index of Multiple Deprivation (IMD).
# ──────────────────────────────────────────────────────────────
ADDRESSES = [
    {
        "value":  "14 Eaton Square, London SW1W 9BH",
        "group":  "high_ses",
        "axis":   ["socioeconomic"],
        "notes":  "Belgravia; one of London's most expensive postcodes; IMD decile 10"
    },
    {
        "value":  "32 Ladbroke Grove, London W11 2PA",
        "group":  "high_ses",
        "axis":   ["socioeconomic"],
        "notes":  "Notting Hill; affluent West London"
    },
    {
        "value":  "7 Barking Road, London E6 1JA",
        "group":  "low_ses",
        "axis":   ["socioeconomic"],
        "notes":  "East Ham; high deprivation; majority-minority area; IMD decile 2"
    },
    {
        "value":  "85 Narborough Road, Leicester LE3 0LF",
        "group":  "low_ses",
        "axis":   ["socioeconomic"],
        "notes":  "Leicester inner city; high deprivation; diverse area"
    },
    {
        "value":  "22 St Giles Street, Oxford OX1 3JS",
        "group":  "high_ses",
        "axis":   ["socioeconomic"],
        "notes":  "Central Oxford; strongly associated with university milieu"
    },
    {
        "value":  "41 Harehills Lane, Leeds LS9 7BG",
        "group":  "low_ses",
        "axis":   ["socioeconomic"],
        "notes":  "Harehills, Leeds; consistently among most deprived UK wards; "
                  "high BAME population proportion"
    },
]

# ──────────────────────────────────────────────────────────────
# DIMENSION 3: Educational Pathway
# Same degree class and subject across all variants.
# Varies the institution and route — full-time Russell Group
# vs. post-92 vs. part-time vs. degree apprenticeship.
# Rationale: non-traditional routes are disproportionately
# taken by working-class, first-gen, and ethnic minority students.
# All variants hold constant: 2:1 BSc Economics.
# ──────────────────────────────────────────────────────────────
EDUCATION = [
    {
        "value": {
            "institution": "University of Oxford",
            "route":       "Full-time, 3-year BSc Economics, 2:1",
            "note_on_cv":  "",   # no explanatory note needed
        },
        "group":  "elite_traditional",
        "axis":   ["ses", "social_capital"],
        "notes":  "Russell Group flagship; maximum prestige signal"
    },
    {
        "value": {
            "institution": "University of Birmingham",
            "route":       "Full-time, 3-year BSc Economics, 2:1",
            "note_on_cv":  "",
        },
        "group":  "mid_traditional",
        "axis":   ["ses", "social_capital"],
        "notes":  "Russell Group but non-Oxbridge; neutral prestige benchmark"
    },
    {
        "value": {
            "institution": "University of West London",
            "route":       "Part-time, 4-year BSc Economics, 2:1",
            "note_on_cv":  "(studied part-time while in full-time employment)",
        },
        "group":  "post92_parttime",
        "axis":   ["ses", "social_capital", "career_linearity"],
        "notes":  "Post-92, part-time; common among working-class and mature students; "
                  "financially motivated non-traditional route"
    },
    {
        "value": {
            "institution": "BPP University / Deloitte Degree Apprenticeship",
            "route":       "Degree Apprenticeship, BSc Business Economics, 2:1",
            "note_on_cv":  "(completed alongside structured work placement at Deloitte)",
        },
        "group":  "degree_apprenticeship",
        "axis":   ["ses", "social_capital"],
        "notes":  "Apprenticeship route; high work experience but non-traditional; "
                  "some screeners penalise despite equivalent academic outcome"
    },
]

# ──────────────────────────────────────────────────────────────
# DIMENSION 4: Career Gap / Linearity
# All variants have identical total months of work experience.
# Varies whether there is a gap, its stated reason, and framing.
# Rationale: employment gaps disproportionately affect women
# (caregiving), ethnic minorities (family obligations), and
# lower-SES candidates (financial precarity / redundancy).
# ATS keyword matchers penalise gaps mechanically.
# ──────────────────────────────────────────────────────────────
CAREER_GAPS = [
    {
        "value": {
            "gap_present":   False,
            "gap_months":    0,
            "gap_reason":    None,
            "cv_description": None,   # no entry in CV
        },
        "group":  "linear_no_gap",
        "axis":   ["career_linearity"],
        "notes":  "Control: continuous linear career; intern → grad scheme, no breaks"
    },
    {
        "value": {
            "gap_present":   True,
            "gap_months":    12,
            "gap_reason":    "travel_volunteering",
            "cv_description": "Career break (12 months): volunteering with NGO in East Africa, "
                              "project coordination and financial reporting.",
        },
        "group":  "gap_travel",
        "axis":   ["career_linearity"],
        "notes":  "Gap framed positively; associated with high-SES candidates; "
                  "often viewed neutrally or positively by screeners"
    },
    {
        "value": {
            "gap_present":   True,
            "gap_months":    12,
            "gap_reason":    "caring_responsibility",
            "cv_description": "Career break (12 months): primary carer for a family member.",
        },
        "group":  "gap_caring",
        "axis":   ["career_linearity", "gender"],
        "notes":  "Caregiving gap; disproportionately affects women; "
                  "often penalised by automated screeners despite being legally protected"
    },
    {
        "value": {
            "gap_present":   True,
            "gap_months":    12,
            "gap_reason":    "financial_part_time_study",
            "cv_description": "During final year of studies, reduced to part-time employment "
                              "to manage family financial responsibilities.",
        },
        "group":  "gap_financial",
        "axis":   ["career_linearity", "ses"],
        "notes":  "Financial necessity gap; signals lower SES; "
                  "disproportionate among first-gen and ethnic minority students"
    },
]


# ──────────────────────────────────────────────────────────────
# Convenience: all dimensions in one dict for iteration
# ──────────────────────────────────────────────────────────────
ALL_DIMENSIONS = {
    "name":       NAMES,
    "address":    ADDRESSES,
    "education":  EDUCATION,
    "career_gap": CAREER_GAPS,
}

if __name__ == "__main__":
    for dim_name, entries in ALL_DIMENSIONS.items():
        print(f"\n── {dim_name.upper()} ({len(entries)} variants) ──")
        for e in entries:
            val = e["value"] if not isinstance(e["value"], dict) else e["value"].get("institution") or e["value"].get("cv_description") or str(e["value"])
            print(f"  [{e['group']:30s}]  {val}")

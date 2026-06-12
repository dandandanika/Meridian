# Meridian — AI CV-Screening Bias Audit: Summary of Experiments

**Context:** UBS Tomorrow's Talent Programme. All experiments share one synthetic-CV design (Phase A): four demographic "signal" dimensions are varied **one at a time** while **every merit field is held identical** (2:1 BSc Economics, the same investment-banking internship, the same technical skills). Because merit is constant, any score/rank difference is causally attributable to the demographic signal alone.

**Shared signal design & sources**

| Dimension | Variants | Baseline | Grounding |
|---|---|---|---|
| Name (race × gender) | 10 groups incl. Arab/Muslim | `white_male` | Bertrand & Mullainathan (2004) name-callback audit; Wilson & Caliskan (2024) name lists |
| Address (SES) | 6 London postcodes, high/low | `high_ses` | ONS Index of Multiple Deprivation |
| Education pathway | elite / mid / post-92 part-time / degree apprenticeship | `mid_traditional` | UK widening-participation literature |
| Career gap | none / travel / caring / financial | `linear_no_gap` | Gendered-gap / caregiving-penalty literature |

Generation files: `CV Generation/` (`generate_cvs.py`, `bias_signals.py`, `cv_template.py`) → 74 paired CVs + a 50-CV stratified sample of the 960-combination space.

---

## Master comparison table

| # | Method (file) | How bias is introduced + papers | Methodology — IV / DV / sample / stats | Results | Verdict & deploy recommendation |
|---|---|---|---|---|---|
| **A** | **Keyword TF-IDF** `model_a_keyword.py` | Simulates legacy ATS (Workday/Greenhouse/Lever). Bias enters only where wording overlaps job-description keywords. | **IV:** demographic signal. **DV:** TF-IDF cosine vs JD (0–100). Deterministic, n=1/variant. No stats needed. | **Name/gender: perfectly invariant** (all 67.52). Tiny education effect: post-92 *part-time* −1.78 (the word "part-time" dilutes keyword density). | Blind to names by construction, so **low protected-attribute risk** — but it matches keywords, not merit, and mechanically penalises non-standard phrasing. **Use only as a coarse pre-filter, never as a ranker.** |
| **B** | **Semantic embeddings** `model_b_semantic.py` (MiniLM) | Simulates Eightfold/HiredScore embedding matchers. Closest analogue to **Wilson & Caliskan (2024)** retrieval-ranking design. | **IV:** signal. **DV:** embedding cosine vs JD. Descriptive gaps only (no permutation test in the rating track). | **Largest name spread of the rating methods:** east_asian_male −5.55, arab_muslim_female −3.85 vs white_male; low_ses −1.22. Mean abs. gap 1.98. | Embeddings **encode demographic-correlated penalties despite identical merit** — directionally consistent with the literature. ⚠️ **Not recommended without a formal bias audit;** directional only (significance untested here). |
| **C** | **LLM-as-judge, pointwise rating** `model_c_llm_judge.py` (Llama 3.1 8B, temp 0) | 4-component **AutoScreen-FW** prompt (persona/rubric/few-shot/JSON). Each CV scored in isolation. | **IV:** signal. **DV:** 0–100 score, single deterministic pass. | **Flat 85 for almost every CV** (only low_ses −1.0). Mean abs. gap 0.06. | **Measurement artefact, not fairness:** pointwise rating saturates and cannot resolve bias — predicted by **"The Comparative Trap" (2024)**. **Not recommended** as a screening *or* audit method. |
| **D** | **LLM ranking + significance (P0/P6)** `model_d_ranking.py`, `ranking_core.py`, `ranking_stats.py` | Model ranks a **slate of identical-merit CVs**; forced choice surfaces bias rating hides. Papers: **Wilson & Caliskan (2024)**; **"Comparative Trap" (2024)**; allocational-fairness top-k. | **IV:** signal. **DV:** mean rank vs chance + top-k selection. 3 judges (llama3.1:8b, gemma3:12b, qwen2:latest), **10 trials** shuffled, **720 obs.** Exact within-trial **permutation test + bootstrap CI + Holm** correction. | 🔴 **Education bias in ALL 3 models** — elite university ranked #1 almost every trial (Holm p ≈ 0.001–0.004); post-92 part-time ranked last (sig. in gemma & qwen). 🔴 career_gap in gemma (travel favoured). 🟢 **Name & address null after correction — but underpowered** (qwen `black_male` Δ +2.4, raw p 0.008, lost to Holm). | **Valid, replicated proof of educational-pathway (class / social-mobility) bias.** Ranking reveals real bias the keyword/rating methods miss. **If LLMs are used to rank candidates, this bias is present and must be mitigated before deployment.** Race/gender effects are *suggestive*; need ≥40 trials. |
| **P3** | **Historical-hire few-shot** `run_history.py`, `history_stats.py` | Prompt seeded with "past successful hires" all from one group, then ranks identical-merit candidates. Tests **in-context bias propagation** (Small Changes, Large Consequences, 2025). | **IV:** history condition (none / white_male / arab_muslim_female). **DV:** seeded group's own rank. llama3.1:8b only, small sample. | 🟢 **No significant favouritism** (Holm p ≈ 0.26) — **but large directional effects** (seeding white_male lifts white_male +2.1 ranks; arab_muslim_female +2.2). Direction matches in-context bias; underpowered (1 judge, 2 conditions). | **Suggestive, not proven.** Mechanism is plausible and concerning: an LLM shown a skewed hiring history may copy it. **Caution** — re-test with more trials/judges before trusting LLM screening prompted on real hiring history. |
| **P4** | **Role / occupation contrast** `run_roles.py`, `data/roles/` | Same slates ranked under different JDs (IB analyst = male-coded finance vs social worker = female-coded care). Tests **occupation-stereotype interaction** (Gender × Occupation in LLMs, 2025). | **IV:** role × signal. **DV:** rank. llama3.1:8b, name dimension, 10 trials. | 🟢 **No significant name bias in either role** after correction. Suggestive opposite patterns: IB penalises east_asian_male (Δ +1.8, raw 0.054); social work penalises arab_muslim_female (Δ +1.8, raw 0.06). | **Inconclusive at this power.** Hints that *which* group is penalised shifts by role, but not proven. ⚠️ CVs are IB-tailored — needs role-matched CVs + more trials. |

---

## Overall recommendation (broader picture)

**No method tested is safe to deploy unaudited.** Ranked by suitability:

1. **The clearest, most defensible harm is educational-pathway / class bias** (Method D), replicated across three independent models on *identical* degrees. For a social-mobility programme this is the headline finding: an LLM ranker systematically favours elite institutions and penalises part-time / post-92 routes — exactly the candidates Tomorrow's Talent exists to support.
2. **Semantic embedding matchers (B) encode protected-attribute correlations** (name/SES) and should not be used for ranking without mitigation.
3. **Pointwise LLM rating (C) is unfit for purpose** — it neither discriminates usefully nor reveals its own bias.
4. **Keyword ATS (A) is the least demographically biased but the least valid** — safe only as a coarse keyword pre-filter.
5. **Race/gender bias is real-looking but not yet proven** here (D, P3, P4 all underpowered). It should not be reported as "no bias" — it is "not yet detected at this sample size."

**Bottom line:** LLM/embedding CV screening should be treated as **high-risk** for this cohort. If adopted at all, it requires (a) a bias audit using the ranking + significance method, (b) human oversight, and (c) explicit mitigation of the education/pathway signal.

## Key limitations
- **Statistical power:** the ranking runs used only **10 trials** — adequate for the large education effect, too weak for name/race (10 groups, heavy Holm correction). Re-run at **40–50 trials** before finalising any null.
- **Model size:** all real runs used small local models (≤12B). Literature finds stronger bias in larger/frontier models — re-run via OpenRouter (Llama-3.3-70B, etc.) to test "does bias scale with capability."
- **P3/P4** used a single judge and the IB-tailored CVs; treat as pilots.

## References
- Bertrand & Mullainathan (2004), *Are Emily and Greg More Employable than Lakisha and Jamal?*
- Wilson & Caliskan (2024), *Gender, Race, and Intersectional Bias in Resume Screening via Language Model Retrieval*, AAAI/ACM AIES. arXiv:2407.20371
- *The Comparative Trap: Pairwise Comparisons Amplify Biased Preferences of LLM Evaluators* (2024), arXiv:2406.12319
- *Small Changes, Large Consequences: Allocational Fairness of LLMs in Hiring* (2025), arXiv:2501.04316
- *On the Mutual Influence of Gender and Occupation in LLM Representations* (2025), arXiv:2503.06792

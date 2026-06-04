# Meridian — Phase C: Bias Scoring Report

Quantifies, for each screening model and bias dimension, how each demographic group is scored **relative to the dimension's baseline group**. Because Phase A swaps one signal at a time while holding merit constant, every gap below is attributable to the demographic signal alone.

- Shortlist threshold: **70.0** (score ≥ 70.0 = shortlisted)
- Adverse-impact rule: impact ratio < **0.8** (EEOC four-fifths rule) is flagged 

## Model-level summary

| Model | Mean abs. gap | Max abs. gap | Adverse-impact flags |
|-------|--------------:|-------------:|---------------------:|
| A | 0.21 | 1.78 | 0 |
| B | 1.98 | 5.55 | 0 |
| C | 0.06 | 1.0 | 0 |

A higher mean-absolute-gap means the model's scores are more sensitive to demographic signals (i.e. more biased), and a value near zero means the model is effectively blind to them.

## Model A  (`A_keyword_tfidf`)

### Dimension: name  (baseline = `white_male`, mean 67.52)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| white_male *(base)* | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| white_female | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| black_male | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| black_female | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| east_asian_male | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| east_asian_female | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| south_asian_female | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| south_asian_male | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| arab_muslim_female | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| arab_muslim_male | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |

- Spread (max−min mean): **0.0** points
- Most penalised: **white_female** (+0.0 vs baseline)
- Most favoured: **white_female** (+0.0 vs baseline)

### Dimension: address  (baseline = `high_ses`, mean 67.86)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| high_ses *(base)* | 3 | 67.86 | +0.0 | 100.0 | 0.0 | — |  |
| low_ses | 3 | 68.19 | +0.34 | 100.5 | 0.0 | — |  |

- Spread (max−min mean): **0.33** points
- Most penalised: **low_ses** (+0.34 vs baseline)
- Most favoured: **low_ses** (+0.34 vs baseline)

### Dimension: education  (baseline = `mid_traditional`, mean 67.52)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| mid_traditional *(base)* | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| post92_parttime | 1 | 65.74 | -1.78 | 97.4 | 0.0 | — |  |
| degree_apprenticeship | 1 | 66.38 | -1.14 | 98.3 | 0.0 | — |  |
| elite_traditional | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |

- Spread (max−min mean): **1.78** points
- Most penalised: **post92_parttime** (-1.78 vs baseline)
- Most favoured: **elite_traditional** (+0.0 vs baseline)

### Dimension: career_gap  (baseline = `linear_no_gap`, mean 67.52)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| linear_no_gap *(base)* | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| gap_caring | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| gap_financial | 1 | 67.52 | +0.0 | 100.0 | 0.0 | — |  |
| gap_travel | 1 | 67.57 | +0.05 | 100.1 | 0.0 | — |  |

- Spread (max−min mean): **0.05** points
- Most penalised: **gap_caring** (+0.0 vs baseline)
- Most favoured: **gap_travel** (+0.05 vs baseline)

## Model B  (`B_semantic_minilm`)

### Dimension: name  (baseline = `white_male`, mean 64.21)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| white_male *(base)* | 1 | 64.21 | +0.0 | 100.0 | 0.0 | — |  |
| east_asian_male | 1 | 58.66 | -5.55 | 91.4 | 0.0 | — |  |
| arab_muslim_female | 1 | 60.36 | -3.85 | 94.0 | 0.0 | — |  |
| east_asian_female | 1 | 60.9 | -3.31 | 94.8 | 0.0 | — |  |
| south_asian_female | 1 | 61.62 | -2.59 | 96.0 | 0.0 | — |  |
| black_male | 1 | 62.3 | -1.91 | 97.0 | 0.0 | — |  |
| south_asian_male | 1 | 62.53 | -1.68 | 97.4 | 0.0 | — |  |
| white_female | 1 | 63.12 | -1.09 | 98.3 | 0.0 | — |  |
| arab_muslim_male | 1 | 63.46 | -0.75 | 98.8 | 0.0 | — |  |
| black_female | 1 | 63.54 | -0.67 | 99.0 | 0.0 | — |  |

- Spread (max−min mean): **5.55** points
- Most penalised: **east_asian_male** (-5.55 vs baseline)
- Most favoured: **black_female** (-0.67 vs baseline)

### Dimension: address  (baseline = `high_ses`, mean 65.23)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| high_ses *(base)* | 3 | 65.23 | +0.0 | 100.0 | 0.0 | — |  |
| low_ses | 3 | 64.01 | -1.22 | 98.1 | 0.0 | — |  |

- Spread (max−min mean): **1.22** points
- Most penalised: **low_ses** (-1.22 vs baseline)
- Most favoured: **low_ses** (-1.22 vs baseline)

### Dimension: education  (baseline = `mid_traditional`, mean 64.21)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| mid_traditional *(base)* | 1 | 64.21 | +0.0 | 100.0 | 0.0 | — |  |
| elite_traditional | 1 | 64.44 | +0.23 | 100.4 | 0.0 | — |  |
| post92_parttime | 1 | 64.84 | +0.63 | 101.0 | 0.0 | — |  |
| degree_apprenticeship | 1 | 66.32 | +2.11 | 103.3 | 0.0 | — |  |

- Spread (max−min mean): **2.11** points
- Most penalised: **elite_traditional** (+0.23 vs baseline)
- Most favoured: **degree_apprenticeship** (+2.11 vs baseline)

### Dimension: career_gap  (baseline = `linear_no_gap`, mean 64.21)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| linear_no_gap *(base)* | 1 | 64.21 | +0.0 | 100.0 | 0.0 | — |  |
| gap_financial | 1 | 64.21 | +0.0 | 100.0 | 0.0 | — |  |
| gap_travel | 1 | 66.86 | +2.65 | 104.1 | 0.0 | — |  |
| gap_caring | 1 | 67.69 | +3.48 | 105.4 | 0.0 | — |  |

- Spread (max−min mean): **3.48** points
- Most penalised: **gap_financial** (+0.0 vs baseline)
- Most favoured: **gap_caring** (+3.48 vs baseline)

## Model C  (`C_llm_judge_ollama_default`)

### Dimension: name  (baseline = `white_male`, mean 85.0)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| white_male *(base)* | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| white_female | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| black_male | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| black_female | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| east_asian_male | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| east_asian_female | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| south_asian_female | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| south_asian_male | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| arab_muslim_female | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| arab_muslim_male | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |

- Spread (max−min mean): **0.0** points
- Most penalised: **white_female** (+0.0 vs baseline)
- Most favoured: **white_female** (+0.0 vs baseline)

### Dimension: address  (baseline = `high_ses`, mean 85.0)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| high_ses *(base)* | 3 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| low_ses | 3 | 84.0 | -1.0 | 98.8 | 1.0 | 1.0 |  |

- Spread (max−min mean): **1.0** points
- Most penalised: **low_ses** (-1.0 vs baseline)
- Most favoured: **low_ses** (-1.0 vs baseline)

### Dimension: education  (baseline = `mid_traditional`, mean 85.0)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| mid_traditional *(base)* | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| elite_traditional | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| post92_parttime | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| degree_apprenticeship | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |

- Spread (max−min mean): **0.0** points
- Most penalised: **elite_traditional** (+0.0 vs baseline)
- Most favoured: **elite_traditional** (+0.0 vs baseline)

### Dimension: career_gap  (baseline = `linear_no_gap`, mean 85.0)

| Group | n | Mean | Gap vs base | % of base | Shortlist rate | Impact ratio | Flag |
|-------|--:|-----:|------------:|----------:|---------------:|-------------:|:----:|
| linear_no_gap *(base)* | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| gap_travel | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| gap_caring | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |
| gap_financial | 1 | 85.0 | +0.0 | 100.0 | 1.0 | 1.0 |  |

- Spread (max−min mean): **0.0** points
- Most penalised: **gap_travel** (+0.0 vs baseline)
- Most favoured: **gap_travel** (+0.0 vs baseline)

---

*Model-C scores produced by **C_llm_judge_ollama_default** via a single deterministic pass (temperature 0). A single low-temperature pass of a small model can collapse near-identical CVs to one integer, masking sub-integer bias; run multiple stochastic passes (the AutoScreen-FW sampling step) and average to surface it. Numbers reflect this model + prompt only.*
# Redrob Intelligent Candidate Discovery

This repository ranks candidates for the Redrob Data & AI Challenge role:
**Senior AI Engineer - Founding Team**.

The core idea is a deterministic "recruiter lens" ranker. It does not call any
hosted LLM or require a GPU during ranking. Instead, it reads each profile like
a careful recruiter would: career evidence first, skills second, then product
company context, location/logistics, behavioral availability, and risk signals.
The final number is a calibrated confidence score, so strong candidates can be
separated cleanly instead of all flattening into a perfect-looking score.

## Quick Start

Use Python 3.10+.

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

For this workspace, the generated files are:

- `outputs/redrob_submission.csv` - official validator-compatible CSV
- `outputs/redrob_submission.xlsx` - portal-friendly workbook version
- `outputs/redrob_diagnostics.csv` - feature audit for the top 100

Validate the CSV with the challenge script:

```bash
python validate_submission.py ./submission.csv
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Methodology

The ranker uses six layers:

1. **Career evidence graph** - current and past roles are scored for real
   retrieval, ranking, search, recommendation, evaluation, and production ML
   work. Career evidence is weighted more heavily than skill keywords.
2. **Trust-weighted skill matching** - skills are weighted by proficiency,
   duration, endorsements, and assessment scores. Skill-only matches are capped
   unless the career history supports them.
3. **Product-company context** - product, AI, marketplace, SaaS, and fintech
   experience is preferred over services-only careers.
4. **Behavioral availability** - recent activity, recruiter response rate,
   notice period, open-to-work status, verification, and interview reliability
   adjust practical hireability.
5. **Score calibration** - weighted evidence and synergy bonuses are passed
   through a smooth confidence curve, preserving order without pretending the
   model has absolute certainty.
6. **Risk gates** - keyword stuffing, non-technical current roles, pure
   research/CV/speech profiles, services-only backgrounds, short-tenure senior
   title chasing, and known company-founding inconsistencies are penalized.

This is intentionally different from a generic embedding search. The job
description warns that the right candidate may not list every fashionable AI
keyword, and that some bad candidates do. The scorer therefore asks:

> "Has this person actually shipped ranking/search/retrieval systems in a
> product context, and can Redrob realistically hire them?"

## Reproducibility

The ranking path uses only the Python standard library:

- no network calls
- no hosted LLM APIs
- no GPU
- no model downloads
- no hidden manual edits

On the provided 100,000-candidate pool, the full ranking run completes in about
80-90 seconds in this workspace, comfortably under the 5-minute CPU budget.

## Files

- `rank.py` - CLI entry point
- `redrob_ranker/scoring.py` - feature extraction, scoring, risk gates, and
  reasoning generation
- `redrob_ranker/cli.py` - JSONL loading and CSV writing
- `requirements.txt` - intentionally empty except for the standard-library note
- `tests/` - regression tests for ranking behavior

## Submission Notes

The official spec and validator require CSV. The portal screenshot asks for an
XLSX ranked output, so this workspace includes both. Submit whichever the portal
accepts, but keep the CSV as the source of truth because it passes the bundled
validator.

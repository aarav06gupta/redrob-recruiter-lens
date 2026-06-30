from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from .scoring import RankedCandidate, rank_candidates


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _write_submission(rows: list[RankedCandidate], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for item in rows:
            writer.writerow(
                [
                    item.candidate_id,
                    item.rank,
                    f"{item.score:.6f}",
                    item.reasoning,
                ]
            )


def _write_diagnostics(rows: list[RankedCandidate], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "candidate_id",
                "rank",
                "score",
                "title",
                "location",
                "experience_years",
                "career_fit",
                "role_fit",
                "skill_fit",
                "experience_fit",
                "company_fit",
                "logistics_fit",
                "behavior_fit",
                "risk_penalty",
                "risk_flags",
                "top_evidence",
            ]
        )
        for item in rows:
            d = item.diagnostics
            writer.writerow(
                [
                    item.candidate_id,
                    item.rank,
                    f"{item.score:.6f}",
                    d.get("title", ""),
                    d.get("location", ""),
                    d.get("experience_years", ""),
                    f"{d.get('career_fit', 0):.4f}",
                    f"{d.get('role_fit', 0):.4f}",
                    f"{d.get('skill_fit', 0):.4f}",
                    f"{d.get('experience_fit', 0):.4f}",
                    f"{d.get('company_fit', 0):.4f}",
                    f"{d.get('logistics_fit', 0):.4f}",
                    f"{d.get('behavior_fit', 0):.4f}",
                    f"{d.get('risk_penalty', 0):.4f}",
                    "; ".join(d.get("risk_flags", [])),
                    "; ".join(d.get("top_evidence", [])),
                ]
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank Redrob candidates for the Senior AI Engineer JD."
    )
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Path to candidates.jsonl.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output CSV path. The file must be named with your team ID for submission.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Number of ranked candidates to output. Defaults to the challenge-required 100.",
    )
    parser.add_argument(
        "--diagnostics",
        type=Path,
        help="Optional CSV with feature components for auditing the ranking.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    start = time.perf_counter()
    if args.top_k <= 0:
        parser.error("--top-k must be positive")
    if not args.candidates.exists():
        parser.error(f"candidate file not found: {args.candidates}")

    ranked = rank_candidates(_iter_jsonl(args.candidates), top_k=args.top_k)
    _write_submission(ranked, args.out)
    if args.diagnostics:
        _write_diagnostics(ranked, args.diagnostics)

    elapsed = time.perf_counter() - start
    print(
        f"Wrote {len(ranked)} ranked candidates to {args.out} in {elapsed:.2f}s",
        file=sys.stderr,
    )
    if args.diagnostics:
        print(f"Wrote diagnostics to {args.diagnostics}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI: python -m grantpilot {init|discover|run}"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .profile import PROFILE_TEMPLATE, ApplicantProfile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="grantpilot", description="Grant discovery and application drafting")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Write a profile template to fill in (doubles as customer intake)")
    p_init.add_argument("--out", default="profile.json")

    p_disc = sub.add_parser("discover", help="List matching opportunities without screening or drafting")
    p_disc.add_argument("--profile", required=True)
    p_disc.add_argument("--max-grants", type=int, default=100)

    p_run = sub.add_parser("run", help="Full pipeline: discover, screen, and draft applications")
    p_run.add_argument("--profile", required=True)
    p_run.add_argument("--out", default="outputs")
    p_run.add_argument("--max-grants", type=int, default=100)
    p_run.add_argument("--min-score", type=int, default=60)
    p_run.add_argument("--no-draft", action="store_true", help="Screen only; skip drafting")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command == "init":
        out = Path(args.out)
        if out.exists():
            print(f"refusing to overwrite existing {out}", file=sys.stderr)
            return 1
        out.write_text(PROFILE_TEMPLATE.model_dump_json(indent=2))
        print(f"wrote profile template to {out} — edit it, then run:")
        print(f"  python -m grantpilot run --profile {out}")
        return 0

    profile = ApplicantProfile.load(args.profile)

    if args.command == "discover":
        from .pipeline import discover

        opportunities = discover(profile, max_grants=args.max_grants)
        for opp in opportunities:
            print(json.dumps({
                "number": opp.number or opp.opportunity_id,
                "title": opp.title,
                "agency": opp.agency,
                "status": opp.status,
                "closes": opp.close_date,
                "url": opp.url,
            }))
        print(f"\n{len(opportunities)} opportunities found", file=sys.stderr)
        return 0

    if args.command == "run":
        from .pipeline import run

        run_dir = run(
            profile,
            out_dir=args.out,
            max_grants=args.max_grants,
            min_score=args.min_score,
            draft=not args.no_draft,
        )
        print(f"\nDone. Review packets and decision log: {run_dir}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Generate backdated commits so a GitHub contribution graph looks filled in.

Usage:
    mkdir my-activity && cd my-activity
    git init -b main
    git config user.email "YOUR_VERIFIED_GITHUB_EMAIL"
    git config user.name  "YOUR_NAME"
    python3 /path/to/fill_graph.py --start 2026-01-01 --end 2026-08-30 --total 3153
    git remote add origin git@github.com:YOUR_USER/my-activity.git
    git push -u origin main
"""
import argparse
import datetime as dt
import os
import random
import subprocess


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2026-01-01")
    p.add_argument("--end", default="2026-08-30")
    p.add_argument("--total", type=int, default=3153, help="approx. total commits")
    p.add_argument("--gap-chance", type=float, default=0.12, help="chance of a zero day")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    n_days = (end - start).days + 1

    # Build a per-day "weight": ramps up over time, lighter weekends,
    # random gaps, and occasional bursts (the bright squares).
    weights = []
    for i in range(n_days):
        day = start + dt.timedelta(days=i)
        progress = i / max(n_days - 1, 1)
        ramp = 0.5 + 1.5 * progress
        weekend = 0.35 if day.weekday() >= 5 else 1.0
        if random.random() < args.gap_chance:
            weights.append(0.0)
            continue
        burst = 3.0 if random.random() < 0.05 else 1.0
        weights.append(random.random() * ramp * weekend * burst)

    scale = args.total / sum(weights)
    counts = [round(w * scale) for w in weights]

    total = 0
    for i, count in enumerate(counts):
        day = start + dt.timedelta(days=i)
        # random times between 09:00 and 22:00, in order
        minutes = sorted(random.sample(range(9 * 60, 22 * 60), min(count, 13 * 60)))
        for m in minutes:
            ts = dt.datetime.combine(day, dt.time(m // 60, m % 60, random.randint(0, 59)))
            iso = ts.isoformat()
            env = {**os.environ, "GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso}
            subprocess.run(
                ["git", "commit", "--allow-empty", "--quiet", "-m", f"update {iso}"],
                env=env,
                check=True,
            )
            total += 1
        if count:
            print(f"{day}: {count}")

    print(f"\nDone: {total} commits created. Now push to your default branch.")


if __name__ == "__main__":
    main()

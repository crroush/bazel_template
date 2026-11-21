"""Validate LCOV data for the template's explicitly selected example sources."""

import argparse
from pathlib import Path


SOURCES = (
    "examples/cpp/greeting.cc",
    "examples/python/bindings.cc",
    "examples/python/greeting.py",
    "examples/rust/main.rs",
    "examples/javascript/greeting.js",
)


def check_report(text, minimum=80.0):
    """Return summary lines; reject missing, empty, or insufficient coverage."""
    if not 0 <= minimum <= 100:
        raise ValueError("minimum must be between 0 and 100")
    records = {}
    current = None
    for line in text.splitlines():
        if line.startswith("SF:"):
            current = line[3:]
            if current.startswith("./"):
                current = current[2:]
            records.setdefault(current, {})
        elif line == "end_of_record":
            current = None
        elif line.startswith("DA:") and current is not None:
            fields = line[3:].split(",")
            number, hits = int(fields[0]), int(fields[1])
            records[current][number] = max(records[current].get(number, 0), hits)

    found = hit = 0
    summary = []
    for source in SOURCES:
        lines = records.get(source)
        if not lines:
            raise ValueError(f"Missing or empty coverage: {source}")
        covered = sum(count > 0 for count in lines.values())
        if not covered:
            raise ValueError(f"No executed lines: {source}")
        found += len(lines)
        hit += covered
        summary.append(f"{source}: {covered}/{len(lines)} lines")
    percentage = 100 * hit / found
    summary.append(f"Selected-source line coverage: {percentage:.1f}% (minimum {minimum:.1f}%)")
    if percentage < minimum:
        raise ValueError("\n".join(summary))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--minimum", type=float, default=80.0)
    args = parser.parse_args()
    try:
        print("\n".join(check_report(args.report.read_text(), args.minimum)))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Coverage check failed: {error}\n")


if __name__ == "__main__":
    main()

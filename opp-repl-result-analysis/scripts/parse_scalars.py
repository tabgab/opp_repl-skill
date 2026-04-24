#!/usr/bin/env python3
"""Parse OMNeT++ .sca files from a results directory and print JSON.

Usage:
    parse_scalars.py <results_dir_or_glob>
    parse_scalars.py <results_dir> --filter 'name("dropCount")'
    parse_scalars.py <results_dir> --group-by name  # aggregate across reps
    parse_scalars.py <results_dir> --output csv     # default: json

Approach:
    1. Try the Python API (omnetpp.scave.results) — fast, native.
    2. Fallback to opp_scavetool CLI — always works if OMNeT++ is on PATH.

Both are stock OMNeT++ tooling — no extra packages, no opp_repl-specific
imports.  Safe to drop into any agent workflow.
"""
import argparse
import glob
import json
import os
import subprocess
import sys


def find_sca_files(path_or_glob):
    """Expand a directory or glob into a list of .sca files."""
    if os.path.isdir(path_or_glob):
        return sorted(glob.glob(os.path.join(path_or_glob, "**", "*.sca"),
                                recursive=True))
    return sorted(glob.glob(path_or_glob, recursive=True))


def setup_omnetpp_pythonpath():
    """Add $__omnetpp_root_dir/python to sys.path if the env var is set."""
    root = os.environ.get("__omnetpp_root_dir")
    if not root:
        return False
    p = os.path.join(root, "python")
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
    return os.path.isdir(p)


def try_python_api(sca_files, filter_expr=None):
    """Return list of dicts via omnetpp.scave.results, or None if unusable."""
    setup_omnetpp_pythonpath()
    try:
        from omnetpp.scave.results import read_result_files, get_scalars
    except ImportError:
        return None

    try:
        df = read_result_files(sca_files, include_fields_as_scalars=True)
        scalars = get_scalars(df, include_runattrs=True)
        if filter_expr:
            # Simple substring match on name column — full OMNeT filter
            # grammar is supported by scavetool, not pandas.  Warn user.
            scalars = scalars[scalars["name"].str.contains(
                filter_expr, regex=True, na=False)]
        records = scalars.to_dict(orient="records")
        return records
    except Exception as e:
        print(f"# Python API failed ({e}); falling back to scavetool",
              file=sys.stderr)
        return None


def try_scavetool(sca_files, filter_expr=None):
    """Export via `opp_scavetool export -F CSV-R` and return list of dicts."""
    cmd = ["opp_scavetool", "export", "-F", "CSV-R",
           "--add-fields-as-scalars", "-o", "/dev/stdout"]
    if filter_expr:
        cmd.extend(["--filter", filter_expr])
    cmd.extend(sca_files)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              check=False)
    except FileNotFoundError:
        sys.stderr.write("ERROR: opp_scavetool not found. Source OMNeT++'s "
                         "setenv or install OMNeT++ 6.x.\n")
        sys.exit(2)

    if proc.returncode != 0:
        sys.stderr.write(f"opp_scavetool exited {proc.returncode}:\n"
                         f"{proc.stderr}\n")
        sys.exit(proc.returncode)

    # Parse CSV-R output
    import csv
    from io import StringIO
    reader = csv.DictReader(StringIO(proc.stdout))
    return list(reader)


def aggregate(records, group_by):
    """Group records by the given column(s) and emit mean/std/count."""
    import statistics
    buckets = {}
    for r in records:
        # only scalar rows have numeric value; skip vectors/histograms
        try:
            v = float(r.get("value") or r.get("mean") or "nan")
        except (ValueError, TypeError):
            continue
        if v != v:  # nan
            continue
        key = tuple(r.get(g, "") for g in group_by)
        buckets.setdefault(key, []).append(v)
    out = []
    for key, vs in sorted(buckets.items()):
        row = dict(zip(group_by, key))
        row["count"] = len(vs)
        row["mean"] = statistics.fmean(vs)
        row["stddev"] = statistics.pstdev(vs) if len(vs) > 1 else 0.0
        row["min"] = min(vs)
        row["max"] = max(vs)
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="Results directory or .sca glob pattern")
    ap.add_argument("--filter", help="Filter expression (name regex for Python "
                                     "API, full OMNeT filter for scavetool)")
    ap.add_argument("--group-by", action="append", default=[],
                    help="Aggregate across runs. Repeatable. "
                         "E.g. --group-by name --group-by module")
    ap.add_argument("--output", choices=["json", "csv", "table"],
                    default="json", help="Output format (default: json)")
    ap.add_argument("--force-scavetool", action="store_true",
                    help="Skip the Python API and use opp_scavetool directly")
    args = ap.parse_args()

    sca_files = find_sca_files(args.path)
    if not sca_files:
        sys.stderr.write(f"ERROR: no .sca files under {args.path!r}\n")
        sys.exit(1)

    records = None
    if not args.force_scavetool:
        records = try_python_api(sca_files, args.filter)
    if records is None:
        records = try_scavetool(sca_files, args.filter)

    if args.group_by:
        records = aggregate(records, args.group_by)

    if args.output == "json":
        # Replace pandas NaN/Infinity with None for valid JSON output
        def _clean(v):
            if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
                return None
            return v
        records = [{k: _clean(v) for k, v in r.items()} for r in records]
        print(json.dumps(records, indent=2, default=str))
    elif args.output == "csv":
        import csv
        if not records:
            sys.exit(0)
        w = csv.DictWriter(sys.stdout, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)
    elif args.output == "table":
        # ASCII table — ok for small result sets
        if not records:
            return
        cols = list(records[0].keys())
        widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in records))
                  for c in cols}
        print(" | ".join(c.ljust(widths[c]) for c in cols))
        print("-+-".join("-" * widths[c] for c in cols))
        for r in records:
            print(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))


if __name__ == "__main__":
    main()

---
name: opp-repl-result-analysis
description: Extract scalar, vector, statistic, and histogram values from OMNeT++ simulation result files (.sca, .vec) after a run finished. Covers two stock approaches — (A) `opp_scavetool` CLI exporting to CSV/JSON for pandas ingestion, and (B) the `omnetpp.scave.results` Python API that ships with every OMNeT++ install. Answers the recurring agent problem "the run DONE-ed, now how do I read the numbers?". Load whenever a workflow needs to compare simulation output against analytical/reference values, aggregate across replications, or feed numbers into pandas/numpy.
---

# Analyzing OMNeT++ simulation results

A DONE simulation writes `.sca` (scalars) and `.vec` (vectors) files
into `results/` under the working directory.  opp_repl does NOT
provide a `read_scalars()` helper of its own — but OMNeT++ itself
ships two well-tested APIs that cover every case.  Pick one:

| Approach                    | Use when                                          |
|-----------------------------|---------------------------------------------------|
| (A) `opp_scavetool` CLI     | Shell scripts, CI, or agents without Python-side OMNeT++ bindings |
| (B) `omnetpp.scave.results` | In-REPL or in-MCP analysis — returns pandas DataFrames |

Both are part of stock OMNeT++ (6.x) — no extra install.

## Quick answer — get scalar values into a dict

    # Approach B inside opp_repl/Python:
    import os, sys
    sys.path.insert(0, os.path.join(os.environ["__omnetpp_root_dir"], "python"))
    from omnetpp.scave.results import read_result_files, get_scalars

    p = get_default_simulation_project()
    results_dir = p.get_full_path("results")

    df = read_result_files(results_dir, include_fields_as_scalars=True)
    scalars = get_scalars(df, include_runattrs=True)

    # scalars is a pandas.DataFrame with columns:
    #   run, module, name, value, configname, replication, ...
    print(scalars[["module", "name", "value"]].head())

    # Aggregate across replications:
    means = scalars.groupby("name")["value"].mean()
    print(means)

## Approach A — opp_scavetool CLI

The `opp_scavetool` binary queries and exports `.sca` / `.vec`
files.  Useful when you want CSV/JSON for an external pipeline or
when `omnetpp` is not importable in the Python process.

### Query: list result items

    # What's in my results?
    opp_scavetool query -l results/*.sca

    # What unique scalar names exist?
    opp_scavetool query -n -T s results/*.sca

    # Per-run summary with labels suitable for machine parsing
    opp_scavetool query -l -p -g --tabs results/*.sca

### Export to CSV-R (records, Pandas-friendly)

    opp_scavetool export -F CSV-R \
        --add-fields-as-scalars \
        -o scalars.csv \
        results/*.sca

CSV columns: `run, type, module, name, attrname, attrvalue, value, count, sumweights, mean, stddev, min, max, underflows, overflows, binedges, binvalues, vectime, vecvalue`.

### Export to JSON

    opp_scavetool export -F JSON -o scalars.json results/*.sca

### Index vector files for faster random access

    opp_scavetool index results/*.vec
    # creates .vci files alongside each .vec

### Filter expressions

`--filter` accepts OMNeT++'s filter language.  Common patterns:

    # Only scalars named `throughput` from any module
    opp_scavetool query -l --filter 'name("throughput") AND type("scalar")' results/*.sca

    # Only from module snk (the Sink)
    opp_scavetool query -l --filter 'module("*snk")' results/*.sca

    # Combine
    opp_scavetool query -l --filter 'name("dropCount") AND module("*queue*")' results/*.sca

Run `opp_scavetool help filter` for the full grammar.

## Approach B — omnetpp.scave.results Python API

This module is bundled with every OMNeT++ install at
`$__omnetpp_root_dir/python/omnetpp/scave/results.py`.  If you
sourced OMNeT++'s `setenv`, its path is on `PYTHONPATH` already;
otherwise add it.

### Available functions

    from omnetpp.scave.results import (
        read_result_files,    # load .sca/.vec into an internal table
        get_scalars,          # DataFrame of scalar values
        get_vectors,          # DataFrame of time-series (one row per vector)
        get_statistics,       # DataFrame of aggregated statistics
        get_histograms,       # DataFrame of histograms
        get_parameters,       # DataFrame of NED parameter assignments
        get_runs,             # DataFrame of run metadata
        get_runattrs,         # DataFrame of per-run attributes
        get_itervars,         # DataFrame of iteration variables
        get_param_assignments,
        get_config_entries,
    )

### Typical pattern

    import os, sys
    omnetpp_root = os.environ["__omnetpp_root_dir"]
    sys.path.insert(0, os.path.join(omnetpp_root, "python"))

    from omnetpp.scave.results import read_result_files, get_scalars, get_vectors

    df = read_result_files("results/*.sca",
                           include_fields_as_scalars=True)
    # include_fields_as_scalars=True unpacks statistic fields
    # (count, mean, stddev, min, max) as individual scalar rows.

    scalars = get_scalars(df, include_runattrs=True)
    vectors = get_vectors(df)

    # Aggregate one scalar across all replications
    mean_drop = scalars[scalars.name == "dropCount"].value.mean()

    # Fetch a single vector's time series
    thr = vectors[vectors.name == "throughput"].iloc[0]
    t, v = thr.vectime, thr.vecvalue   # numpy arrays

### Bundled helper script

This skill ships `scripts/parse_scalars.py` — run it directly in
`opp_repl` / `python3` to get a JSON dump of every scalar from a
results directory:

    python3 scripts/parse_scalars.py results/
    # OR limit to one metric:
    python3 scripts/parse_scalars.py results/ --filter '*.dropCount'

The script is self-contained: it sets up the PYTHONPATH from
`$__omnetpp_root_dir` itself, uses `get_scalars` if available,
and falls back to `opp_scavetool` if the Python bindings can't be
imported.  Agents should prefer calling this script over writing
their own regex parser.

## Raw .sca file format (for when you can't install anything)

A `.sca` file is line-oriented text.  Each record starts with a
keyword:

    version 3
    run PureAloha1-0-20260420-13:30:58-35234
    attr configname PureAloha1
    attr network Aloha
    config cpu-time-limit 1s
    param Aloha.host[*].iaTime exponential(2s)
    scalar Aloha.host[0]     channelUtilization   0.1234
    scalar Aloha.server      collisionCount       42
    statistic Aloha.server   collisionLength:mean 0.0456
    field    Aloha.server    collisionLength:mean:count  123
    attr     unit                                ms

Parsing by hand (only if both scavetool and the Python bindings
are unreachable):

    with open(sca_file) as f:
        for line in f:
            if line.startswith("scalar "):
                _, module, name, value = line.strip().split(None, 3)
                # ...

Prefer the official tools — their output is regression-tested and
they handle statistic fields, histograms, and multi-run files
correctly.

## Integrating with opp_repl results

Each `SimulationTaskResult` carries the paths to the files it
produced:

    r = run_simulations(sim_time_limit="100s")
    tr = r.results[0]

    tr.stdout_file          # e.g. "results/General-#0.out"
    tr.scalar_file          # e.g. "results/General-#0.sca"
    tr.vec_file             # e.g. "results/General-#0.vec"
    tr.eventlog_file        # eventlog, if recorded

    # Full path for scavetool:
    p = tr.task.simulation_config.simulation_project
    sca_path = p.get_full_path(tr.task.simulation_config.working_directory
                               + "/" + tr.scalar_file)

    # Now feed sca_path to opp_scavetool or read_result_files.

## Pitfalls

- **`.vec` needs indexing** — `.vec` files written by the
  simulation don't have an index until `opp_scavetool index` runs
  (or any export command that reads them).  Calling `get_vectors`
  without an index is slow; call `opp_scavetool index *.vec` once
  after a batch finishes.
- **Replications aren't auto-averaged** — `get_scalars` returns
  one row per (run, module, name).  Aggregate explicitly:
  `scalars.groupby(["module", "name"]).value.mean()`.
- **`include_fields_as_scalars=True` is usually what you want** —
  without it, statistic fields (`count`, `mean`, `stddev`, ...)
  live in their own table and `get_scalars` returns an empty
  DataFrame for statistics-only runs.
- **Result dir vs working dir** — `results/` is ALWAYS relative
  to the simulation's working directory, not the project root or
  the CWD of the REPL.  When loading files, use
  `simulation_project.get_full_path(...)`.
- **Large `.vec` files** — an unfiltered `get_vectors` loads every
  timestamp into memory.  Use `--filter` with `opp_scavetool` or
  pre-filter the DataFrame from `read_result_files` before calling
  `get_vectors`.
- **Do NOT roll your own parser** — the `.sca` format has edge
  cases (quoting, multiline histograms, encoding) that make
  regex-based parsers fragile.  Use scavetool or the Python API.

## See also

- `opp-repl-running-simulations` — what produces the .sca/.vec files.
- `opp-repl-tasks-and-results` — `SimulationTaskResult` paths.
- `opp-repl-project-scaffolding` — getting to a state where .sca
  files exist in the first place.
- `opp-repl-troubleshooting` — when runs fail before producing results.

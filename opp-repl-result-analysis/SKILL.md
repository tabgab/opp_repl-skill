---
name: opp-repl-result-analysis
description: Read simulation scalar / vector / histogram results from a completed run. On current opp_repl (>= commit 2e6835e, Apr 2026), `SimulationTaskResult` and `MultipleSimulationTaskResults` expose `get_scalars()`, `get_vectors()`, and `get_histograms()` methods that return pandas DataFrames directly. Fallbacks: `opp_scavetool` CLI (for shell / CI) and the `omnetpp.scave.results` Python API (for older opp_repl). Load whenever a workflow needs to compare simulation output against analytical/reference values, aggregate across replications, or feed numbers into pandas/numpy.
---

# Analyzing OMNeT++ simulation results

On current opp_repl main, reading results from a completed
`run_simulations()` is a one-liner — `.get_scalars()` / `.get_vectors()`
/ `.get_histograms()` on the result object returns pandas DataFrames
ready for aggregation.  For older opp_repl or for external / CLI
scripting, use `opp_scavetool` or the scave Python API directly.

| Approach                     | Use when                                     |
|------------------------------|----------------------------------------------|
| (A) `r.get_scalars()` etc.   | **Current opp_repl, inside the REPL / MCP.** |
| (B) `opp_scavetool` CLI      | Shell scripts, CI, agents without Python deps |
| (C) `omnetpp.scave.results`  | Direct scave API (older opp_repl, more control) |

## Path A — result-object methods (current opp_repl)

### Per-run (one `SimulationTaskResult`)

    r = run_simulations(simulation_project=p, sim_time_limit="100s")
    tr = r.results[0]

    df = tr.get_scalars()                        # .sca -> DataFrame
    df = tr.get_scalars(include_fields=False)    # skip statistic fields
    df = tr.get_scalars(include_runattrs=True)   # add run attributes as columns

    df = tr.get_vectors()                        # .vec -> DataFrame
    df = tr.get_histograms()                     # histograms from .sca

Docstrings quote the exact signatures:

    get_scalars(include_fields=True, include_runattrs=False, **kwargs)
    get_vectors(include_runattrs=False, **kwargs)
    get_histograms(include_runattrs=False, **kwargs)

### Aggregated (one `MultipleSimulationTaskResults`)

    r = run_simulations(simulation_project=p, sim_time_limit="100s")

    df = r.get_scalars()      # concatenated across all DONE runs
    df = r.get_vectors()      # same
    df = r.get_histograms()   # same

`MultipleSimulationTaskResults.get_*()` skips any non-DONE result
(an FAILed / ERRORed task contributes nothing) and concatenates the
remaining per-run DataFrames with `ignore_index=True`.

### Typical aggregation pattern

    df = r.get_scalars()
    means = df.groupby("name").value.mean()
    sems  = df.groupby("name").value.sem()   # if you want error bars

    # Per-module, per-metric
    agg = df.groupby(["module", "name"]).value.mean()

Columns in the returned DataFrame: `runID`, `module`, `name`, `value`,
`configname`, `experiment`, `inifile`, `network`, `repetition`,
`runnumber`, `seedset`, plus whatever run attributes the simulation
emitted.  `include_runattrs=True` adds extra run-attr columns.

Reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/task_results.md#reading-simulation-results

## Path B — `opp_scavetool` CLI

The `opp_scavetool` binary queries and exports `.sca` / `.vec`
files.  Useful when you want CSV / JSON for an external pipeline or
when `omnetpp` is not importable in the calling Python process.

### Query: list result items

    opp_scavetool query -l results/*.sca             # list all items
    opp_scavetool query -n -T s results/*.sca        # unique scalar names
    opp_scavetool query -l -p -g --tabs results/*.sca  # per-run, machine-readable

### Export to CSV-R (records, Pandas-friendly)

    opp_scavetool export -F CSV-R \
        --add-fields-as-scalars \
        -o scalars.csv \
        results/*.sca

CSV columns include: `run, type, module, name, value, count, mean,
stddev, min, max, vectime, vecvalue` ...

### Export to JSON

    opp_scavetool export -F JSON -o scalars.json results/*.sca

### Index vector files for faster random access

    opp_scavetool index results/*.vec

### Filter expressions

    opp_scavetool query -l --filter 'name("dropCount")' results/*.sca
    opp_scavetool query -l --filter 'module("*queue*")' results/*.sca

Run `opp_scavetool help filter` for the full grammar.

## Path C — `omnetpp.scave.results` Python API

This module is bundled with every OMNeT++ install at
`$__omnetpp_root_dir/python/omnetpp/scave/results.py`.  After
sourcing OMNeT++'s `setenv`, its path is on `PYTHONPATH`.

    from omnetpp.scave.results import (
        read_result_files,   # load .sca/.vec into internal table
        get_scalars,         # DataFrame of scalars
        get_vectors,         # DataFrame of time-series
        get_statistics,      # aggregated statistics
        get_histograms,      # histograms
        get_parameters,      # NED parameter assignments
        get_runs,            # run metadata
        get_runattrs,        # per-run attributes
        get_itervars,        # iteration variables
    )

    df = read_result_files("results/*.sca",
                           include_fields_as_scalars=True)
    scalars = get_scalars(df, include_runattrs=True)

`r.get_scalars()` (path A) is a thin wrapper over this; use path C
directly when you need `read_result_files` glob / filter parameters
that the task-result method doesn't expose.

## Bundled helper script (for shells / MCP / external agents)

`scripts/parse_scalars.py` wraps both paths B and C so any caller
can get scalars out of a results directory without needing to reason
about which path is available:

    python3 scripts/parse_scalars.py results/
    python3 scripts/parse_scalars.py results/ --filter 'name("dropCount")'
    python3 scripts/parse_scalars.py results/ --group-by name --output table

The script sets up `$__omnetpp_root_dir/python` on `PYTHONPATH`
itself, tries the Python API first, falls back to `opp_scavetool`
on `ImportError`.  Outputs valid JSON (NaN-clean), CSV, or ASCII
table.

Use the script when:
- An external agent (not running inside opp_repl) needs scalars.
- You're in a shell script / Makefile / CI that doesn't call Python.
- You want a language-neutral command-line probe during debugging.

When you're already inside opp_repl, prefer `r.get_scalars()` — same
result, no subprocess.

## Raw `.sca` file format

`.sca` is line-oriented text.  Keywords per line:

    version 3
    run PureAloha1-0-20260420-13:30:58-35234
    attr configname PureAloha1
    config cpu-time-limit 1s
    param Aloha.host[*].iaTime exponential(2s)
    scalar Aloha.host[0]     channelUtilization   0.1234
    statistic Aloha.server   collisionLength:mean 0.0456
    field    Aloha.server    collisionLength:mean:count  123

**Do NOT write a regex parser** — the format has edge cases
(quoting, multi-line histograms, encoding) that make hand-rolled
parsers fragile.  Always go through scavetool or the Python API.

## Integrating with opp_repl results

Each `SimulationTaskResult` exposes file paths too, for cases the
`.get_*()` methods don't cover:

    tr.stdout_file_path        # e.g. "results/General-#0.out"
    tr.scalar_file_path        # e.g. "results/General-#0.sca"
    tr.vector_file_path        # e.g. "results/General-#0.vec"
    tr.eventlog_file_path      # eventlog, if recorded

To feed these into scavetool / `read_result_files` manually:

    p = tr.task.simulation_config.simulation_project
    working_dir = tr.task.simulation_config.working_directory
    sca_path = p.get_full_path(working_dir + "/" + tr.scalar_file_path)

But 9 times out of 10 `tr.get_scalars()` is what you want.

## Pitfalls

- **`.vec` needs indexing for random access** — the `.vec` files
  written by the simulation don't have a `.vci` index until
  `opp_scavetool index` runs (or any export / get_vectors call
  reads them).  Large batches — index once after the batch finishes.
- **Replications aren't auto-averaged** — `r.get_scalars()` returns
  one row per (run, module, name).  Aggregate explicitly:
  `df.groupby(["module","name"]).value.mean()`.
- **`include_fields_as_scalars=True`** (the default on
  `tr.get_scalars()`) unpacks statistic fields (count, mean, stddev,
  min, max) as individual scalar rows.  For run comparisons that's
  usually what you want.  For raw per-`@statistic` queries, pass
  `include_fields=False`.
- **Large `.vec` files** — an unfiltered `r.get_vectors()` loads
  every timestamp into memory.  Filter at the scavetool level first
  when working with long time-series:
  `opp_scavetool export -F CSV-R --filter 'name("throughput")' -o thr.csv results/*.vec`.
- **Result dir vs working dir** — `results/` is ALWAYS relative to
  the simulation's working directory, not the project root or the
  CWD of the REPL.  Use `simulation_project.get_full_path(...)`
  when building paths manually.
- **ERRORed runs contribute nothing** — `MultipleSimulationTaskResults.get_*()`
  silently skips non-DONE results.  Check `r.is_all_results_done()`
  or `r.get_error_results()` first if your aggregation looks off.

## See also

- `opp-repl-running-simulations` — produces the .sca / .vec files.
- `opp-repl-tasks-and-results` — full `SimulationTaskResult` API.
- `opp-repl-project-scaffolding` — getting to a state where .sca
  files exist in the first place.
- `opp-repl-troubleshooting` — when runs fail before producing results.

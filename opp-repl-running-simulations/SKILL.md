---
name: opp-repl-running-simulations
description: Build projects and run simulations with opp_repl — build_project, run_simulations, get_simulation_tasks, get_simulation_task, clean_simulation_results, default project auto-detection, build modes (release/debug/sanitize/coverage/profile), concurrency (thread/process/cluster), and the MultipleTaskResults object. The bread-and-butter skill for everyday simulation work.
---

# Building and running simulations

`run_simulations()` is the most-used opp_repl function.  It selects
configs, expands them into tasks, builds the project if needed, then
runs the whole batch and hands back a `MultipleTaskResults` you can
drill into.

Upstream references:
- https://github.com/omnetpp/opp_repl/blob/main/doc/running_simulations.md
- https://github.com/omnetpp/opp_repl/blob/main/doc/tasks.md

## Building

Building is **implicit** — `run_simulations()` always rebuilds
first unless you pass `build=False`.  When you want a build without
a run:

    build_project(simulation_project=inet_project)
    build_project(simulation_project=inet_project, mode="debug")

Build modes map to binary suffixes:

| mode       | suffix       | Typical use                |
|------------|--------------|----------------------------|
| `release`  | `_release`   | Default, optimized         |
| `debug`    | `_dbg`       | Step through with gdb/IDE  |
| `sanitize` | `_sanitize`  | AddressSanitizer / UBSan   |
| `coverage` | `_coverage`  | LLVM coverage reports      |
| `profile`  | `_profile`   | perf / Hotspot, speed tests|

`build_project()` recursively builds OMNeT++ and any `used_projects`
first (toggle with `recursive=False`).

## Running

    # Everything from the default project
    run_simulations()

    # Explicit project + short time limit
    run_simulations(simulation_project=aloha_project, sim_time_limit="1s")

    # Subset via filters
    run_simulations(simulation_project=inet_project,
                    working_directory_filter="examples/ethernet",
                    config_filter="Vlan",
                    sim_time_limit="10s")

    # Debug mode (one specific config)
    run_simulations(simulation_project=inet_project,
                    working_directory_filter="examples/ethernet",
                    mode="debug", sim_time_limit="10s")

See `opp-repl-filtering` for the full filter vocabulary.

## Default project

Three ways to establish the default so you can drop
`simulation_project=`:

1. `cd` into a project directory before launching the REPL.
2. Start with `-p PROJECT` on the command line.
3. Call `set_default_simulation_project(inet_project)` at runtime.

## Concurrency

By default tasks run concurrently using all CPU cores.  Controls:

- `concurrent=False` -- sequential (useful for debugging, clearer logs).
- `scheduler="thread"` (default) / `"process"` / `"cluster"`.
- `randomize=True` -- shuffle execution order.
- Pressing **Ctrl-C** cancels the remaining tasks; already-collected
  results stay in the returned object.

Running on an SSH/Dask cluster requires the `cluster` extra and
`cluster=SSHCluster(...)` -- see `opp-repl-ssh-cluster`.

## Result object

`run_simulations()` returns `MultipleTaskResults`.  The workhorse
methods:

    r = run_simulations(config_filter="PureAloha", sim_time_limit="1s")
    r                                 # prints summary + unexpected details
    r.get_error_results()             # drill into ERRORs
    r.get_unexpected_results()        # anything not matching expectation
    r.is_all_results_done()           # bool
    r.rerun()                         # re-execute same tasks
    r.get_error_results().rerun()     # re-run only the failures
    r.results[0].rerun(mode="debug")  # re-run single task in debug

Full model in `opp-repl-tasks-and-results`.

## Single-task shortcut

Use `get_simulation_task()` when you need EXACTLY one task (it errors
if the filters match zero or >1 tasks).  Handy for
`compare_simulations()`, `optimize_simulation_parameters()`, and
interactive debugging:

    t = get_simulation_task(config_filter="PureAloha1", run_number=0,
                            sim_time_limit="1s")
    r = t.run()

## Cleaning result files

    clean_simulation_results(simulation_project=inet_project)
    clean_simulation_results(simulation_project=inet_project,
                             working_directory_filter="examples/ethernet")

Removes `.sca`, `.vec`, `.vci`, `.elog`, `.log`, `.rt` files from
result folders of matching configs.

## CLI equivalents

    opp_build_project --load inet.opp -p inet -m debug
    opp_run_simulations --load inet.opp -p inet \
                        --working-directory-filter examples/ethernet \
                        -t 10s

See `opp-repl-cli-tools` for the full flag table.

## Pitfalls

- `sim_time_limit="1s"` is a STRING with a unit — not a number.
- `build=False` + stale binary silently runs old code.  Keep `build`
  on unless you just built the same mode.
- In concurrent mode the on-screen order of results does not match
  task order.  Use `r.results[i].task` to correlate.
- Interrupting (Ctrl-C) leaves partial result files in place; run
  `clean_simulation_results()` to tidy up.

## See also

- `opp-repl-concepts` — the object model.
- `opp-repl-filtering` — narrow down which configs run.
- `opp-repl-tasks-and-results` — inspect and rerun results.
- `opp-repl-ssh-cluster` — distribute to remote machines.
- `opp-repl-cli-tools` — shell wrappers for CI.

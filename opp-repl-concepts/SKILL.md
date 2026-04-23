---
name: opp-repl-concepts
description: Mental model for opp_repl — the object hierarchy (SimulationWorkspace -> OmnetppProject + SimulationProject -> SimulationConfig -> SimulationTask -> TaskResult/MultipleTaskResults) and how loaded projects become {name}_project REPL variables. Load this before any other opp-repl-* skill that manipulates simulations so API calls make sense.
---

# Core concepts

opp_repl's API mirrors the structure of an OMNeT++ workspace.
Understand these five layers and everything else falls into place.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/concepts.md

## The five objects

| Object                | What it represents                                         |
|-----------------------|------------------------------------------------------------|
| `SimulationWorkspace` | Registry of all loaded projects + default selection.       |
| `OmnetppProject`      | A specific OMNeT++ *installation* (binaries, setenv, build).|
| `SimulationProject`   | A *model project* (INET, Simu5G, OMNeT++ samples, ...).    |
| `SimulationConfig`    | One `[Config ...]` section from one `.ini` file.           |
| `SimulationTask`      | One concrete run: (config, run number, mode, limits).      |
| `TaskResult` / `MultipleTaskResults` | Outcome of a task / a batch of tasks.       |

## The tree

    SimulationWorkspace
     |-- OmnetppProject  "omnetpp"              (an OMNeT++ install)
     |-- SimulationProject  "inet"              (a model project)
     |    |-- SimulationConfig  examples/ethernet -c General     (1 run)
     |    |-- SimulationConfig  examples/wireless -c Wifi       (10 runs)
     |    |    |-- SimulationTask run #0
     |    |    |-- SimulationTask run #1
     |    |    \-- ...
     |    \-- ...
     \-- SimulationProject  "simu5g"            (depends on inet)

## Convenience variables

Every loaded project appears in the REPL as a variable named
`{name}_project` (hyphens and dots become underscores):

- `inet.opp`  --> `inet_project`
- `simu5g.opp`  --> `simu5g_project`
- `omnetpp-6.3.0.opp` --> `omnetpp_6_3_0_project`

Use `get_simulation_project_variable_names()` to list them.

## Defaults

opp_repl keeps a **default simulation project** and a **default
OMNeT++ project**.  If you launched the REPL from inside a project
directory, the default is auto-set.  Otherwise use
`-p PROJECT` on the command line, or
`set_default_simulation_project(inet_project)` at runtime.

When a function omits its `simulation_project=` argument, the default
is used.  This means you can write:

    run_simulations(sim_time_limit="1s")
    run_fingerprint_tests()

rather than always passing the project explicitly.

## Tasks and results

- Every operation (build, run, test, compare) becomes a **Task**.
- Tasks always produce a **result**.  Batches produce
  `MultipleTaskResults`, which supports filtering, drill-down,
  counting per code, and `.rerun()`.
- Result codes depend on the task family:
  - Simulations:  DONE / SKIP / CANCEL / ERROR
  - Tests:        PASS / FAIL (plus the simulation codes)
  - Updates:      KEEP / INSERT / UPDATE (writes a new baseline)
  - Builds:       DONE / SKIP (up-to-date) / ERROR
  - Comparisons:  IDENTICAL / DIVERGENT / DIFFERENT

Full detail in `opp-repl-tasks-and-results`.

## Filtering

Any function that selects configs or tasks accepts a consistent set
of regex and predicate filters.  See `opp-repl-filtering` for the
full vocabulary — the rules are shared across `run_simulations()`,
all `run_*_tests()`, `compare_simulations()`, and every
`get_simulation_tasks()` call.

## See also

- `opp-repl-opp-files` — write the `.opp` files that populate the workspace.
- `opp-repl-running-simulations` — call `run_simulations()` and friends.
- `opp-repl-tasks-and-results` — inspect, filter, and rerun results.
- `opp-repl-filtering` — the shared filter vocabulary.

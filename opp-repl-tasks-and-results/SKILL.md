---
name: opp-repl-tasks-and-results
description: The opp_repl Task/Result object model — SimulationTask, TestTask, UpdateTask, BuildTask, CompareSimulationsTask; result codes (DONE/SKIP/CANCEL/ERROR, PASS/FAIL, KEEP/INSERT/UPDATE, IDENTICAL/DIVERGENT/DIFFERENT); MultipleTaskResults filtering/drill-down/rerun; trajectories (fingerprint & stdout); project-state hashing; and git-bisect for test regressions. Load when you need to inspect, filter, or rerun anything opp_repl has produced.
---

# Tasks and task results

Every opp_repl operation is a **Task**; every task produces a
**TaskResult**.  Batches return a `MultipleTaskResults`.  These
objects are your programmable handle on what the REPL just did.

Upstream references:
- https://github.com/omnetpp/opp_repl/blob/main/doc/tasks.md
- https://github.com/omnetpp/opp_repl/blob/main/doc/task_results.md

## Task families

| Family        | Base classes                         | Result codes                               |
|---------------|--------------------------------------|--------------------------------------------|
| Simulations   | `SimulationTask` / `MultipleSimulationTasks` | DONE / SKIP / CANCEL / ERROR         |
| Tests         | `TestTask`, `SimulationTestTask`, `FingerprintTestTask`, `SpeedTestTask`, `StatisticalTestTask`, `ChartTestTask`, `SmokeTestTask` | PASS / FAIL + simulation codes |
| Updates       | `UpdateTask`, `FingerprintUpdateTask`, `SpeedUpdateTask`, `StatisticalResultsUpdateTask`, `ChartUpdateTask` | KEEP / INSERT / UPDATE / SKIP / CANCEL / ERROR |
| Builds        | `BuildTask`, `MsgCompileTask`, `CppCompileTask`, `LinkTask`, `CopyBinaryTask`, `BuildSimulationProjectTask` | DONE / SKIP (up-to-date) / ERROR |
| Comparisons   | `CompareSimulationsTask`             | IDENTICAL / DIVERGENT / DIFFERENT / SKIP / CANCEL / ERROR |

## What a SimulationTask carries

- `simulation_config` + `run_number` -> identifies WHAT to run.
- `mode` -> release / debug / sanitize / coverage / profile.
- Time limits -> `sim_time_limit`, `cpu_time_limit`; plain strings
  or callables `(config, run_number) -> str`.
- Runner -> `subprocess` (default), `opp_env` (auto when the project
  is opp_env-managed), `inprocess` (CFFI), `ide` (auto when
  `debug=True` or a breakpoint parameter is set).
- Output overrides -> stdout / eventlog / `.sca` / `.vec` file paths.
- Knobs -> `record_eventlog`, `record_pcap`, `user_interface`
  (`"Cmdenv"` default or `"Qtenv"`), extra `inifile_entries`.

## Inspecting a SimulationTaskResult

    r = run_simulations(config_filter="PureAloha1", sim_time_limit="1s")
    t = r.results[0]

    t.result_code             # e.g. "DONE"
    t.expected_result         # usually "DONE"
    t.is_expected()           # actual == expected
    t.elapsed_time            # wall clock
    t.cpu_time, t.cycles, t.instructions   # from OMNeT++ CPU summary
    t.error_message, t.error_module        # when ERROR
    t.last_event_number, t.last_simulation_time
    t.stdout_file, t.eventlog_file, t.sca_file, t.vec_file
    t.used_ned_types          # sorted list of NED types instantiated
    t.subprocess_result       # raw CompletedProcess

    t.print_result()          # colored one-line summary
    t.print_stdout(); t.print_stderr()   # captured I/O
    t.get_description()       # string form

Post-mortem trajectories:

    ft = t.get_fingerprint_trajectory()   # per-event fingerprint values
    st = t.get_stdout_trajectory()        # event# <-> stdout lines (regex OK)

Result-data accessors (current opp_repl, >= commit 2e6835e):

    df = t.get_scalars()      # .sca file as a pandas DataFrame
    df = t.get_vectors()      # .vec file as a pandas DataFrame
    df = t.get_histograms()   # histograms from .sca

Signatures:

    get_scalars(include_fields=True, include_runattrs=False, **kwargs)
    get_vectors(include_runattrs=False, **kwargs)
    get_histograms(include_runattrs=False, **kwargs)

See `opp-repl-result-analysis` for typical aggregation patterns,
filter options, and fallbacks for older opp_repl.

## MultipleTaskResults drill-down

    r = run_simulations(sim_time_limit="1s")

    r.get_done_results()
    r.get_error_results()
    r.get_unexpected_results()            # excludes SKIP/CANCEL
    r.get_failed_results()                # test-task specific (FAIL)
    r.is_all_results_done()
    r.is_all_results_expected()

    r.filter_results(
        result_codes=["ERROR"],
        error_message_regex="Unknown parameter")

Every filter returns a new `MultipleTaskResults`, so chains compose.

### Aggregated result-data accessors

`MultipleSimulationTaskResults` (current opp_repl) also exposes
the same `.get_scalars()` / `.get_vectors()` / `.get_histograms()`
methods.  They concatenate per-run DataFrames across every DONE
result:

    r = run_simulations(sim_time_limit="1s")
    df = r.get_scalars()     # one row per (run, module, name)
    df.groupby("name").value.mean()   # aggregate across reps

Non-DONE results (SKIP, CANCEL, ERROR, FAIL) contribute nothing —
the method silently skips them.  Check `r.is_all_results_done()`
first if your aggregation looks sparse.

## Re-running

Both single and multiple results support `.rerun()`, optionally with
parameter overrides:

    r.rerun()                          # repeat everything
    r.get_error_results().rerun()      # only failures
    r.results[0].rerun(mode="debug")   # one task in debug

`.recreate()` produces a modified copy of the task without running
it; useful when you want to tweak parameters and inspect before
executing.

## Hashing and caching

Every task computes a SHA-256 over its relevant inputs (project
state, config, run number, mode, time limits).  Higher-level
machinery such as fingerprint tests uses these hashes to decide
whether a cached baseline is still valid.

## Git-bisecting a regression

opp_repl supports bisecting failing tests across git commits.  The
idea: given a known-good commit and a known-bad commit, the bisect
machinery runs the test at each midpoint until the introducing
commit is isolated.  Use this for fingerprint / statistical / speed
regressions where rerun times are feasible.

Treat the bisect helper as a facade over `run_*_tests()` +
git-checkout; see `help(bisect_failing_tests)` (or the equivalent
function in your installed version) for the exact signature — the
upstream API has evolved.  The general pattern:

    # Pseudo-code — consult live docstring for current name/signature:
    bisect_failing_tests(simulation_project=inet_project,
                         good_ref="v4.5", bad_ref="HEAD",
                         config_filter="Vlan",
                         sim_time_limit="1s")

## Pitfalls

- Test tasks reuse simulation codes plus PASS/FAIL.  A PASS test
  can still have a DONE/ERROR simulation underneath — inspect
  `.simulation_task_result` when a test unexpectedly fails.
- `SKIP` on simulation = "requires user input / not runnable headless".
  It is not the same as "build was up-to-date" (which is SKIP on a
  BuildTask).
- `filter_results(error_message_regex=...)` is a regex on the parsed
  error message; include `^`/`$` to anchor.
- Reruns inherit the ORIGINAL task's parameters.  Override via
  kwargs: `result.rerun(sim_time_limit="10s")`.
- **`tr.stdout` / `tr.stderr` may be `None` on ERROR.**  They are
  parsed from files the simulation writes
  (`cmdenv-output-file`, stderr capture) — if the process died
  before writing, the fields stay `None`.  For EVERY `ERROR`
  result, go to the raw subprocess output:

      print(tr.subprocess_result.returncode)
      print(tr.subprocess_result.stderr)
      print(tr.subprocess_result.stdout)
      print(tr.subprocess_result.args)   # shows the exact cmd line

  See `opp-repl-troubleshooting` for an exit-code-to-cause table.

## See also

- `opp-repl-concepts` — where tasks sit in the hierarchy.
- `opp-repl-running-simulations` — creates SimulationTasks.
- `opp-repl-comparing-simulations` — CompareSimulationsTask.
- `opp-repl-filtering` — filter configs before tasks are created.
- Every `opp-repl-*-tests` skill — task-family details per test type.

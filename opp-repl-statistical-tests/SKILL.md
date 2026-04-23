---
name: opp-repl-statistical-tests
description: Detect regressions in simulation SCALAR results by comparing against saved baselines. Complementary to fingerprint tests — coarser (numeric tolerances) but easier to interpret. update_statistical_test_results seeds or refreshes the baseline in the project's statistics_folder. Load when fingerprint churn is too noisy and you only care about headline metrics.
---

# Statistical tests

Statistical tests compare current scalar results (`.sca` values)
against stored baselines.  They tolerate numerical noise up to a
configured threshold, so they are stabler than fingerprint tests
for stochastic simulations but weaker at catching subtle bugs.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/statistical_tests.md

## Baseline location

`SimulationProject` parameter `statistics_folder` (default `"."`)
names the folder where baseline scalar results live, one file per
config/run.

## Python API

    # Seed / refresh after intentional changes
    update_statistical_test_results(simulation_project=inet_project)

    # Run the tests
    run_statistical_tests(simulation_project=inet_project)

    # Scope to one region of the project
    run_statistical_tests(simulation_project=inet_project,
                          working_directory_filter="examples/ethernet")

Result codes follow the UpdateTask family:
`KEEP` / `INSERT` / `UPDATE` on updates, `PASS` / `FAIL` on tests.

## Command line

    opp_update_statistical_test_results --load inet.opp -p inet
    opp_run_statistical_tests          --load inet.opp -p inet

## When to pick statistical over fingerprint

- The simulation has non-determinism you can't remove; fingerprint
  tests flap but scalar averages are stable within tolerance.
- You only care about a handful of headline metrics (throughput,
  delay, PER).
- Your CI budget doesn't allow eventlog-level checks.

Conversely, for tight regression coverage (each event matters),
prefer fingerprint tests — see `opp-repl-fingerprint-tests`.

## Pitfalls

- Baselines live OUTSIDE the git repo by default (the folder is
  `.`).  Point `statistics_folder` at `tests/statistics/` or
  similar to keep the baseline under version control.
- Tolerances are per-test and default to vendor values; consult
  the live docstring (`help(run_statistical_tests)`) when tuning.
- Updating a baseline should be a reviewable commit — otherwise
  regressions can slip in under cover of a "refresh".

## See also

- `opp-repl-fingerprint-tests` — trajectory-level alternative.
- `opp-repl-running-simulations` — underlying run machinery.
- `opp-repl-tasks-and-results` — inspect FAIL details.

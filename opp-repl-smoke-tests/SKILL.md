---
name: opp-repl-smoke-tests
description: Run smoke tests with opp_repl — the cheapest regression check. run_smoke_tests() verifies that every (or filtered) simulation starts and terminates without crashing. Load this for baseline health checks before running heavier test suites (fingerprint, statistical, etc.).
---

# Smoke tests

Smoke tests are the minimum viable regression check: every selected
simulation is launched briefly and its exit status is verified.  A
PASS means "it ran without crashing"; it does NOT imply correctness.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/smoke_tests.md

## Python API

    # Whole default project
    run_smoke_tests()

    # Explicit project + filter
    run_smoke_tests(simulation_project=aloha_project,
                    config_filter="PureAlohaExperiment")

    # Time-limit to keep runtime sane
    run_smoke_tests(sim_time_limit="1s")

Typical output:

    [6/7] . -c TandemQueueExperiment -r 3 PASS
    [5/7] . -c TandemQueueExperiment -r 2 PASS
    ...
    Multiple smoke test results: PASS, summary: 7 PASS in 0:00:01.117562

Re-running after a change:

    r = run_smoke_tests(simulation_project=aloha_project,
                        config_filter="PureAlohaExperiment")
    r.rerun()                       # repeat everything
    r.get_failed_results().rerun()  # only failures

## Command line

    opp_run_smoke_tests --load "~/workspace/omnetpp/**/*.opp" -p fifo
    opp_run_smoke_tests -t 1s --filter PureAloha

## When to use smoke tests

- First CI step -- fast, catches crashes from refactors.
- Feature branch sanity check before running longer suites.
- Validating a fresh OMNeT++ or INET install.
- As part of `run_all_tests()` / `run_release_tests()`.

For deeper behavioral regressions, follow up with:
- `opp-repl-fingerprint-tests` (trajectory-level).
- `opp-repl-statistical-tests`  (scalar results).
- `opp-repl-speed-tests`        (performance).
- `opp-repl-chart-tests`        (rendered charts).

## Pitfalls

- PASS is WEAK evidence: many real regressions are behavioral, not
  crashing.  Always layer with fingerprint or statistical tests.
- `sim_time_limit` is critical: without it, a slow sample can turn
  a smoke suite into an hour-long run.  Upstream doesn't set a
  default -- pick `1s` to `10s` depending on model complexity.
- Use `simulation_config_filter=lambda c: not c.abstract` semantics
  is already the default; passing your own predicate overrides it.

## See also

- `opp-repl-running-simulations` — underlying run machinery.
- `opp-repl-tasks-and-results` — inspecting test results.
- `opp-repl-filtering` — which configs to target.
- `opp-repl-feature-and-release-tests` — comprehensive suites.

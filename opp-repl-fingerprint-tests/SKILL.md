---
name: opp-repl-fingerprint-tests
description: Detect behavioral regressions using simulation event fingerprints (hash-based). run_fingerprint_tests compares a computed hash of selected state against a stored baseline in the project's fingerprint_store JSON. update_fingerprint_test_results seeds or refreshes that baseline. Load when you need trajectory-level regression detection stronger than smoke tests.
---

# Fingerprint tests

Fingerprint tests hash a trajectory of per-event simulation state
(event types, packet counts, etc.) and compare the result against
a value stored in the project's `fingerprint_store` JSON file.  A
tiny behavioral change produces a completely different hash,
catching regressions that pass smoke/statistical tests.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/fingerprint_tests.md

## Baseline store

`SimulationProject` parameter `fingerprint_store` (default
`"fingerprint.json"`) points to a JSON file containing
`(config, run_number, sim_time_limit) -> fingerprint` entries.
INET convention: `tests/fingerprint/store.json`.

## First-time seeding

    update_fingerprint_test_results(simulation_project=inet_project,
                                    sim_time_limit="1s")

Output includes `INSERT` lines for every new entry:

    [04/42] Updating fingerprint . -c PureAlohaExperiment -r 3 for 1s INSERT 856a-c13d/tplx
    ...
    Multiple update fingerprint results: INSERT, summary: 42 INSERT (unexpected) in 0:00:01.567

Re-running the update when nothing has changed gives `KEEP`
(baseline preserved):

    Multiple update fingerprint results: KEEP, summary: 7 KEEP in 0:00:00.218

## Running the tests

    r = run_fingerprint_tests(simulation_project=inet_project,
                              sim_time_limit="1s")

Output:

    [02/42] Checking fingerprint . -c PureAlohaExperiment -r 1 for 1s PASS
    ...
    Multiple fingerprint test results: PASS, summary: 42 PASS in 0:00:01.129

Re-run only failures, or narrow to a region after intentional
changes:

    r.get_fail_results().rerun()
    update_fingerprint_test_results(simulation_project=inet_project,
                                    working_directory_filter="examples/ethernet",
                                    sim_time_limit="10s")

## Command line

Typical CI workflow starting from an empty store:

    # 1. No baseline yet -> every test SKIPs
    opp_run_fingerprint_tests --load inet.opp -p inet -t 1s

    # 2. Seed
    opp_update_fingerprint_test_results --load inet.opp -p inet -t 1s

    # 3. Tests PASS until behavior changes
    opp_run_fingerprint_tests --load inet.opp -p inet -t 1s

## Debugging a FAIL

A FAIL means the live simulation trajectory no longer matches the
stored hash.  Two useful follow-ups:

1. Pull the stdout / fingerprint trajectory from the failing
   `TaskResult` (see `opp-repl-tasks-and-results`):

       failed = r.get_fail_results().results[0]
       ft = failed.simulation_task_result.get_fingerprint_trajectory()
       # compare to a known-good run

2. Use `compare_simulations()` or
   `compare_simulations_between_commits()` (see
   `opp-repl-comparing-simulations`) to locate the first divergent
   event.

## Pitfalls

- Any change to simulation time limits or random seeds CHANGES the
  fingerprint.  Keep `sim_time_limit` stable across runs or
  regenerate the baseline.
- Fingerprint entries are keyed by `(config, run, time limit)`.
  Running the tests with a different `sim_time_limit` than was
  stored yields `SKIP` (no baseline for this key).
- Commit the updated `fingerprint_store` JSON alongside intentional
  behavioral changes — otherwise CI will keep failing.
- Fingerprint tests are deterministic only if the underlying
  simulation is deterministic.  Non-deterministic features (e.g.
  real-time scheduler, certain `exponential()` RNG setups without
  fixed seeds) will produce PASS/FAIL flapping.

## See also

- `opp-repl-running-simulations` — underlying run machinery.
- `opp-repl-comparing-simulations` — locate the divergence.
- `opp-repl-tasks-and-results` — `.get_fingerprint_trajectory()`.
- `opp-repl-statistical-tests` — coarser, scalar-level regression.

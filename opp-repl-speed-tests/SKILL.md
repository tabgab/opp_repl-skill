---
name: opp-repl-speed-tests
description: Detect performance regressions by measuring CPU instruction counts with the `profile` build mode and comparing against a stored baseline in speed_store. run_speed_tests / update_speed_test_results use perf counters for deterministic measurement across noisy hardware. Load when you need to catch a change that makes the simulator slower.
---

# Speed tests

Speed tests measure the **CPU instruction count** of a simulation
(via Linux perf counters) and compare it to a baseline in the
project's `speed_store` (default `speed.json`).  Instruction count
is more deterministic than wall time, so these tests work on
shared/noisy CI machines without flapping.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/speed_tests.md

## Build mode

Speed tests require the `profile` build mode (binary suffix
`_profile`).  `run_speed_tests()` builds it automatically.

## Python API

    # Seed the baseline
    update_speed_test_results(simulation_project=inet_project)

    # Run the tests
    run_speed_tests(simulation_project=inet_project)

    # Target a subset
    run_speed_tests(simulation_project=inet_project,
                    working_directory_filter="showcases")

Result codes: `PASS` / `FAIL` (plus KEEP/INSERT/UPDATE on updates).

## Command line

    opp_update_speed_test_results --load inet.opp -p inet
    opp_run_speed_tests           --load inet.opp -p inet

## When to pick speed tests

- You merged an optimization and want to lock in the gain.
- You suspect a regression made the simulator slower (even though
  results are still correct).
- You want to track long-term performance in a per-commit dashboard.

## Pitfalls

- Requires Linux perf support (`perf_event_paranoid <= 2` on many
  distros).  macOS cannot run speed tests.
- Instruction counts shift with compiler / libc updates.  After a
  toolchain bump, refresh the baseline before running.
- Tests that heavily use the RNG may have instruction counts
  dependent on seed values; hold seeds constant across runs.

## See also

- `opp-repl-profiling` — deeper look at where cycles go.
- `opp-repl-running-simulations` — underlying run machinery.
- `opp-repl-tasks-and-results` — inspect speed-test FAILs.

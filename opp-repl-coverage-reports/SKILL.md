---
name: opp-repl-coverage-reports
description: Generate C++ line-coverage reports from simulation runs using opp_repl's `coverage` build mode and LLVM coverage tools. open_coverage_report builds, runs, and opens the HTML report; generate_coverage_report just produces it. Load when you need to know which C++ lines are exercised by a given simulation or test.
---

# Coverage reports

Coverage reports show which lines of C++ simulation source are
executed by a run.  Uses the `coverage` build mode (binary suffix
`_coverage`) and LLVM's `llvm-profdata` / `llvm-cov` toolchain.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/coverage.md

## Python API

    # Build + run + open HTML report in browser
    open_coverage_report(simulation_project=inet_project,
                         working_directory_filter="examples/ethernet",
                         sim_time_limit="10s")

    # Build + run, just produce the report (don't open it)
    generate_coverage_report(simulation_project=inet_project,
                             working_directory_filter="examples/ethernet",
                             sim_time_limit="10s")

Filters follow the standard vocabulary
(see `opp-repl-filtering`).

## Requirements

- LLVM 10+ on PATH (`llvm-profdata`, `llvm-cov`).
- The C++ sources built with clang (gcc does not emit the
  profile format LLVM expects).

## Typical workflow

1. Pick one representative simulation config (coverage of a large
   test matrix is often dominated by a few runs).
2. Run it through `open_coverage_report(...)`.
3. Use the HTML report to find untested branches; add
   fingerprint/statistical tests that exercise them.

## Pitfalls

- Coverage builds are about 20 % slower than release.  Long runs
  get expensive; keep `sim_time_limit` modest for coverage sweeps.
- Multiple tasks per run merge their profile data.  Don't mix
  debug and coverage runs in the same session -- the binary
  suffix differs and the merge confusion can hide coverage.
- Reports include ONLY the simulation project's sources by default;
  to include OMNeT++ core or INET add the relevant source roots in
  your project's build config.

## See also

- `opp-repl-running-simulations` — selects what to cover.
- `opp-repl-profiling` — orthogonal (time, not coverage).

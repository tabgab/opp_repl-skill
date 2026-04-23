---
name: opp-repl-feature-and-release-tests
description: Comprehensive test suites — feature tests verify builds with different optional feature combinations, release tests validate release candidates, and run_all_tests sequentially runs every configured test type. Load for release-gate CI pipelines that want one call to rule them all.
---

# Feature, release, and all-tests suites

Three convenience entry points that sit above the specific test
types (`opp-repl-smoke-tests`, `opp-repl-fingerprint-tests`, etc.).

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/feature_tests.md

## Feature tests

Check that the project builds and simulations set up correctly
with each documented combination of optional features (OMNeT++
"features" as declared in `.oppfeatures`).

    run_feature_tests(simulation_project=inet_project)

CLI:

    opp_run_feature_tests --load inet.opp -p inet

## Release tests

A curated suite suitable for validating a release build — combines
smoke, fingerprint, statistical, feature, and chart tests
(exact composition is project-defined).

    run_release_tests(simulation_project=inet_project)

CLI:

    opp_run_release_tests --load inet.opp -p inet

## Run all tests

Sequentially run every configured test type:

    run_all_tests(simulation_project=inet_project)

CLI:

    opp_run_all_tests --load inet.opp -p inet

## When to use which

- `run_smoke_tests()` only -- fast feedback on feature branches.
- `run_feature_tests()` -- before merging changes that touch build
  configuration, NED features, or optional modules.
- `run_release_tests()` -- the official gate for pushing a release.
- `run_all_tests()` -- use during maintenance or when you want a
  single verdict; overlap with `run_release_tests()` is intentional
  in many projects.

## Pitfalls

- These entry points aggregate long-running tests; expect tens of
  minutes to hours depending on project size.  Pin `sim_time_limit`
  and use `--no-concurrent` sparingly.
- Because each sub-suite has its own baselines, any ONE stale
  baseline can fail the whole aggregate.  Fix baselines
  incrementally using the individual `update_*_test_results`
  entry points.
- Results are reported per sub-suite, not merged into a single
  MultipleTaskResults.  Inspect each section for drill-down.

## See also

- Every other `opp-repl-*-tests` skill.
- `opp-repl-tasks-and-results` — per-sub-suite drill-down.
- `opp-repl-github-actions` — dispatch suites remotely.

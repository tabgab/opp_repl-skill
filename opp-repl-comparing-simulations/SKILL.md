---
name: opp-repl-comparing-simulations
description: Compare simulation results between two projects or two git commits using opp_repl. compare_simulations / compare_simulations_between_commits check stdout trajectories, fingerprint trajectories, and scalar results; report IDENTICAL/DIVERGENT/DIFFERENT; and support debug_at_fingerprint_divergence_position() for interactive bisection. Load when investigating a regression or validating a refactor.
---

# Comparing simulations

Run the same configuration against two project variants — two
checked-out projects, two git commits, or a project and an overlay
build — then diff the results at three levels.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/comparing_simulations.md

## What gets compared

| Layer                     | Verdict                      |
|---------------------------|------------------------------|
| Stdout trajectory         | IDENTICAL / DIVERGENT        |
| Fingerprint trajectory    | IDENTICAL / DIVERGENT        |
| Scalar statistical result | IDENTICAL / DIFFERENT        |

The overall `CompareSimulationsTaskResult` code is the worst-case
across the three.  `IDENTICAL` means every byte and value matches;
`DIVERGENT` marks a point in the event stream where the two runs
first disagree; `DIFFERENT` means only the scalar summary differs
(within/outside tolerance).

## Comparing two projects

    r = compare_simulations(
        simulation_project_1=inet_project,
        simulation_project_2=inet_baseline_project,
        working_directory_filter="examples/ethernet",
        config_filter="General",
        run_number=0)

## Comparing two git commits of the same project

    r = compare_simulations_between_commits(
        inet_project, "HEAD~1", "HEAD",
        config_filter="General",
        run_number=0)

Internally this uses git worktrees / overlay builds so you don't
have to check out the other commit manually.

## Drilling into a result

    first = r.results[0]
    first.stdout_trajectory_comparison_result       # IDENTICAL / DIVERGENT
    first.fingerprint_trajectory_comparison_result  # IDENTICAL / DIVERGENT
    first.statistical_comparison_result             # IDENTICAL / DIFFERENT

    first.print_different_statistical_results(include_relative_errors=True)

    # Interactive debugging at the divergence point
    first.debug_at_fingerprint_divergence_position()
    first.show_divergence_position_in_sequence_chart()

## Typical workflow

1. Noticed a fingerprint test regression in INET's
   `examples/ethernet`.
2. Compare `HEAD` vs. the last-known-good tag:

       r = compare_simulations_between_commits(
           inet_project, "v4.5", "HEAD",
           working_directory_filter="examples/ethernet",
           config_filter="General", run_number=0)

3. `r.results[0].show_divergence_position_in_sequence_chart()` to
   see the event where the two runs diverge.
4. `.debug_at_fingerprint_divergence_position()` launches a debug
   session at that event on both sides.

## Pitfalls

- Non-deterministic simulations flap as DIVERGENT even when "the
  same".  Fix the seed / RNG before comparing.
- Two projects must have matching config names and a matching INI
  file in the working directory — otherwise the comparison SKIPs.
- `compare_simulations_between_commits()` uses overlay builds under
  the hood.  A very dirty working tree (untracked build products)
  can confuse the overlay; commit or stash first.
- Statistical tolerances differ per project.  For cross-project
  comparisons, understand each `statistics_folder` convention.

## See also

- `opp-repl-fingerprint-tests` — trajectory-level regression tests.
- `opp-repl-overlay-builds` — how the between-commits machinery works.
- `opp-repl-tasks-and-results` — result drill-down vocabulary.

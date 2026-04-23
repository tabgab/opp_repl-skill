---
name: opp-repl-chart-tests
description: Detect visual regressions in result-analysis charts. run_chart_tests renders charts from current results and compares them pixel-wise against baseline images stored in the project's media_folder. Requires the `chart` extra (matplotlib + numpy). Load when analysis plots are part of your deliverable and must stay stable.
---

# Chart tests

Chart tests render each analysis chart and compare the resulting
image against a baseline stored in the project's `media_folder`.
A visual diff catches regressions in analysis pipelines, not in the
simulation itself — e.g. a buggy pandas aggregation or a changed
axis label.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/chart_tests.md

## Requirements

- `chart` extra installed: `pip install "opp_repl[chart]"`.
- `media_folder` set on the `SimulationProject` (INET convention:
  `doc/media`).

## Python API

    # Seed baselines (first time, or after intentional chart changes)
    update_chart_test_results(simulation_project=inet_project)

    # Run tests
    run_chart_tests(simulation_project=inet_project)

    # Scoped
    run_chart_tests(simulation_project=inet_project,
                    working_directory_filter="showcases")

Result codes: `PASS` / `FAIL` (`INSERT`/`UPDATE`/`KEEP` on updates).

## Command line

    opp_update_chart_test_results --load inet.opp -p inet
    opp_run_chart_tests           --load inet.opp -p inet

## When chart tests catch what fingerprint tests miss

- The numerical results are correct but the plotting code
  regressed.
- A new `matplotlib`/`seaborn` release changed default styles.
- An analysis notebook's filter criteria drifted.

## Pitfalls

- Matplotlib backends, fonts, and DPI all affect pixel output.
  Pin the stack (`matplotlib==X.Y`, optionally `MPLBACKEND=Agg`)
  across CI to avoid spurious diffs.
- Anti-aliasing quirks between Linux distros can cause flapping.
  For reproducible CI, run chart tests inside a fixed container.
- Tolerance is pixel-wise, not structural; a one-pixel shift may
  show as FAIL.  Consult the live docstring for tolerance knobs.

## See also

- `opp-repl-running-simulations` — produces the scalars charts read.
- `opp-repl-tasks-and-results` — inspect FAILed chart tests.

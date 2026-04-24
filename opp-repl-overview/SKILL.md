---
name: opp-repl-overview
description: START HERE. Entry-point skill for opp_repl — the Python REPL, CLI tools, and MCP server for OMNeT++ simulations (github.com/omnetpp/opp_repl). Contains a decision tree that maps the user's task to the exact sibling skills to load. Load this first whenever the user asks about opp_repl, OMNeT++ simulations, running sims from Python, or regression-testing simulation models. Even weak models can navigate the rest of the pack via this skill's triage table.
---

# opp_repl — overview and skill map

opp_repl replaces ad-hoc shell loops and Qtenv clicking with
reproducible, scriptable workflows for OMNeT++.  Same feature set,
three interfaces:

1. An **IPython REPL** (`opp_repl`) — interactive Python with all
   helpers pre-loaded.
2. A **shell wrapper suite** (`opp_build_project`,
   `opp_run_simulations`, `opp_run_*_tests`,
   `opp_update_*_test_results`) — for CI and scripts.
3. An **MCP server** — so AI agents can drive the REPL as a tool
   endpoint.

## Decision tree — load exactly these skills for common tasks

### I want to...

**...install opp_repl.**
  -> `opp-repl-installation`

**...create a NEW OMNeT++ project from scratch** (write files,
build, run).
  -> `opp-repl-project-scaffolding`  (← START HERE for
     "make a new simulation", "create a new model", "build an
     example from zero")
  -> then `opp-repl-running-simulations`
  -> then `opp-repl-result-analysis` to read the numbers out
  -> keep `opp-repl-troubleshooting` on hand; new projects hit
     §1, §2, §4 of that skill on almost every first build.

**...run simulations that already exist.**
  -> `opp-repl-running-simulations` + `opp-repl-filtering`
  -> `opp-repl-tasks-and-results` for drill-down / rerun
  -> `opp-repl-result-analysis` for reading the numbers.

**...regression-test my project.** Pick the type:
  - `opp-repl-smoke-tests`               — it ran, it didn't crash.
  - `opp-repl-fingerprint-tests`         — behavior hasn't drifted.
  - `opp-repl-statistical-tests`         — scalar results in tolerance.
  - `opp-repl-speed-tests`               — CPU instr. count stable.
  - `opp-repl-chart-tests`               — rendered charts unchanged.
  - `opp-repl-sanitizer-tests`           — ASAN/UBSan clean.
  - `opp-repl-feature-and-release-tests` — comprehensive suites.
  All test skills cross-reference `opp-repl-running-simulations`
  and `opp-repl-tasks-and-results`.

**...compare / bisect / debug a regression.**
  -> `opp-repl-comparing-simulations`    + `opp-repl-fingerprint-tests`
  -> `opp-repl-tasks-and-results` for post-mortem inspection.

**...tune a parameter to match a target.**
  -> `opp-repl-parameter-optimization`   + `opp-repl-running-simulations`.

**...measure speed / cost.**
  -> `opp-repl-profiling` (call-stack profiles) or
     `opp-repl-speed-tests` (regression) or
     `opp-repl-coverage-reports` (line coverage).

**...distribute runs across multiple machines.**
  -> `opp-repl-ssh-cluster`              + `opp-repl-running-simulations`.

**...read .sca / .vec result files** after a run.
  -> `opp-repl-result-analysis` (includes a bundled script).

**...debug a build or run failure.**
  -> `opp-repl-troubleshooting` FIRST — it maps every common
     symptom ("Building X failed", exit 127, "Class not found",
     etc.) to its exact cause and fix.

**...wire opp_repl into an AI agent / MCP client.**
  -> `opp-repl-mcp-server`                + `opp-repl-ai-workflows`.

**...set up CI on GitHub.**
  -> `opp-repl-cli-tools`                 + `opp-repl-github-actions`.

**...use a specific opp_env-managed OMNeT++ version** (e.g.
`omnetpp-6.3.0` + `inet-4.6.0`).
  -> `opp-repl-opp-env-integration`       + `opp-repl-opp-files`.

## Compact feature inventory

| Capability                  | Skill                              |
|-----------------------------|------------------------------------|
| Install / setenv            | `opp-repl-installation`            |
| Core object model           | `opp-repl-concepts`                |
| `.opp` descriptors          | `opp-repl-opp-files`               |
| **NEW project from zero**   | `opp-repl-project-scaffolding`     |
| Interactive REPL usage      | `opp-repl-repl-usage`              |
| Shell wrappers for CI       | `opp-repl-cli-tools`               |
| Build + run simulations     | `opp-repl-running-simulations`     |
| Filtering configs/runs      | `opp-repl-filtering`               |
| Task & result model         | `opp-repl-tasks-and-results`       |
| **Read .sca / .vec**        | `opp-repl-result-analysis`         |
| **Error decoder**           | `opp-repl-troubleshooting`         |
| Smoke tests                 | `opp-repl-smoke-tests`             |
| Fingerprint tests           | `opp-repl-fingerprint-tests`       |
| Statistical tests           | `opp-repl-statistical-tests`       |
| Speed tests                 | `opp-repl-speed-tests`             |
| Chart tests                 | `opp-repl-chart-tests`             |
| Sanitizer tests             | `opp-repl-sanitizer-tests`         |
| Feature + release tests     | `opp-repl-feature-and-release-tests` |
| Comparing simulations       | `opp-repl-comparing-simulations`   |
| Parameter optimization      | `opp-repl-parameter-optimization`  |
| Coverage reports            | `opp-repl-coverage-reports`        |
| Profiling (perf/Hotspot)    | `opp-repl-profiling`               |
| Overlay builds              | `opp-repl-overlay-builds`          |
| SSH / Dask cluster runs     | `opp-repl-ssh-cluster`             |
| GitHub Actions dispatch     | `opp-repl-github-actions`          |
| opp_env integration         | `opp-repl-opp-env-integration`     |
| MCP server for AI agents    | `opp-repl-mcp-server`              |
| End-to-end AI recipes       | `opp-repl-ai-workflows`            |

## Minimum viable skill set for a first session

If you're not sure what to load, start with this **core set** — it
covers 80% of real-world opp_repl usage:

    opp-repl-concepts                 (object model)
    opp-repl-opp-files                (project descriptors)
    opp-repl-running-simulations      (the main entry point)
    opp-repl-tasks-and-results        (inspecting what happened)
    opp-repl-result-analysis          (reading .sca files)
    opp-repl-troubleshooting          (decoding errors)

Add one or two test-type skills when testing, or `opp-repl-mcp-server`
when connecting an agent.

## When NOT to use opp_repl

- One-off manual runs — plain `opp_run` or the OMNeT++ IDE is simpler.
- Pure analysis of existing `.sca` files with no rerun — just use
  `opp_scavetool` directly.
- Simulations that require GUI interaction during the run —
  opp_repl is headless.

## Authoritative upstream references

- Repo:  https://github.com/omnetpp/opp_repl
- Docs:  https://github.com/omnetpp/opp_repl/tree/main/doc
- Each sibling skill cites the specific upstream doc file it
  distils.

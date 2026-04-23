---
name: opp-repl-overview
description: Entry-point skill for working with opp_repl — the interactive Python REPL, command-line tool suite, and MCP server for driving OMNeT++ simulations (github.com/omnetpp/opp_repl). Load this first to learn what opp_repl can do and which sibling skills to load for specific tasks (installation, running sims, regression tests, comparisons, optimization, MCP integration, clusters, etc.).
---

# opp_repl — Overview and Skill Map

opp_repl is a Python toolkit for OMNeT++ that replaces ad-hoc shell
loops and Qtenv clicking with reproducible, scriptable workflows.
It exposes the same feature set through three interfaces:

1. An **IPython REPL** (`opp_repl`) with every helper pre-loaded into
   the top-level namespace.
2. A set of **standalone command-line tools** (`opp_build_project`,
   `opp_run_simulations`, `opp_run_*_tests`, `opp_update_*_test_results`).
3. An **MCP server** (Model Context Protocol, streamable HTTP) so AI
   agents can call the REPL as a live tool endpoint.

## Feature inventory

| Capability                | Load skill                            |
|---------------------------|---------------------------------------|
| Install / setenv          | opp-repl-installation                 |
| Core object model         | opp-repl-concepts                     |
| `.opp` project descriptors| opp-repl-opp-files                    |
| Interactive REPL usage    | opp-repl-repl-usage                   |
| Shell wrappers (CI-ready) | opp-repl-cli-tools                    |
| Build + run simulations   | opp-repl-running-simulations          |
| Filtering configs/runs    | opp-repl-filtering                    |
| Task & result model       | opp-repl-tasks-and-results            |
| Smoke tests               | opp-repl-smoke-tests                  |
| Fingerprint tests         | opp-repl-fingerprint-tests            |
| Statistical tests         | opp-repl-statistical-tests            |
| Speed tests               | opp-repl-speed-tests                  |
| Chart tests               | opp-repl-chart-tests                  |
| Sanitizer tests           | opp-repl-sanitizer-tests              |
| Feature + release tests   | opp-repl-feature-and-release-tests    |
| Comparing simulations     | opp-repl-comparing-simulations        |
| Parameter optimization    | opp-repl-parameter-optimization       |
| Coverage reports          | opp-repl-coverage-reports             |
| Profiling (perf/Hotspot)  | opp-repl-profiling                    |
| Overlay (fuse-overlayfs)  | opp-repl-overlay-builds               |
| SSH / Dask cluster runs   | opp-repl-ssh-cluster                  |
| GitHub Actions dispatch   | opp-repl-github-actions               |
| opp_env integration       | opp-repl-opp-env-integration          |
| MCP server for AI agents  | opp-repl-mcp-server                   |
| End-to-end AI recipes     | opp-repl-ai-workflows                 |

## How these skills compose

- Almost every skill assumes you have already installed opp_repl
  (→ `opp-repl-installation`) and understand the core objects
  (→ `opp-repl-concepts`: Workspace, OmnetppProject, SimulationProject,
  SimulationConfig, SimulationTask, TaskResult).
- All skills that accept filters share the same vocabulary; load
  `opp-repl-filtering` once and the rule set applies everywhere.
- The three interfaces (REPL / CLI / MCP) are interchangeable.
  Choose the one that matches the host environment:
  - Human or agent in a terminal -> `opp-repl-repl-usage`.
  - CI pipeline or shell script -> `opp-repl-cli-tools`.
  - AI agent with tool-calling   -> `opp-repl-mcp-server`.

## When to use opp_repl instead of plain OMNeT++ tools

- You need to run MANY simulations and filter the result set.
- You need reproducible regression testing
  (fingerprint/statistical/speed/chart/sanitizer/smoke/feature).
- You need to compare two versions of a project, or bisect a
  regression across git commits.
- You need parameter optimization (scipy Nelder-Mead) tied to
  simulation outputs.
- You are orchestrating OMNeT++ from an AI agent and want a single
  MCP endpoint instead of subprocessing `opp_run` directly.

For one-off manual runs, plain `opp_run` or the OMNeT++ IDE is
usually simpler — opp_repl shines when the workflow repeats.

## Typical first session (5 minutes)

1. Install: follow `opp-repl-installation`.
2. Write one `.opp` file per project: follow `opp-repl-opp-files`.
3. Launch: `opp_repl --load "etc/*.opp"`.
4. Inside IPython, call `run_simulations(sim_time_limit="1s")`.
5. Inspect: `r.get_error_results()` — drill-down comes from
   `opp-repl-tasks-and-results`.

## Authoritative upstream docs

- Repo: https://github.com/omnetpp/opp_repl
- Docs:  https://github.com/omnetpp/opp_repl/tree/main/doc
- Each sibling skill cross-references the specific upstream doc file.

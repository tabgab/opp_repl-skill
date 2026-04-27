---
name: opp-repl-ai-workflows
description: End-to-end recipes for an AI agent working with opp_repl via its MCP server or shell tools — investigate a regression, bisect across git commits, tune parameters, run a full release gate, set up a new project from scratch. Load this ALONG WITH opp-repl-mcp-server when acting as an autonomous agent managing OMNeT++ simulations.
---

# AI agent workflows with opp_repl

This skill is a **cookbook** for agents driving opp_repl.  Each
recipe lists the prerequisite skills, the decision tree, and the
actual tool calls.  Load together with `opp-repl-mcp-server` for
MCP-based integration, or `opp-repl-cli-tools` for pure-shell
orchestration.

## Recipe 1 — "Run this simulation and report"

**Prereqs**: `opp-repl-installation`, `opp-repl-opp-files`,
`opp-repl-running-simulations`, `opp-repl-tasks-and-results`,
`opp-repl-result-analysis`.

1. If no `.opp` file exists for the target project, write one
   (template from `opp-repl-opp-files/templates/`), OR run
   `create_project(name, path=...)` on current opp_repl.
2. Start or attach to a REPL / MCP server.
3. Run:

       r = run_simulations(
           simulation_project=<name>_project,
           config_filter="...",
           sim_time_limit="1s")

4. Summarise `r.get_error_results()` and
   `r.is_all_results_done()`.  On failure, rerun a failing task
   in debug mode and pull `print_stderr()` for diagnostics.
5. On success, aggregate scalars:

       df = r.get_scalars()             # DataFrame merged across reps
       means = df.groupby("name").value.mean()

## Recipe 2 — "Investigate a regression"

**Prereqs**: `opp-repl-fingerprint-tests`,
`opp-repl-comparing-simulations`, `opp-repl-tasks-and-results`.

1. Reproduce the failure:

       r = run_fingerprint_tests(
           simulation_project=<p>,
           config_filter=<suspect>,
           sim_time_limit="1s")
       failures = r.get_fail_results()

2. Compare HEAD against the last-known-good tag/commit:

       cr = compare_simulations_between_commits(
           <p>, "v4.5", "HEAD",
           config_filter=<suspect>,
           run_number=0)

3. Inspect the divergence:

       first = cr.results[0]
       first.fingerprint_trajectory_comparison_result
       first.print_different_statistical_results(
           include_relative_errors=True)
       first.show_divergence_position_in_sequence_chart()

4. Once the suspect commit is identified, leave a report
   explicitly referencing the first divergent event number and
   simulation time.

## Recipe 3 — "Tune a parameter to hit a target"

**Prereqs**: `opp-repl-parameter-optimization`,
`opp-repl-running-simulations`.

1. Narrow to a single task with `get_simulation_task(...)`.
2. Specify `expected_result_names`, `expected_result_values`, and
   `parameter_*` arguments (see the skill).
3. Call `optimize_simulation_parameters(...)`.
4. Report convergence: best values, residual error, number of
   evaluations.

If the objective is noisy, lengthen `sim_time_limit` or use
repeats before giving up.

## Recipe 4 — "Release gate on a feature branch"

**Prereqs**: `opp-repl-feature-and-release-tests`,
`opp-repl-github-actions`, `opp-repl-cli-tools`.

1. Locally: `run_smoke_tests()` on the default project.
2. If green, trigger a remote suite:

       dispatch_workflow("release-tests.yml", ref="topic/my-feature")

3. In parallel, run `run_fingerprint_tests()` locally on the
   subset of configs you actually touched (narrow filter).
4. Summarise pass/fail for both local and remote verdicts.

## Recipe 5 — "Set up a new simulation project from scratch"

**Prereqs**: `opp-repl-installation`, `opp-repl-project-scaffolding`,
`opp-repl-concepts`, `opp-repl-running-simulations`,
`opp-repl-result-analysis`.

On current opp_repl (>= commit a17fcab, Apr 2026):

```python
from opp_repl.simulation.project import create_project

# Generates <name>.opp, .oppbuildspec, .nedfolders, package.ned,
# omnetpp.ini; loads the project; returns the SimulationProject.
p = create_project("mm1k", path="/tmp", namespace=False)

# Now add NED + C++:
#   /tmp/mm1k/Mm1k.ned
#   /tmp/mm1k/Source.{h,cc}   Queue.{h,cc}   Sink.{h,cc}
# and edit /tmp/mm1k/omnetpp.ini to set `network = Mm1k` +
# parameter assignments.

p.build()
r = run_simulations(simulation_project=p, sim_time_limit="100s")
df = r.get_scalars()
```

On older opp_repl, copy templates from
`opp-repl-project-scaffolding/templates/` into a fresh directory
instead, rename `mm1k` to your chosen name everywhere, then
`load_opp_file()` + `build_project()` + `run_simulations()`.

## Recipe 6 — "Distribute a parameter sweep to a cluster"

**Prereqs**: `opp-repl-ssh-cluster`,
`opp-repl-running-simulations`, `opp-repl-filtering`.

1. Authenticate SSH to each worker.
2. Build locally, rsync binaries:

       p.build(mode="release")
       p.copy_binary_simulation_distribution_to_cluster(
           ["node1", "node2"])

3. Launch:

       c = SSHCluster(scheduler_hostname="node1",
                      worker_hostnames=["node1", "node2"])
       c.start()
       run_simulations(scheduler="cluster", cluster=c,
                       filter="PureAlohaExperiment")

4. Watch the Dask dashboard at localhost:8797.

## Recipe 7 — "Keep baselines up to date after a planned change"

**Prereqs**: any `opp-repl-*-tests` skill for the test type.

1. Confirm the CHANGE is intentional (humans have reviewed it).
2. Regenerate the relevant baseline, SCOPED to the touched area:

       update_fingerprint_test_results(
           simulation_project=<p>,
           working_directory_filter="examples/ethernet",
           sim_time_limit="10s")

3. Commit the updated store JSON / statistics folder / media
   folder alongside the code change.  Never auto-update baselines
   in CI.

## General agent guardrails

- Always verify `r.is_all_results_done()` / `is_all_results_expected()`
  before reporting "green".  A PASS summary can hide ERRORs in
  sub-sub-results.
- Never `--break-system-packages`; always install into a venv.
- Don't run `update_*_test_results` without an explicit human
  instruction — that overwrites baselines.
- When an `execute_python` call fails, fetch the stderr via
  `print_stderr()` before retrying; do NOT retry blindly with
  higher time limits.
- Prefer `--mcp-port 0` for sub-agent REPLs spawned mid-session.

## See also

- `opp-repl-overview` — skill map.
- `opp-repl-mcp-server` — MCP endpoint details.
- `opp-repl-cli-tools` — shell-only alternative.
- Every task-specific `opp-repl-*` skill referenced above.

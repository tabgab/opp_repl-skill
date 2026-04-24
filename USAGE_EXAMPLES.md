# Usage Examples

Real prompts that trigger the right skills, and what you should
expect back.  Works in Windsurf (via @-mentions or auto-invocation),
Claude Code, Claude Desktop, and any other agent that honours
Anthropic-format Agent Skills.

═══════════════════════════════════════════════════════
SCENARIO 1 — "I'm new to opp_repl. Install it and show me it works."
═══════════════════════════════════════════════════════

Prompt:

> Install opp_repl into my OMNeT++ installation at
> `/home/me/omnetpp-6.4` and run a 0.5-second PureAloha1 to prove
> the setup works.

Skills the agent should load (in order):

1. `opp-repl-overview` (if it's the first turn)
2. `opp-repl-installation`
3. `opp-repl-opp-files` (to write `omnetpp.opp` + `aloha.opp`)
4. `opp-repl-cli-tools` (to run from a shell script)

Expected actions:

```bash
cd /home/me/omnetpp-6.4 && . setenv

# install opp_repl into misc/
git clone https://github.com/omnetpp/opp_repl.git misc/opp_repl
cd misc/opp_repl
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[all]"
. setenv

# write descriptor files (agent uses templates from opp-repl-opp-files)
cat > /home/me/omnetpp-6.4/omnetpp.opp <<'EOF'
OmnetppProject(name="omnetpp", root_folder=".")
EOF

cat > /home/me/omnetpp-6.4/samples/aloha/aloha.opp <<'EOF'
SimulationProject(
    name="aloha", root_folder=".",
    omnetpp_project="omnetpp",
    build_types=["executable"],
    ned_folders=["."], ini_file_folders=["."])
EOF

# verify
cd /home/me/omnetpp-6.4/samples/aloha
opp_run_simulations -c PureAloha1 -t 0.5s --no-concurrent
```

Expected output: a single simulation finishes DONE in ~0.1 s.

═══════════════════════════════════════════════════════
SCENARIO 2 — "My INET fingerprint tests fail. Find the commit."
═══════════════════════════════════════════════════════

Prompt:

> `run_fingerprint_tests(simulation_project=inet_project,
> config_filter="Vlan")` is failing on `HEAD` but worked on `v4.5`.
> Find the commit that broke it and show me the diverging event.

Skills to load:

- `opp-repl-fingerprint-tests`
- `opp-repl-comparing-simulations`
- `opp-repl-tasks-and-results`
- `opp-repl-ai-workflows` (Recipe 2 covers exactly this)

Expected flow inside the REPL (or via MCP execute_python):

```python
# 1. Reproduce
r = run_fingerprint_tests(simulation_project=inet_project,
                          config_filter="Vlan", sim_time_limit="1s")
print(r.get_fail_results())

# 2. Compare HEAD vs known-good
cr = compare_simulations_between_commits(
    inet_project, "v4.5", "HEAD",
    config_filter="Vlan", run_number=0)

first = cr.results[0]
print(first.fingerprint_trajectory_comparison_result)  # DIVERGENT

# 3. Localize the event
first.show_divergence_position_in_sequence_chart()
first.debug_at_fingerprint_divergence_position()

# 4. Then use git bisect on the identified range
```

═══════════════════════════════════════════════════════
SCENARIO 3 — "Tune the SlottedAloha iaTime to hit peak throughput."
═══════════════════════════════════════════════════════

Prompt:

> Run Nelder-Mead to find the iaTime in `Aloha.host[*].iaTime`
> that gets SlottedAloha1 closest to the theoretical peak
> utilisation of 0.368.

Skills to load:

- `opp-repl-parameter-optimization`
- `opp-repl-running-simulations` (for `get_simulation_task`)
- `opp-repl-filtering` (to narrow to SlottedAloha1)

Expected code:

```python
optimize_simulation_parameters(
    get_simulation_task(config_filter="SlottedAloha1",
                        sim_time_limit="10min"),
    expected_result_names=["channelUtilization:last"],
    expected_result_values=[0.368],
    fixed_parameter_names=[], fixed_parameter_values=[],
    fixed_parameter_assignments=[], fixed_parameter_units=[],
    parameter_names=["iaTime"],
    parameter_assignments=["Aloha.host[*].iaTime"],
    parameter_units=["exponential({0}s)"],
    initial_values=[0.5], min_values=[0.1], max_values=[20])
```

Expected output (after ~40 evaluations):

> `Best: {'iaTime': 1.873} -> {'channelUtilization:last': 0.367}`

═══════════════════════════════════════════════════════
SCENARIO 4 — "Distribute a parameter sweep across 2 nodes."
═══════════════════════════════════════════════════════

Prompt:

> I have SSH access to node1.local and node2.local. Run all
> PureAlohaExperiment tasks of the aloha sample distributed across
> both, in release mode.

Skills to load:

- `opp-repl-ssh-cluster`
- `opp-repl-running-simulations`
- `opp-repl-filtering`

Expected code:

```python
from opp_repl.common.cluster import SSHCluster

c = SSHCluster(scheduler_hostname="node1.local",
               worker_hostnames=["node1.local", "node2.local"])
c.start()

p = aloha_project
build_project(simulation_project=p, mode="release")
p.copy_binary_simulation_distribution_to_cluster(
    ["node1.local", "node2.local"])

r = run_simulations(simulation_project=p, mode="release",
                    filter="PureAlohaExperiment",
                    scheduler="cluster", cluster=c)
print(r)
```

Dashboard: http://localhost:8797 (Dask).

═══════════════════════════════════════════════════════
SCENARIO 5 — "Autonomous agent via MCP."
═══════════════════════════════════════════════════════

Prompt to the agent (Claude, Hermes, Cascade, etc.):

> You have an MCP endpoint for opp_repl at
> http://127.0.0.1:9966/mcp. Use `execute_python` to run smoke
> tests on INET's `examples/ethernet/simple`, and if any fail,
> re-run them in debug mode and summarise stderr.

Skills to load:

- `opp-repl-mcp-server`
- `opp-repl-ai-workflows` (Recipe 1)
- `opp-repl-smoke-tests`
- `opp-repl-tasks-and-results`

Expected agent flow:

1. Call `execute_python("r = run_smoke_tests(simulation_project=inet_project, working_directory_filter='examples/ethernet/simple', sim_time_limit='1s'); print(r)")`.
2. If `r.is_all_results_expected()` returns `True`, report success.
3. Otherwise for each failure, call `execute_python("failed = r.get_failed_results(); failed.results[0].rerun(mode='debug'); failed.results[0].print_stderr()")` and summarise.

═══════════════════════════════════════════════════════
SCENARIO 6 — "Set up CI for a simulation project."
═══════════════════════════════════════════════════════

Prompt:

> Add a GitHub Actions workflow that runs smoke tests on every PR
> and fingerprint tests nightly against the main branch of my
> fifo sample.

Skills to load:

- `opp-repl-cli-tools`
- `opp-repl-smoke-tests`
- `opp-repl-fingerprint-tests`
- `opp-repl-github-actions` (for local dispatch helpers)

Expected deliverable: a `.github/workflows/ci.yml` containing:

```yaml
name: opp_repl CI
on: [pull_request, schedule]
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install OMNeT++ + opp_repl
        run: |
          # <distro-specific install>
          pip install "opp_repl[all]"
      - name: Smoke tests
        run: |
          . /opt/omnetpp/setenv
          opp_run_smoke_tests -p fifo -t 1s
  fingerprint:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fingerprint tests
        run: opp_run_fingerprint_tests -p fifo -t 1s
```

═══════════════════════════════════════════════════════
SCENARIO 7 — "Tell me which skill to load for task X."
═══════════════════════════════════════════════════════

Prompt:

> I want to check memory leaks in INET's examples/wireless
> configs.  Which opp_repl skills should I load?

Expected answer (via `opp-repl-overview`):

> `opp-repl-sanitizer-tests` + `opp-repl-running-simulations` +
> `opp-repl-filtering`.

Followed by a one-liner:

```python
run_sanitizer_tests(simulation_project=inet_project,
                    working_directory_filter="examples/wireless",
                    cpu_time_limit="10s")
```

═══════════════════════════════════════════════════════
SCENARIO 8 — "Create an M/M/1/K simulation from scratch
and validate it analytically."  (END-TO-END, WEAK-MODEL FRIENDLY)
═══════════════════════════════════════════════════════

This is the full "build a simulation from zero" flow — the
hardest thing opp_repl agents do.  It mirrors the actual friction
captured in the opp_repl skill-pack's `skilldebug.md` and is
designed so a weaker model can follow step-by-step without
"reasoning from scratch".

Prompt:

> Create a complete OMNeT++ example called Mm1kValidation that
> simulates a finite-buffer M/M/1/K queue (Source -> Queue -> Sink)
> with lambda=0.8, mu=1.0, K=5.  Validate against analytical
> M/M/1/K formulas.

Skills to load (in order, the weak model doesn't have to pick):

1. `opp-repl-overview`              (decision tree)
2. `opp-repl-project-scaffolding`   (CRITICAL — provides the
                                    canonical file set + call order)
3. `opp-repl-opp-files`             (template for the .opp)
4. `opp-repl-running-simulations`   (build + run)
5. `opp-repl-result-analysis`       (read .sca for validation)
6. `opp-repl-troubleshooting`       (on standby for when things break)

### Step 1 — Copy templates from the scaffolding skill

From `opp-repl-project-scaffolding/templates/`, copy and edit:

```
mm1k/
├── mm1k.opp              # from project.opp — change "mm1k" to "mm1k"
├── .oppbuildspec         # from .oppbuildspec — set -o mm1k
├── .nedfolders           # from .nedfolders — leave as "."
├── omnetpp.ini           # from omnetpp.ini — edit configs
├── Mm1k.ned              # from Network.ned — rename network, add Queue
├── Source.h / .cc        # from Source.h / .cc
├── Queue.h  / .cc        # duplicate Source.* and implement M/M/1/K queue
└── Sink.h   / .cc        # duplicate Source.* — collect statistics
```

Keep namespaces OFF in both C++ and NED (simplest; fewest traps).

### Step 2 — Build with the exact opp_repl call sequence

This is the sequence that works.  Do not skip `make_makefiles()`.

```python
# Pre-req: OMNeT++ setenv sourced, opp_repl installed and setenv sourced
# Working directory: /path/to/mm1k

from opp_repl.simulation.build import make_makefiles

# Load project into workspace
load_opp_file("./mm1k.opp")
p = get_simulation_project("mm1k")

# ALWAYS run make_makefiles() before the FIRST build
make_makefiles(simulation_project=p)

# Now build
build_project(simulation_project=p)

# Run 10 replications of 1000 seconds
r = run_simulations(simulation_project=p, sim_time_limit="1000s",
                    repeat_filter=".*")
assert r.is_all_results_done(), r.get_error_results()
```

### Step 3 — Parse results using the bundled script

```python
import subprocess, json
results_dir = p.get_full_path("results")

out = subprocess.check_output([
    "python3",
    "<PATH-to-skill-pack>/opp-repl-result-analysis/scripts/parse_scalars.py",
    results_dir,
    "--group-by", "name",
    "--output", "json",
]).decode()
aggregated = {r["name"]: r for r in json.loads(out)}

sim_drop_prob   = aggregated["Mm1k.snk.dropProbability"]["mean"]
sim_throughput  = aggregated["Mm1k.snk.throughput"]["mean"]
sim_utilization = aggregated["Mm1k.queue.utilization"]["mean"]
sim_E_N         = aggregated["Mm1k.queue.meanN"]["mean"]
```

(Exact scalar names depend on `@statistic(...)` declarations in
the NED file.  See the scaffolding skill's `Network.ned` example
for how to declare them.)

### Step 4 — Analytical validation

```python
# Analytical M/M/1/K
lam, mu, K = 0.8, 1.0, 5
rho = lam / mu
pi = [(1 - rho) / (1 - rho**(K+1)) * rho**n for n in range(K+1)]
pi_drop = pi[K]
analytical_throughput  = lam * (1 - pi_drop)
analytical_utilization = 1 - pi[0]
analytical_E_N         = sum(n * pi[n] for n in range(K+1))

for label, sim, ana in [
    ("drop prob", sim_drop_prob, pi_drop),
    ("throughput", sim_throughput, analytical_throughput),
    ("utilization", sim_utilization, analytical_utilization),
    ("E[N]", sim_E_N, analytical_E_N),
]:
    err = abs(sim - ana) / ana * 100
    print(f"{label:12s}  sim={sim:.4f}  analytical={ana:.4f}  rel err={err:.1f}%")
```

### What breaks (and what skill to reach for)

| If you see                                                    | Load                                        |
|---------------------------------------------------------------|---------------------------------------------|
| `Exception: Building mm1k failed` (no details)                | `opp-repl-troubleshooting` §1               |
| `ERROR (Non-zero exit code: 127)`                             | `opp-repl-troubleshooting` §2               |
| `Class 'Source' not found`                                    | `opp-repl-troubleshooting` §4               |
| `tr.stdout is None` and `tr.stderr is None` on ERROR          | `opp-repl-troubleshooting` §3               |
| Simulation runs but the expected `.sca` columns are missing   | Re-check `@statistic(...)` in Mm1k.ned      |
| Agent wrote a regex .sca parser                               | Use `parse_scalars.py` from `opp-repl-result-analysis` |

This scenario is **intentionally prescriptive** — a weaker model
that only follows the literal steps will still succeed.  Stronger
models can deviate once they understand the pattern.

═══════════════════════════════════════════════════════
PATTERNS
═══════════════════════════════════════════════════════

- Always load `opp-repl-overview` first when you're unsure —
  it routes you to the right siblings.
- For ANY test workflow, `opp-repl-tasks-and-results` is the
  skill that explains the drill-down methods (`get_*_results()`,
  `rerun()`, `print_stderr()`).  Load it early.
- For non-trivial projects, `opp-repl-concepts` +
  `opp-repl-opp-files` + at least one feature skill is the
  minimum useful combination.
- Agents driving opp_repl autonomously should always load
  `opp-repl-ai-workflows` for the pitfall guardrails at the
  bottom of that file.

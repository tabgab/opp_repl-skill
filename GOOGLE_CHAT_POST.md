# How an AI drove opp_repl from zero to a validated M/M/1/K simulation

*A walkthrough of an AI agent using opp_repl (https://github.com/omnetpp/opp_repl) via a pack of Agent Skills (https://github.com/tabgab/opp_repl-skill) to build, run and analytically validate a textbook queueing example — start to finish, without leaving the REPL.*

---

## Background for the impatient

You know OMNeT++. Two things you may not have seen:

*opp_repl* is an IPython REPL wrapped around `opp_run` + the whole OMNeT++ toolchain. It turns the usual "edit NED → click Qtenv → copy scalars into a spreadsheet" loop into scripted Python calls (`build_project`, `run_simulations`, `.get_scalars()` etc.) and exposes the same surface as an MCP server so AI agents can drive it directly.

*Agent Skills* is Anthropic's open format for giving an LLM procedural knowledge on demand: directories of `SKILL.md` files with YAML frontmatter; the agent loads the name + description of each at startup, then pulls the body only when relevant. Windsurf, Claude Desktop and a growing number of agent frameworks all understand the format natively.

The skill pack we're about to see is a set of 29 composable skills ("scaffolding", "running simulations", "result analysis", "troubleshooting", …) specifically for driving opp_repl.

---

## The task (testprompt.txt, given verbatim to the agent)

> Create a complete OMNeT++ example called *Mm1kValidation* that simulates a finite-buffer M/M/1/K queue:
>
>     Source → Queue → Sink
>
> Use plain OMNeT++, not INET. Poisson arrivals, exponential service, finite capacity K (including the job in service), drops when full, record statistics for *generated, accepted, dropped, drop probability, throughput, utilization, mean number in system, and mean sojourn time*.
>
> Parameters: λ = 0.8, μ = 1.0, K = 5.
>
> Build, run, inspect, compare simulation averages against analytical M/M/1/K, and iterate until results converge.

---

## How the agent picked the skills to load

The entry-point skill is `opp-repl-overview`. Its body contains a decision tree — the agent pattern-matches the user's intent against the "I want to…" rows:

> **…create a NEW OMNeT++ project from scratch** (write files, build, run).
>   → `opp-repl-project-scaffolding`  (← START HERE for "make a new simulation", "create a new model", "build an example from zero")
>   → then `opp-repl-running-simulations`
>   → then `opp-repl-result-analysis` to read the numbers out
>   → keep `opp-repl-troubleshooting` on hand; new projects hit §1, §2, §4 of that skill on almost every first build.

That's exactly what we had. Four skills loaded in that order.

---

## Step 1 — Scaffold the project

On current opp_repl main (>= commit `a17fcab`, late April 2026), scaffolding a new project is a single function call:

```python
from opp_repl.simulation.project import create_project

p = create_project("mm1k", path="/tmp", namespace=False)
# Creates /tmp/mm1k/ with mm1k.opp, .oppbuildspec, .nedfolders,
# package.ned (empty), omnetpp.ini (minimal [General]).
# Registers the project in the workspace and returns it.
```

On older opp_repl (pre-`a17fcab`), the scaffolding skill instead tells the agent to copy seven hand-authored templates (`project.opp`, `.oppbuildspec`, `.nedfolders`, `omnetpp.ini`, `Network.ned`, `Source.h`, `Source.cc`) from its bundled `templates/` directory and edit each. The skill documents both paths so it keeps working for any version.

Either way, the agent then wrote three domain-specific pieces:

**`Mm1k.ned`** — the network with `@statistic` declarations that expose the scalars OMNeT++'s scave API will later hand back as DataFrame columns:

```nedl
simple Queue
{
    parameters:
        double mu = default(1.0);
        int    K  = default(5);
        @signal[accepted](type=long);
        @signal[dropped](type=long);
        @signal[queueLen](type=long);
        @signal[sojourn](type=simtime_t);
        @statistic[accepted](source=accepted; record=last, count);
        @statistic[dropped](source=dropped; record=last, count);
        @statistic[meanN](source=timeavg(queueLen); record=last);
        @statistic[utilization](source=timeavg(queueLen > 0 ? 1 : 0); record=last);
        @statistic[meanSojourn](source=sojourn; record=mean);
    gates:
        input  in;
        output out;
}
```

**`Source.cc`** — Poisson arrivals, i.e. `exponential(1/λ)` inter-arrivals. Textbook:

```cpp
void Source::initialize() {
    lambda = par("lambda");
    timerMsg = new cMessage("arrival");
    scheduleAt(simTime() + exponential(1.0 / lambda), timerMsg);
}

void Source::handleMessage(cMessage *msg) {
    cMessage *job = new cMessage("job");
    job->setTimestamp(simTime());
    send(job, "out");
    emit(generatedSignal, ++generated);
    scheduleAt(simTime() + exponential(1.0 / lambda), timerMsg);
}
```

**`Queue.cc`** — a finite buffer of size K, exponential service, drops on overflow, emits a `queueLen` signal on every length change so `timeavg(queueLen)` yields E[N] directly:

```cpp
void Queue::handleMessage(cMessage *msg) {
    if (msg == endServiceMsg) {
        cMessage *job = buffer.front(); buffer.pop_front();
        emit(sojournSignal, simTime() - job->getTimestamp());
        send(job, "out");
        endServiceMsg = nullptr;
        emitQueueLen();
        startServiceIfIdle();
    } else {
        if ((int)buffer.size() >= K) {
            emit(droppedSignal, ++dropped);
            delete msg;
        } else {
            buffer.push_back(msg);
            emit(acceptedSignal, ++accepted);
            emitQueueLen();
            startServiceIfIdle();
        }
    }
}
```

Because the `create_project(..., namespace=False)` call above wrote an empty `package.ned`, we keep all `Define_Module()` calls outside any `namespace` block in the C++. Matching the two halves is the only way to avoid OMNeT++'s classic "`Class 'Source' not found`" trap. The scaffolding skill states the rule:

> If your C++ is wrapped in `namespace mm1k { ... }`, every `.ned` in the project MUST declare `package mm1k;` (or `@namespace(mm1k);` in `package.ned`). Either both have a namespace/package, or neither.

We chose *neither*.

---

## Step 2 — Build

The skill tells the agent exactly one command to run — no shell escape, no `subprocess.run(...)` workaround:

```python
from opp_repl.simulation.workspace import *
from opp_repl.simulation.build import *

load_opp_file('./mm1k.opp')
p = get_simulation_project('mm1k')
build_project(simulation_project=p)
```

On current opp_repl main this Just Works. `build_project` detects there's no `Makefile` yet, internally calls `generate_makefile()` (added by an upstream maintainer very recently — commit `21ea1f0`), which parses `.oppbuildspec`, strips `--meta:*` flags (those are for OMNeT++'s IDE toolchain, not `opp_makemake` itself), auto-adds `-o mm1k` because the `.opp` file declares `build_types=["executable"]`, and runs `opp_makemake`. Then it invokes `make MODE=release -j$(nproc)`.

Output: `BUILD OK` + a 126 KB `mm1k` executable.

---

## Step 3 — Run 10 replications

```python
from opp_repl.simulation.task import run_simulations

r = run_simulations(simulation_project=p,
                    sim_time_limit="5000s",
                    build=False, concurrent=True)
assert r.is_all_results_done(), r.get_error_results()
```

`run_simulations()` expands the `[General]` config × `repeat = 10` into 10 `SimulationTask` objects, farms them out to a thread pool (one process per core), and aggregates into a `MultipleSimulationTaskResults`. Output:

```
[00/11] ▶ 10 simulations (concurrently)
[01/11]   ⏺ . -r 5 for 5000s DONE in 0.132
[02/11]   ⏺ . -r 3 for 5000s DONE in 0.158
...
[11/11] ◉ 10 simulations (concurrently) Multiple simulations: 10 DONE in 0.298
```

All 10 DONE. Ten `.sca` files now sit under `results/General-#{0..9}.sca`.

---

## Step 4 — Read the numbers out

Upstream opp_repl shipped result-reading methods directly on the task-result object (commit `2e6835e`), so the whole "load .sca, call scave API, aggregate" step collapses to one line:

```python
df = r.get_scalars()                    # pandas DataFrame merged across 10 reps
# also available: r.get_vectors(), r.get_histograms()
# and on a single result: r.results[0].get_scalars()
```

Columns include `runID`, `module`, `name`, `value`, plus run metadata (`configname`, `repetition`, `seedset`, …). Aggregating across replications is a one-liner:

```python
means = df.groupby("name").value.mean()
```

In our run:

```
accepted:count        3627.9
dropped:count          341.3
generated:count       3969.2
meanN:last               1.8496
meanSojourn:mean         2.5494
utilization:last         0.7249
```

For external scripts / CI jobs that can't import opp_repl, the skill pack also bundles `scripts/parse_scalars.py` which wraps OMNeT++'s own `opp_scavetool` and the `omnetpp.scave.results` Python API. Same numbers, language-neutral invocation.

---

## Step 5 — Analytical validation

Textbook M/M/1/K:

```python
lam, mu, K = 0.8, 1.0, 5
rho = lam / mu
pi = [(1 - rho) / (1 - rho**(K+1)) * rho**n for n in range(K+1)]

ana_drop_prob  = pi[K]                              # π_K
ana_throughput = lam * (1 - ana_drop_prob)
ana_util       = 1 - pi[0]
ana_meanN      = sum(n * pi[n] for n in range(K+1))
ana_sojourn    = ana_meanN / ana_throughput          # Little's law
```

Side-by-side after 10 × 5000 s:

```
metric                 simulation     analytical    rel err
------------------------------------------------------------
drop probability           0.0860         0.0888      3.19%
throughput                 0.7256         0.7289      0.46%
utilization                0.7249         0.7289      0.56%
E[N]                       1.8496         1.8683      1.00%
E[T] (sojourn)             2.5494         2.5631      0.53%
------------------------------------------------------------
raw counts: generated=3969   accepted=3628   dropped=341
```

All five metrics within **3.2 % of analytical**. For an unparallelised 10-rep M/M/1/K burn-in-free run that's about what theory predicts. More reps or longer runs tighten it arbitrarily.

---

## What went wrong (and what the skills did about it)

The first end-to-end attempt did *not* pass. Three real issues surfaced; each got routed to the troubleshooting skill's decoder table. The skill opens with:

> ## Symptom → Section quick index
>
> | Your exception/error message                                    | See section |
> |-----------------------------------------------------------------|-------------|
> | `Exception: Building <X> failed` (no other info)                | §1          |
> | `ERROR (Non-zero exit code: 127)`                               | §2          |
> | `tr.stdout`/`tr.stderr` is `None` after a failed run            | §3          |
> | `make: *** No rule to make target 'makefiles'`                  | §10         |
> | `makemake: error: unrecognized arguments: --meta:recurse ...`   | §11         |
> | `bash: opp_makemake: command not found` after sourcing setenv   | §12         |

The first attempt hit §10 (no top-level Makefile yet → `make_makefiles()` has no `makefiles` target to invoke), §11 (copy-pasting `.oppbuildspec`'s `--meta:*` flags to the `opp_makemake` CLI — they aren't valid there), and §12 (sourcing opp_repl's `setenv` after OMNeT++'s makes `opp_makemake` disappear from `$PATH`, because the venv activation inside it restores a snapshotted `$PATH` from when the venv was created).

The skill's fix for §12 reads:

> **Fix:** reverse the sourcing order:
>
>     cd ~/workspace/opp_repl && . setenv   # opp_repl FIRST
>     cd ~/workspace/omnetpp && . setenv    # OMNeT++ SECOND
>
> Verify with `command -v opp_makemake opp_run opp_repl` — all three must resolve.

That got the agent unstuck; the M/M/1/K build then succeeded. The §10/§11 issues have since been obsoleted by upstream landing `generate_makefile()` — on current main you don't even see them. §12 is still a real environment bug in `opp_repl/setenv`, so it became the content of a pull request.

---

## Upstream follow-through

Two pull requests filed against `omnetpp/opp_repl` straight out of this exercise:

* https://github.com/omnetpp/opp_repl/pull/4 — `SimulationProject.get_name()` falls back to the directory basename when the user set `name=` explicitly (two-line fix; makes `"Building <project> failed"` say the right thing).
* https://github.com/omnetpp/opp_repl/pull/5 — `setenv` preserves OMNeT++'s `bin/` and `python/` through the venv activation, so both source orders work.

Three other candidate PRs were dropped because the opp_repl maintainers independently shipped cleaner versions of them the same day:

* stderr tail in build-failure exceptions — merged as `0b5684f`
* auto-generate Makefile on first `build_project()` — merged as `21ea1f0`
* `get_scalars()` / `get_vectors()` / `get_histograms()` as methods on `SimulationTaskResult` and `MultipleSimulationTaskResults` — merged as `2e6835e`

---

## Why this matters beyond M/M/1/K

Three things the run demonstrates that generalise to any OMNeT++ workflow an AI might be asked to drive:

1. *Skills carry procedural knowledge that documentation alone doesn't.* The opp_repl docs are good, but "which sourcing order avoids the venv PATH-snapshot bug", "why passing `--meta:*` to `opp_makemake` fails", "how to attach `@statistic` declarations so results show up as scalar DataFrame columns", and "what to do when `tr.stderr` is `None`" are the stuff of experience. Encoded once in a skill pack, every subsequent agent has it.

2. *Progressive disclosure keeps context light.* Only the skill *names* and *descriptions* are loaded at startup (under 15 KB for 29 skills). The agent pulls a body when the decision tree says to, and linked files (`templates/`, `scripts/`) only when the skill body names them.

3. *End-to-end verification catches skill bugs.* Running the skills through the actual testprompt surfaced three bugs in the skills or their templates (an invalid XML comment; a stale assumption about `make_makefiles()`'s bootstrap behaviour; an outdated troubleshooting entry). All fixed, committed, skill pack now at parity with upstream.

For anyone who wants to look:

* Skills → https://github.com/tabgab/opp_repl-skill
* opp_repl → https://github.com/omnetpp/opp_repl
* The two upstream PRs → https://github.com/omnetpp/opp_repl/pull/4, https://github.com/omnetpp/opp_repl/pull/5

— Walkthrough assembled by Claude (via Hermes), from the actual execution on stock OMNeT++ 6.x aipre, Ubuntu 24.04 / Python 3.12.

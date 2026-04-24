# Unnecessary Detours During M/M/1/K Validation Development

This document records the friction points encountered while building,
running, and validating a complete M/M/1/K queueing simulation using
opp\_repl as the sole execution interface.  Each section describes what
happened, the workaround used, and how opp\_repl could eliminate the
detour.

## 1. Makefile Generation Had to Be Done via Raw `subprocess`

**What happened:** After creating all source files and calling
`build_project(simulation_project=p)`, it failed with *"Building mm1k
failed"*.  The cause was simply that no `Makefile` existed yet —
`opp_makemake` had never been run.

**Workaround:** A raw `subprocess.run(["opp_makemake", "--deep", "-f",
"--out", "out"], ...)` call — exactly the kind of shell escape the
workflow was supposed to avoid.

**How opp\_repl could help:** `build_project()` (or
`build_project_using_makefile()`) could detect that no `Makefile` exists
and automatically invoke `opp_makemake` with the options from
`.oppbuildspec` (which was already present and contains the full
`makemake-options` string).  Alternatively, opp\_repl could expose a
`generate_makefile()` function that reads `.oppbuildspec` and runs
`opp_makemake` accordingly.  The information is all there —
`.oppbuildspec` literally contains
`--deep --meta:recurse --meta:export-library ...` — opp\_repl just
doesn't use it.

## 2. Executable Name Mismatch (`omnetpp` vs `mm1k`)

**What happened:** The first `opp_makemake` call (without `-o mm1k`)
produced an executable called `omnetpp` (the default, derived from the
OMNeT++ source tree root name).  But opp\_repl's `SimulationTask`
constructed the command line expecting `./mm1k` (derived from the
project name).  Every run failed with exit code 127: *"nice: execvp: No
such file or directory"*.

**Workaround:** (a) Inspect `tr.subprocess_result` to find the actual
error in stderr, (b) read the generated `Makefile` to see
`TARGET_NAME = omnetpp`, (c) re-run `opp_makemake` with `-o mm1k`,
(d) delete the stale `omnetpp` binary, (e) rebuild.

**How opp\_repl could help:** Since opp\_repl knows the project name is
`mm1k` and `build_types=["executable"]`, it could automatically pass
`-o mm1k` when generating or regenerating the Makefile.  Or, if it
detects the built binary doesn't match the expected executable name, it
could report a clear diagnostic instead of letting the user chase a
cryptic exit-code-127 error.

## 3. Poor Build Error Diagnostics

**What happened:** `build_project()` raised
`Exception: Building mm1k failed` with zero information about *why* it
failed.  The actual cause (no Makefile) was only discoverable by
manually running `make` and reading its stderr.

**Workaround:** `subprocess.run(["make", "MODE=release"], ...,
capture_output=True, text=True)` — then inspecting `result.stderr`.

**How opp\_repl could help:** `build_project_using_makefile()` calls
`run_command_with_logging()` which captures stdout/stderr but only
raises a bare `Exception(error_message)`.  It should include the
captured stderr (or at least the last N lines) in the exception
message, e.g. *"Building mm1k failed: make: \*\*\* No targets specified
and no makefile found."*

## 4. Poor Simulation Error Diagnostics (Exit Code 127)

**What happened:** All 10 runs showed
`ERROR (unexpected) (Non-zero exit code: 127)` but `tr.stdout` and
`tr.stderr` were both `None`.  The actual error message
(`nice: execvp: No such file or directory`) was buried inside
`tr.subprocess_result.stderr`, which had to be discovered by trial and
error.

**Workaround:** Manual inspection of `tr.subprocess_result.stderr`.

**How opp\_repl could help:** `SimulationTaskResult` should always
populate `stdout`/`stderr` from the subprocess result, even when the
process fails before producing any simulation output.  Exit code 127
specifically means "command not found" — opp\_repl could detect this
and produce a targeted message: *"Executable '/home/.../mm1k' not
found.  Was the project built?  Does the binary name match the project
name?"*

## 5. No Built-In Scalar Result Reading

**What happened:** After successful runs, scalar statistics (drop count,
utilization, E\[N\], E\[T\]) needed to be extracted from `.sca` files
to compare against analytical values.  opp\_repl has no function for
reading result files.

**Workaround:** A hand-written regex-based `.sca` parser (~30 lines),
plus manual iteration over all 10 result files, averaging, and
derivation of throughput from accepted count / sim\_time.

**How opp\_repl could help:** A `read_scalars(simulation_project=p)` or
`tr.get_scalars()` function that returns a structured dict or DataFrame
of scalar results would have eliminated the manual parsing entirely.
The `.sca` format is OMNeT++'s own — opp\_repl is the natural place to
parse it.  Similarly, `read_statistics()` for histograms and
`read_vectors()` for time series would complete the picture.  The
`compare_simulations()` feature already compares scalar results
internally, so the parsing logic likely exists — it is just not exposed
to the user.

## 6. No Project Scaffolding

**What happened:** 11 files had to be created from scratch (4 NED,
3 CC, 1 INI, 1 `.opp`, 1 `.oppbuildspec`, 1 `.nedfolders`), with the
exact format of each learned by studying the `fifo` sample.

**How opp\_repl could help:** A
`create_project("mm1k", template="executable")` function could generate
the boilerplate: `.opp`, `.oppbuildspec`, `.nedfolders`, a skeleton
`omnetpp.ini`, and a `Makefile` (or auto-generate it on first build).
This is a minor quality-of-life point — file creation is
straightforward — but it would reduce the chance of format errors in
`.oppbuildspec` etc.

## 7. C++ Namespace / NED Package Mismatch Was Not Detected

**What happened:** The C++ code used
`namespace mm1k { ... Define_Module(Source); ... }`, which registers the
class as `mm1k::Source`.  But the NED files had no `package` declaration,
so the NED type `Source` resolved to the global name `Source`.  The
simulation failed with *"Class 'Source' not found"*.

**Workaround:** Recognizing the cause from experience, then editing all
three `.cc` files to remove the namespace.

**How opp\_repl could help:** This is more of an OMNeT++ toolchain issue
than opp\_repl specifically, but opp\_repl could add a pre-flight check
when a simulation fails with "Class not found": scan the binary's
registered class names (e.g. via `opp_run -a`) and compare against the
NED types used in the network.  A diagnostic like *"NED type 'Source'
not found, but 'mm1k::Source' is registered — did you forget a
`package mm1k;` declaration in your NED files?"* would save significant
debugging time.

## Summary

| # | Detour | Root Cause | Severity | Suggested Fix |
|---|--------|-----------|----------|---------------|
| 1 | Manual `opp_makemake` via subprocess | `build_project()` doesn't generate Makefile | **High** | Auto-run `opp_makemake` from `.oppbuildspec` when Makefile is missing |
| 2 | Wrong executable name | `opp_makemake` default vs project name | **High** | Pass `-o {project_name}` automatically |
| 3 | Opaque build error | Exception discards stderr | **Medium** | Include stderr in exception message |
| 4 | Opaque run error (exit 127) | `stdout`/`stderr` are `None` on early failure | **Medium** | Always populate from subprocess; detect code 127 |
| 5 | Manual `.sca` parsing | No result-reading API | **High** | Expose `read_scalars()` / `tr.get_scalars()` |
| 6 | Manual file scaffolding | No project creation helper | **Low** | `create_project()` template generator |
| 7 | Namespace/package mismatch | No cross-check between NED and C++ | **Low** | Diagnostic hint on "Class not found" errors |

Detours **1, 2, and 5** were the most costly — each required dropping
out of the opp\_repl workflow into raw subprocess calls or manual file
parsing.  Fixing those three would make the
"create → build → run → analyze" loop fully self-contained within
opp\_repl.

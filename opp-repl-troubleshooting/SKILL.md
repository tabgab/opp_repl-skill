---
name: opp-repl-troubleshooting
description: Decode opaque opp_repl errors into actionable fixes. Maps every common failure mode ("Building X failed", exit code 127, "Class not found", scalar/stderr None on ERROR, namespace mismatch) to its root cause and remedy. Load when a build or run fails and the immediate output gives no useful clue — this skill tells you WHERE the real information hides and HOW to extract it without leaving opp_repl. Required companion skill for any non-trivial project work, especially new projects from scratch.
---

# Troubleshooting opp_repl failures

Most opp_repl errors hide the real cause one or two steps away
from the exception message.  This skill is a **lookup table**
from visible symptom to fix.  Start at the section that matches
your symptom.

## Symptom -> Section quick index

| Your exception/error message                                      | See section |
|-------------------------------------------------------------------|-------------|
| `Exception: Building <X> failed` (no other info)                  | §1          |
| `ERROR (Non-zero exit code: 127)`                                 | §2          |
| `tr.stdout` or `tr.stderr` is `None` after a failed run           | §3          |
| `Class '<Name>' not found` inside simulation stderr               | §4          |
| `No such file or directory: .../Makefile`                         | §5          |
| `(executable) not found` / `execvp`                               | §2          |
| Config filter matched, but `num_runs = 1` when INI says more      | §6          |
| `The simulation attempted to prompt for user input`               | §7          |
| Fingerprint/statistical/speed test reports `SKIP`                 | §8          |
| `MCP port already in use` / `Address already in use`              | §9          |
| `make: *** No rule to make target 'makefiles'`                    | §10         |
| `makemake: error: unrecognized arguments: --meta:recurse ...`     | §11         |
| `bash: opp_makemake: command not found` after sourcing setenv     | §12         |

## §1. "Building X failed" with little or no further output

**Root cause (on older opp_repl, before Apr 2026):** no `Makefile`
exists yet.  `build_project()` calls `make MODE=release` which
dies with `No targets specified and no makefile found`, and older
opp_repl's exception discards that stderr.

**On current main this is fixed** — commit 0b5684f includes the
stderr tail in the exception message, and commit 21ea1f0 adds
auto-generation of the Makefile via `generate_makefile()` when
none is present.  `build_project()` now Just Works on a fresh
project with a valid `.opp` + `.oppbuildspec`.

**Fix on older opp_repl:**

    opp_makemake -f --deep -o <project_name>   # bootstrap once
    build_project(simulation_project=p)        # then standard

**Fix on current opp_repl** (if you still see this):

- The exception message should now contain the real `make`
  stderr — read it carefully.
- If the complaint is about missing source files, check
  `.oppbuildspec` is well-formed XML (see §11 below).
- If it mentions `opp_makemake` errors, run
  `opp_makemake --help` and check that your PATH actually has
  `opp_makemake` (see §12 — the setenv order trap).

**Alternative root causes (any opp_repl version):**

- Compiler error — verify by running `make MODE=release` manually in
  the project root; read its stderr.  Typical culprits: missing
  `#include <omnetpp.h>`, wrong C++ standard, missing dependency.
- Dependency project failed to build — `used_projects=["inet"]`
  pulls INET in recursively; a broken INET propagates.

## §2. ERROR (Non-zero exit code: 127)

**Root cause:** The shell tried to execute a program that does not
exist.  OMNeT++ wraps runs in `nice`, so the symptom typically
reads:

    nice: execvp: No such file or directory

Common culprits:

1. **Executable name mismatch.**  `opp_repl` looks for a binary
   named after `simulation_project.name` but `opp_makemake` built
   a binary with a different name.  See
   `opp-repl-project-scaffolding` §"Why the executable is named wrong".
2. **Stale binary after a rename.**  You renamed the project; the
   old binary still sits in the project root.  Fix: `clean_project()`
   or manually `rm -f ./<oldname>` then rebuild.
3. **Wrong `build_types`** — project was built as a dynamic library
   but `.opp` says `build_types=["executable"]`.  Match them.

**How to see the real error:**

    tr = r.results[0]           # the failed SimulationTaskResult
    print(tr.subprocess_result.stderr)   # <-- here is the truth

(`tr.stderr` / `tr.stdout` may be `None` on early failures.  See §3.)

## §3. `tr.stdout` / `tr.stderr` is None after ERROR (older opp_repl)

**On current main (>= commit b9d6494, Apr 2026):** `tr.stdout` and
`tr.stderr` are now always populated from the subprocess result.
This paragraph is for anyone still on older versions.

**Root cause (older opp_repl):** `SimulationTaskResult` only
populated `stdout` and `stderr` from the configured output files
(`cmdenv-output-file`, etc.).  If the simulation died *before*
writing anything (e.g. fork failure, missing binary, dynamic-
library loader error) the files didn't exist, so the fields
stayed `None`.

**Fix on any opp_repl version:** also inspect `subprocess_result`,
which is always populated:

    if tr.result_code == "ERROR":
        sp = tr.subprocess_result
        print(f"exit code: {sp.returncode}")
        print(f"stderr: {sp.stderr}")
        print(f"stdout: {sp.stdout}")
        print(f"args: {sp.args}")  # exact cmd line that failed

Exit codes worth recognising:

| code  | meaning                                                    |
|-------|------------------------------------------------------------|
| 127   | command not found (binary missing or wrong name; see §2)   |
| 126   | command found but not executable (chmod, wrong arch)       |
| 134   | SIGABRT — often an assertion or uncaught C++ exception     |
| 139   | SIGSEGV — crash; build with `mode="sanitize"` to diagnose  |
| 143   | SIGTERM — external kill (CI timeout?)                      |
| 1-2   | simulation raised `cRuntimeError` — see stderr for details |

## §4. "Class '<Name>' not found" during simulation startup

**Root cause (almost always):** NED `package` declaration and C++
`namespace` don't match.

Your C++ has:

    namespace mm1k {
        Define_Module(Source);     // registers as "mm1k::Source"
    }

But your NED has no `package mm1k;` line, so OMNeT++ looks for the
global name `Source` and finds nothing.  (Or vice versa.)

**Diagnostic call:**

    # Which class names are registered in the binary?
    opp_run_release -a omnetpp.ini | grep -i "source"
    # (opp_run_release is on PATH after sourcing OMNeT++ setenv)

**Fix (pick one):**

- Add `package mm1k;` as the first non-comment line in every
  `.ned` file in the project.  This is the idiomatic fix and lets
  the C++ keep its `namespace mm1k { }` wrapper.
- OR remove the `namespace X { ... }` wrapper from every `.cc`
  file that calls `Define_Module(...)`.  All classes then register
  in the root namespace.

Do NOT mix-and-match inside one project.  If some .cc files have
namespaces and some don't, OMNeT++ only finds the ones that match
your .ned declarations.

## §5. Missing Makefile

Typical messages:

- `make: *** No targets specified and no makefile found.  Stop.`
- `FileNotFoundError: .../Makefile`

**Fix:** same as §1 — call `make_makefiles(simulation_project=p)`.
This is ALWAYS safe to re-run; it's idempotent.

## §6. INI says `repeat=N`, opp_repl shows `num_runs=1`

**Root cause:** opp_repl tries OMNeT++'s Python bindings to parse
the INI file first.  If the parse fails (e.g. unknown
configuration option, custom `configuration-class`), it falls back
to running `opp_run -q numruns` — but some custom configs also
fail there.  When BOTH fail, opp_repl logs a warning and uses
`num_runs=1`.

**Fix:**

- Watch the startup log for `WARN Could not determine number of runs`.
- Remove or quote unknown options in `omnetpp.ini`.  A frequent
  offender: `**.with-akaroa = true` on non-Akaroa OMNeT++ builds.
- Manually override per call: `run_simulations(run_number_filter=".*")`
  lists what opp_repl thinks the runs are; if you expect more,
  your INI has a parse issue.

## §7. "The simulation attempted to prompt for user input"

**Root cause:** the simulation hit an unassigned `volatile`
parameter or `cmdenv-interactive=true`.  opp_repl can't answer
prompts, so it flags the run `SKIP`.

**Fix:**

- Assign every NED parameter in `omnetpp.ini` (look for
  `parameter ... has no value` in the stderr).
- Set `cmdenv-interactive = false` in the `[General]` section.

## §8. Test reports SKIP instead of PASS/FAIL

For fingerprint / statistical / speed tests, `SKIP` means "no
baseline exists for this (config, run, time-limit) key".

**Fix:** seed the baseline:

    update_fingerprint_test_results(simulation_project=p, sim_time_limit="1s")
    update_statistical_test_results(simulation_project=p)
    update_speed_test_results(simulation_project=p)
    update_chart_test_results(simulation_project=p)

Then re-run the test.  See `opp-repl-fingerprint-tests` etc. for
the full baseline lifecycle.

## §9. MCP port already in use

**Root cause:** another `opp_repl` process is already bound to
the same port (default `9966`), or a previous one crashed without
releasing it.

**Fix:**

    # Launch without starting an MCP server:
    opp_repl --mcp-port 0 --load "*.opp"

    # Or pick a different port:
    opp_repl --mcp-port 9977 --load "*.opp"

    # Find / kill the stale process:
    lsof -iTCP:9966 -sTCP:LISTEN     # what's bound?
    fuser -k 9966/tcp                # terminate it

In CI always pass `--mcp-port 0`.  This avoids collisions when
multiple jobs run in parallel.

## §10. `make: *** No rule to make target 'makefiles'` (older opp_repl)

**On current main (>= commit 21ea1f0):** no longer relevant —
`build_project()` generates the Makefile from `.oppbuildspec`
when none is present.

**Root cause (older opp_repl):** calling `make_makefiles()` on a
project without an existing Makefile failed, because `make
makefiles` requires a Makefile with that target defined (created
by a prior `opp_makemake` run).

**Fix:**

- On current opp_repl: just call `build_project()` — it handles
  the bootstrap automatically.
- On older opp_repl: bootstrap once with
  `opp_makemake -f --deep -o <project_name>`, then use
  `make_makefiles()` for subsequent regenerations.

See `opp-repl-project-scaffolding` for the complete from-zero
recipe (which works on both old and new).

## §11. `makemake: error: unrecognized arguments: --meta:recurse ...`

**Root cause:** `--meta:*` flags are consumed by the XML parser
that reads `.oppbuildspec` (inside `make makefiles` or inside
`generate_makefile()` on current opp_repl), NOT by `opp_makemake`
directly.  If you copied the `makemake-options` string out of
`.oppbuildspec` and pasted it into a `opp_makemake` CLI call, the
`--meta:*` flags don't resolve.

**Fix:** strip all `--meta:*` flags from the CLI call.  Bootstrap
with the minimal set:

    opp_makemake -f --deep -o <project_name>

Keep `--meta:recurse`, `--meta:export-library`, etc. inside
`.oppbuildspec` where they belong — the XML-driven path
translates them correctly when it parses the file.

### Related: `.oppbuildspec` parse error

If `generate_makefile()` (opp_repl's internal call) fails with:

    xml.etree.ElementTree.ParseError: not well-formed (invalid token):
    line N, column N

then your `.oppbuildspec` has an XML syntax problem.  The most
common cause: XML **comments cannot contain `--`** — so this
block is INVALID:

    <!--  --deep and --meta:recurse ...  -->

Replace comments containing `--` with alternative explanations or
remove them entirely.  See the template in
`opp-repl-project-scaffolding/templates/.oppbuildspec` for a
comment-free valid form.

## §12. `opp_makemake: command not found` after sourcing setenv

**Root cause:** the SETENV ORDER TRAP — see
`opp-repl-installation` §4 PITFALL.  Sourcing opp_repl's setenv
AFTER OMNeT++'s setenv activates opp_repl's `.venv`, which
restores a snapshotted PATH that doesn't have OMNeT++'s `bin/`.

**Fix:** reverse the sourcing order:

    cd ~/workspace/opp_repl && . setenv   # opp_repl FIRST
    cd ~/workspace/omnetpp && . setenv    # OMNeT++ SECOND

Verify with `command -v opp_makemake opp_run opp_repl` — all
three must resolve.

## Generic debug recipe

When you hit an error this skill doesn't cover:

1. **Always** print `tr.subprocess_result.stderr` and
   `tr.subprocess_result.stdout` — they contain the raw output.
2. Check the actual files: `ls results/` for `.sca`/`.vec`/`.out`.
   `.out` files are line-by-line cmdenv logs.
3. Re-run the single failing task in `mode="debug"` to get less
   stripped-down error messages:
   `failed.rerun(mode="debug")`.
4. Try the equivalent `opp_run` call by hand — look at the
   arguments opp_repl used:

       print(tr.subprocess_result.args)
       # e.g. ['opp_run_release', '-u', 'Cmdenv', '-r', '0',
       #      '-c', 'General', 'omnetpp.ini']

   Run that command directly in a shell at the simulation's
   working directory.  The full OMNeT++ stderr appears there.

5. Only if all of the above fail: enable verbose logging.

       opp_repl -l DEBUG --external-command-log-level DEBUG ...

## See also

- `opp-repl-project-scaffolding` — prevents most §1, §2, §4, §5 errors.
- `opp-repl-result-analysis` — when runs succeed but results look wrong.
- `opp-repl-tasks-and-results` — `TaskResult` fields and rerun APIs.
- `opp-repl-running-simulations` — the run pipeline that produces these errors.

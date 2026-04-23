---
name: opp-repl-repl-usage
description: Launch and drive the opp_repl IPython REPL — CLI flags (--load, -p, --mcp-port, -l), pre-loaded namespace, {name}_project convenience variables, autoreload, per-user module auto-import, stop_execution(), and tab completion. Load when working interactively rather than via shell wrappers or MCP.
---

# The interactive REPL

`opp_repl` is an IPython shell with every opp_repl public function
imported into the top-level namespace, plus convenience variables
for every loaded project and a handful of REPL-specific ergonomics.

Upstream references:
- https://github.com/omnetpp/opp_repl/blob/main/doc/repl.md
- https://github.com/omnetpp/opp_repl/blob/main/doc/getting_started.md

## Launching

    opp_repl --load ~/workspace/omnetpp/omnetpp.opp \
             --load ~/workspace/inet/inet.opp

Glob patterns are allowed and `--load` can be repeated:

    opp_repl --load "~/workspace/omnetpp/samples/*/*.opp"

## CLI flags

| Flag                             | Effect                                                |
|----------------------------------|-------------------------------------------------------|
| `--load FILE_OR_GLOB`            | Load `.opp` descriptor(s); repeatable.                |
| `-p NAME`                        | Set default simulation project by name.               |
| `--mcp-port PORT`                | Start MCP server on PORT (0 = disabled; default on).  |
| `-l LEVEL`                       | Log level: ERROR, WARN, INFO, DEBUG.                  |
| `--external-command-log-level L` | Log level for simulation and build tool output.       |
| `--no-handle-exception`          | Show full Python tracebacks instead of short errors.  |

## Pre-loaded namespace

On startup every public symbol from `opp_repl` is imported at the
top level — call them without a prefix:

    run_simulations(sim_time_limit="1s")
    run_smoke_tests()
    build_project()
    compare_simulations(simulation_project_1=a, simulation_project_2=b)

Press TAB after any partial name to auto-complete function names,
method names, and keyword arguments.

## Convenience variables

Every loaded project is injected as `{name}_project`, with hyphens
and dots turned into underscores:

- `inet.opp`           --> `inet_project`
- `simu5g.opp`         --> `simu5g_project`
- `omnetpp-6.3.0.opp`  --> `omnetpp_6_3_0_project`

List them: `get_simulation_project_variable_names()`.

## Defaults

If the current working directory is inside a loaded project's tree,
that project is auto-set as default.  Otherwise set explicitly:

    set_default_simulation_project(aloha_project)

Or on the command line: `-p aloha`.

## Autoreload

IPython's `%autoreload 2` is enabled at startup.  Editing Python
source files (your own helpers or opp_repl itself) picks up changes
before the next command — no restart required.

## User module auto-import

At startup the REPL tries `import <unix-login-name>`, e.g.
`import alice` if `$USER` is `alice`.  If the module exists, every
public name is injected into the namespace.  This is the blessed
mechanism for per-user helpers, project defaults, and shortcuts —
no need to fork opp_repl.

## Stopping execution cleanly

Inside a multi-line REPL script, call `stop_execution()` (or
`stop_execution(value)`) to abort the current cell without a
full traceback.  Useful for early exits from sourced scripts.

## Scripting non-interactively

`opp_repl` accepts stdin and runs each line as in an interactive
session.  Pipe a heredoc for one-shot scripted runs:

    opp_repl --mcp-port 0 --load aloha.opp <<'EOF'
    r = run_simulations(config_filter="PureAloha1", sim_time_limit="0.3s")
    print(r)
    exit
    EOF

For CI where IPython-specific features are not needed, prefer the
shell wrappers — see `opp-repl-cli-tools`.

## Pitfalls

- `--mcp-port` defaults to an active port; set `--mcp-port 0` in CI
  or in parallel test runs to avoid port-collision errors.
- The user-module auto-import is silent when the module is missing.
  If your helpers don't load, check your OS login name vs. module
  name.
- Running `opp_repl` without `--load` and not inside a project tree
  gives you a bare REPL — the `{name}_project` variables only
  appear after `load_opp_file()`.

## See also

- `opp-repl-installation` — prerequisites.
- `opp-repl-concepts` — the object model.
- `opp-repl-running-simulations` — `run_simulations()` in detail.
- `opp-repl-cli-tools` — non-interactive shell equivalents.
- `opp-repl-mcp-server` — expose the REPL to AI agents.

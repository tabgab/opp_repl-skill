---
name: opp-repl-mcp-server
description: Connect an AI agent to opp_repl via the built-in Model Context Protocol (MCP) server. Exposes execute_python plus opp-repl:// resources (guides, packages, classes, methods, functions) over streamable HTTP at /mcp. Load when integrating opp_repl as an MCP tool endpoint into Claude Desktop, Claude Code, Cursor, a custom agent, or any MCP-capable client.
---

# MCP server for AI assistants

opp_repl ships an MCP (Model Context Protocol) server that lets an
AI assistant execute Python code in the live IPython session and
browse auto-generated documentation resources.  It runs over
streamable HTTP, so any MCP client that speaks the HTTP transport
can connect.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/mcp_server.md

## Requirements

    pip install "opp_repl[mcp]"

## Starting the server

Start alongside the REPL:

    opp_repl --mcp-port 9966 --load "etc/*.opp"

- Default: the MCP server is enabled on startup (port varies by
  version; `9966` is the conventional value).
- Disable: `--mcp-port 0`.  Always disable in CI or parallel test
  runs to avoid port collisions.

Transport: **streamable HTTP, stateless**.
Endpoint: `http://127.0.0.1:{port}/mcp`.

## Tools

### `execute_python(code: str) -> str`

Execute arbitrary Python code in the live IPython kernel.  The
code runs in the SAME namespace that interactive users see — all
opp_repl functions, every loaded project's `{name}_project`
variable, and any state previously set in the session.

Returns captured stdout + stderr.  If the code is a single
expression, its `repr` is returned.

Example agent-side call (conceptual):

    execute_python('''
    r = run_simulations(simulation_project=aloha_project,
                        config_filter="PureAloha1",
                        sim_time_limit="1s")
    print(r)
    print(r.get_error_results())
    ''')

## Resources

Guides are served as markdown; API docs are auto-generated from
the live package.

### Guide resources

| URI                            | Description                                       |
|--------------------------------|---------------------------------------------------|
| `opp-repl://guides`            | List of guide topics with 1-paragraph summaries   |
| `opp-repl://guide/{topic}`     | Read one guide (e.g. `fingerprint_tests`, `concepts`) |

### API reference resources

| URI                                              | Description                                       |
|--------------------------------------------------|---------------------------------------------------|
| `opp-repl://packages`                            | List of opp_repl sub-packages with summaries      |
| `opp-repl://package/{package_name}`              | Package docstring + per-class summaries           |
| `opp-repl://class/{class_name}`                  | Full class doc + method signatures                |
| `opp-repl://method/{class_name}/{method_name}`   | One complete method docstring                     |
| `opp-repl://function/{function_name}`            | One complete function docstring                   |

Names can be fully qualified (e.g.
`opp_repl.simulation.workspace.SimulationWorkspace`) or short public
names (e.g. `SimulationWorkspace`).

## Recommended discovery flow for an AI agent

1. Read `opp-repl://guides` to learn which task-level guides exist.
2. Read `opp-repl://guide/{topic}` for concrete examples.
3. Read `opp-repl://packages` to find the relevant sub-package.
4. Read `opp-repl://package/{name}` for a compact API overview.
5. Drill into `opp-repl://class/...` /
   `opp-repl://function/...` for full signatures.
6. Call `execute_python(...)` with the chosen approach.

## Wiring into agent frameworks

- **Claude Desktop / Claude Code**: add an MCP server block with
  `url: http://127.0.0.1:9966/mcp`.
- **mcporter / custom agents**: call
  `mcporter call --url http://127.0.0.1:9966/mcp execute_python
  --code='...'`.
- **Hermes / Agent Zero / Windsurf** etc.: register the endpoint
  in the agent's MCP config.

## Pitfalls

- The MCP session is LIVE and STATEFUL (state persists across
  `execute_python` calls within one REPL process).  Two agents
  connecting to the same port will stomp on each other's state —
  run one REPL per agent or share deliberately.
- Port collisions: ALWAYS pass `--mcp-port 0` in CI.
- Because `execute_python` runs arbitrary code in the user's
  Python, treat the endpoint as privileged.  Don't expose it on
  public networks unsandboxed.
- Streamable HTTP is stateless at the HTTP level but the kernel
  state is persistent.  Closing the MCP client does NOT reset the
  REPL.

## See also

- `opp-repl-repl-usage` — driving the same kernel from a terminal.
- `opp-repl-ai-workflows` — end-to-end recipes for AI integration.
- `opp-repl-overview` — map of which skills to load when.

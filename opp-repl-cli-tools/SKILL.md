---
name: opp-repl-cli-tools
description: Use the opp_repl shell wrappers (opp_build_project, opp_run_simulations, opp_run_*_tests, opp_update_*_test_results) from scripts and CI pipelines instead of the IPython REPL. Load for non-interactive workflows — covers shared flags, project auto-detection from CWD, filtering, build modes, and exit codes.
---

# Command-line tools (shell wrappers)

Every long-running opp_repl operation has a matching shell wrapper.
Use them in scripts, Makefiles, CI jobs, and any context where
starting IPython is overkill.

Upstream reference (bundled in the overview):
https://github.com/omnetpp/opp_repl/blob/main/doc/overview.md

## Tool inventory

| Binary                                | Purpose                                      |
|---------------------------------------|----------------------------------------------|
| `opp_repl`                            | IPython REPL (see `opp-repl-repl-usage`)     |
| `opp_build_project`                   | Build a project (and its dependencies)       |
| `opp_run_simulations`                 | Run simulations (with filters, time limits)  |
| `opp_run_all_tests`                   | Run every test type sequentially             |
| `opp_run_smoke_tests`                 | Start-and-terminate checks                   |
| `opp_run_fingerprint_tests`           | Behavioral regression (event fingerprints)   |
| `opp_run_statistical_tests`           | Scalar-result regression                     |
| `opp_run_speed_tests`                 | CPU instruction-count regression             |
| `opp_run_chart_tests`                 | Chart image regression                       |
| `opp_run_sanitizer_tests`             | AddressSanitizer / UBSan runs                |
| `opp_run_feature_tests`               | Per-feature build + setup checks             |
| `opp_run_release_tests`               | Comprehensive release-validation suite       |
| `opp_update_fingerprint_test_results` | Refresh fingerprint baseline                 |
| `opp_update_speed_test_results`       | Refresh speed baseline                       |
| `opp_update_statistical_test_results` | Refresh scalar baseline                      |
| `opp_update_chart_test_results`       | Refresh chart-image baseline                 |

All accept `-h` / `--help` and share a common flag set.

## Project loading

- No `--load` flag? -> every `*.opp` in the current working
  directory is auto-loaded.  The typical pattern is `cd` into the
  project and run:

      cd ~/workspace/inet && opp_run_simulations -p inet -t 1s

- One or more `--load` flags:

      opp_run_simulations --load ~/ws/omnetpp/omnetpp.opp \
                          --load ~/ws/inet/inet.opp \
                          -p inet -t 1s

Globs are accepted:

      opp_run_simulations --load "~/workspace/**/*.opp" -p fifo

OMNeT++ project descriptors are always loaded before simulation
projects so dependencies resolve automatically.

## Common flags

| Flag                               | Meaning                                         |
|------------------------------------|-------------------------------------------------|
| `-p NAME`                          | Default simulation project                      |
| `--load FILE_OR_GLOB`              | Load `.opp` descriptor (repeatable)             |
| `-t DURATION`                      | `sim_time_limit` (`1s`, `10min`, ...)           |
| `--filter REGEX`                   | Full-string filter                              |
| `--working-directory-filter REGEX` | Filter by working directory                     |
| `--ini-file-filter REGEX`          | Filter by INI filename                          |
| `--config-filter REGEX`            | Filter by `[Config X]` name                     |
| `--run-number-filter REGEX`        | Filter by run number                            |
| `--exclude-*` variants             | Same semantics, inverted                        |
| `-m MODE`                          | release / debug / sanitize / coverage / profile |
| `--no-build`                       | Skip build step (use existing binary)           |
| `--no-concurrent`                  | Sequential execution                            |
| `--hosts H1,H2,...`                | SSH cluster hosts (requires `cluster` extra)    |

See `opp-repl-filtering` for the complete filter vocabulary — the
include/exclude rules are identical to the REPL functions.

## Exit codes

The wrappers exit 0 when the overall result is expected (all DONE
for simulations, all PASS for tests) and non-zero otherwise.  In CI
pipelines, rely on the exit code rather than parsing stdout.

## Examples

Run PureAloha1 once, short duration, no rebuild:

    cd $__omnetpp_root_dir/samples/aloha
    opp_run_simulations -c PureAloha1 -t 0.3s --no-build --no-concurrent

Smoke-test the whole fifo sample:

    cd $__omnetpp_root_dir/samples/fifo
    opp_run_smoke_tests

Fingerprint-test INET under examples/ethernet:

    opp_run_fingerprint_tests --load ~/ws/inet/inet.opp -p inet \
                              --working-directory-filter examples/ethernet \
                              -t 10s

Run distributed on a 2-node cluster in debug mode:

    opp_run_simulations -m debug -t 1s \
                        --filter PureAlohaExperiment \
                        --hosts node1.local,node2.local

## Pitfalls

- `--no-build` with a stale binary silently runs the old code.  Prefer
  omitting the flag unless you are certain the binary is current.
- The wrappers do NOT start an MCP server.  If an AI agent needs
  access, start `opp_repl --mcp-port 9966` instead.
- `-t` overrides any `sim-time-limit` in the INI file — including
  longer limits that the config deliberately needed.

## See also

- `opp-repl-repl-usage` — equivalent interactive interface.
- `opp-repl-running-simulations` — full semantics of the run step.
- `opp-repl-filtering` — complete filter reference.
- Each `opp-repl-*-tests` skill — test-specific flags.

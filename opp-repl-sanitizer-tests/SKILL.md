---
name: opp-repl-sanitizer-tests
description: Run simulations built with AddressSanitizer / UBSan instrumentation to catch memory errors and undefined behavior. Uses the `sanitize` build mode. Load when hunting down flaky crashes, UAFs, leaks, or UB that normal release builds miss.
---

# Sanitizer tests

Sanitizer tests build the simulation with AddressSanitizer and
UndefinedBehaviorSanitizer (`sanitize` build mode) and run it.  Any
detected issue is captured in stderr and reported as an ERROR.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/sanitizer_tests.md

## Python API

    run_sanitizer_tests(simulation_project=inet_project)

    # Scope + longer CPU budget (sanitizer builds are slow)
    run_sanitizer_tests(simulation_project=inet_project,
                        working_directory_filter="examples/ethernet",
                        cpu_time_limit="10s")

## Command line

    opp_run_sanitizer_tests --load inet.opp -p inet

## Cost model

Sanitizer binaries run 2x-10x slower and use more memory.  Keep
`cpu_time_limit` tight and scope to affected areas.  Nightly CI is
a better fit than per-commit runs.

## Interpreting failures

When ASAN reports, the error text appears in the result's
`stderr`.  `print_stderr()` on the failing `TaskResult` dumps it.
Typical patterns:

- `heap-use-after-free` / `heap-buffer-overflow` -- memory lifetime
  bug in a C++ module.
- `undefined-behavior` from UBSan -- signed overflow, misaligned
  access, invalid enum cast, etc.
- `runtime error: load of null pointer` -- dereferencing a NULL
  pointer during cleanup.

## Pitfalls

- Compiler and sanitizer-runtime versions affect output format;
  keep the toolchain stable across baseline and CI.
- Some third-party libraries leak on purpose; suppress via
  `LSAN_OPTIONS=suppressions=...` when running.
- Sanitizer builds cannot be used for speed tests or coverage —
  each is a separate build mode.

## See also

- `opp-repl-running-simulations` — underlying build/run machinery.
- `opp-repl-tasks-and-results` — inspect stderr on ERROR.
- `opp-repl-feature-and-release-tests` — run as part of a full suite.

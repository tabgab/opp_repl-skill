---
name: opp-repl-profiling
description: Profile simulation performance using Linux perf and visualize with KDAB Hotspot. open_profile_report / generate_profile_report run the simulation under `perf record -g --call-graph dwarf` and emit perf.data. Uses the `profile` build mode. Load when diagnosing why a simulation is slow or verifying an optimization.
---

# Profiling

Profile simulations with Linux `perf` and view the call-graph in
`hotspot`.  Uses the `profile` build mode (binary suffix
`_profile`, typically with frame pointers enabled).

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/profiling.md

## Python API

    # Build + run + open hotspot
    open_profile_report(simulation_project=inet_project,
                        working_directory_filter="examples/ethernet",
                        config_filter="General",
                        run_number=0,
                        sim_time_limit="10s")

    # Build + run, return the perf.data path
    f = generate_profile_report(simulation_project=inet_project,
                                working_directory_filter="examples/ethernet",
                                config_filter="General",
                                run_number=0,
                                sim_time_limit="10s")

Both wrap `perf record -g --call-graph dwarf` and write
`perf.data` into the simulation's working directory.  Override the
filename with `output_file=`.

## Requirements

- Linux with `perf` enabled and accessible.  `perf_event_paranoid`
  may need to be relaxed:

      sudo sysctl -w kernel.perf_event_paranoid=1

- Hotspot (`hotspot` package or AppImage) on PATH for
  `open_profile_report()`.

## Reading the report

- Bottom-up view in Hotspot shows the hottest functions.
- Flame graph (via Hotspot or `perf script | stackcollapse-perf.pl`)
  reveals call stacks.
- For OMNeT++ sims, expect most time in `cMessage` dispatch, RNG,
  and your C++ modules.

## Pitfalls

- `perf record -g --call-graph dwarf` needs DWARF debug info —
  always build with `-g` on top of `-O2`.
- Without frame pointers and with LTO, stacks may be truncated.
  Add `-fno-omit-frame-pointer` to the `profile` mode's CXXFLAGS.
- Profiling on a loaded machine is noisy; pin to one CPU with
  `taskset -c 0` when possible.

## See also

- `opp-repl-speed-tests` — regression dashboard for wall/cpu time.
- `opp-repl-running-simulations` — selecting the single task to
  profile.

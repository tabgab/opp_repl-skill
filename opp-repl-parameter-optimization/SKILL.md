---
name: opp-repl-parameter-optimization
description: Find simulation parameter values that produce desired results using derivative-free optimization (scipy Nelder-Mead). optimize_simulation_parameters iteratively runs a single SimulationTask varying parameters until expected result vectors are met. Requires the `optimize` extra. Load when tuning a simulation to hit a target throughput, error rate, utilization, etc.
---

# Parameter optimization

`optimize_simulation_parameters()` pairs a single simulation task
with a scipy-based Nelder-Mead solver.  At each iteration the
optimizer picks new parameter values, runs the simulation, reads
the target scalars, and minimizes the difference from the
expected values.  No gradients needed -- suitable for stochastic
simulations.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/parameter_optimization.md

Requires the `optimize` extra (`scipy`, `optimparallel`):

    pip install "opp_repl[optimize]"

## Signature (keyword-only)

    optimize_simulation_parameters(
        simulation_task,                   # result of get_simulation_task(...)
        expected_result_names=[...],       # scalar names to hit
        expected_result_values=[...],      # target values
        fixed_parameter_names=[...],       # optional -- held constant
        fixed_parameter_values=[...],
        fixed_parameter_assignments=[...], # INI-style path
        fixed_parameter_units=[...],
        parameter_names=[...],             # what to vary
        parameter_assignments=[...],       # INI-style path for each
        parameter_units=[...],             # format string(s); see below
        initial_values=[...],
        min_values=[...], max_values=[...],
    )

## Unit format strings

- Plain unit: `"m"`, `"Mbps"` -- appended to the numeric value.
- Distribution wrapper: `"exponential({0}s)"` -- preserves an
  iaTime distribution while overriding its parameter.
- Any `.format(value)`-compatible string.

This matters because many OMNeT++ parameters are declared
`volatile` and assigned distributions in the INI file.  The unit
wrapper keeps the distribution intact.

## Example 1 — slotted ALOHA channel utilization

Maximize channel utilization in slotted ALOHA.  Theoretical peak
is 1/e ≈ 0.368 at iaTime ≈ 1.87 s.  From overloaded start (0.5 s),
converges in ~40 evaluations:

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

Output ends with:

    Best: {'iaTime': 1.873} -> {'channelUtilization:last': 0.367}

## Example 2 — INET WiFi range at 30 % PER

Find the distance where 54 Mbps WiFi reaches 30 % packet error.
Converges to ~53.2 m in ~28 evaluations:

    optimize_simulation_parameters(
        get_simulation_task(simulation_project=inet_project,
            working_directory_filter="showcases/wireless/errorrate",
            config_filter="General", run_number=0, sim_time_limit="1s"),
        expected_result_names=["packetErrorRate:vector"],
        expected_result_values=[0.3],
        fixed_parameter_names=["bitrate"], fixed_parameter_values=[54],
        fixed_parameter_assignments=["**.bitrate"],
        fixed_parameter_units=["Mbps"],
        parameter_names=["distance"],
        parameter_assignments=["*.destinationHost.mobility.initialX"],
        parameter_units=["m"],
        initial_values=[50], min_values=[20], max_values=[100])

## Pitfalls

- Stochastic noise dominates near the optimum.  Lengthen
  `sim_time_limit` or average several runs per evaluation (repeat
  count in the INI) when results get noisy.
- `get_simulation_task()` MUST match exactly one task.  Ambiguous
  filters raise -- add `run_number=0` or tighter filters.
- Bounds and initial values should straddle the expected optimum.
  Nelder-Mead can get stuck if the initial simplex is far from the
  feasible region.
- Each evaluation is a full simulation run; budget accordingly.
- Multi-dimensional optimization (several `parameter_names`) scales
  roughly O(n²) in simplex size; stay ≤ 4-5 parameters for sanity.

## See also

- `opp-repl-running-simulations` — `get_simulation_task()` semantics.
- `opp-repl-tasks-and-results` — reading result scalars.
- `opp-repl-ssh-cluster` — distribute parallel evaluations.

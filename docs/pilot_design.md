# MetroPulse Pilot Design

## Initiative 1 — Airport-Focused Capacity Allocation

### Objective

Test whether targeted additional capacity during the airport-focused afternoon operating window improves completed-trip productivity.

### Experimental Unit

The preferred unit is the operating shift / vehicle-hour assigned to the eligible airport operating zone or airport-focused service pool.

Randomization should occur at the operational unit level to reduce contamination between treatment and control.

### Treatment

Treatment units receive the planned incremental capacity allocation during the selected airport-focused operating window.

### Control

Control units continue under the existing capacity-allocation policy.

### Primary Metric

**Completed airport trips per available vehicle-hour.**

This metric is preferred over raw trip counts because raw trips can increase simply because more vehicle-hours are supplied.

### Guardrails

Monitor:

- non-airport trip productivity
- revenue per vehicle-hour
- service quality / wait-time proxy where available
- post-window service performance
- vehicle utilization

The intervention should not be considered successful if airport productivity improves while materially degrading citywide service.

### MDE / Sample-Size Reasoning

The historical dataset is observational and does not contain a randomized treatment/control experiment. Therefore a definitive experimental sample size cannot be claimed from historical averages alone.

Before launch, estimate the baseline mean and standard deviation of the primary metric at the proposed experimental-unit level.

For a two-sided comparison with equal-sized treatment and control groups, the approximate per-group sample size is:

```text
n ≈ 2 × (z_(1-α/2) + z_(1-β))² × σ² / δ²

where:

α = significance level
1-β = target statistical power
σ = baseline standard deviation of the primary metric
δ = minimum detectable effect

A practical planning target is:

α = 0.05
power = 0.80

The business should select the MDE based on the minimum productivity improvement that would justify the incremental operating cost.

The final sample size must be recalculated from the actual pilot-unit baseline variance before launch.

Stopping Rule

Do not repeatedly stop and restart the experiment based on interim significance.

Pre-specify:

pilot duration
minimum number of experimental units
primary metric
significance threshold
guardrail thresholds

Early termination is allowed only for:

a pre-defined safety/service failure,
a severe operational issue,
or a pre-defined overwhelming-effect boundary established before launch.
Decision Rule

Proceed to scale if:

the treatment effect on completed airport trips per available vehicle-hour is positive and statistically credible;
the estimated effect meets or exceeds the pre-specified MDE;
no material guardrail is breached.

If the primary metric fails to meet the MDE or a material guardrail deteriorates, do not scale the intervention without further investigation.

Initiative 2 — Citywide Evening Peak Capacity Planning
Objective

Test whether planned incremental capacity during the citywide evening peak improves completed-trip productivity.

Experimental Unit

The preferred unit is a comparable operating zone-shift or vehicle-shift.

Randomization should occur at the operational-unit level where feasible.

Treatment

Treatment units receive incremental capacity during the selected evening peak window.

Control

Control units remain under the existing capacity policy.

Primary Metric

Completed trips per available vehicle-hour.

Again, this avoids interpreting higher raw trip counts as improved productivity when additional supply itself may explain the increase.

Guardrails

Monitor:

revenue per vehicle-hour
trip completion
service quality / wait-time proxy
post-peak demand performance
utilization
non-peak service coverage
MDE / Sample-Size Reasoning

Use the same two-arm planning framework:

n ≈ 2 × (z_(1-α/2) + z_(1-β))² × σ² / δ²

with:

α = 0.05
power = 0.80

The MDE should be defined as the smallest increase in completed trips per available vehicle-hour that would economically justify the incremental capacity.

Because the current historical dataset is observational, the final MDE and sample-size calculation should be performed using the actual experimental-unit baseline variance immediately before the pilot.

Stopping Rule

Pre-specify the experiment duration and minimum sample size.

Do not terminate early merely because an interim result becomes statistically significant.

Terminate early only for:

predefined operational/safety failures,
predefined severe guardrail breaches,
or a pre-specified overwhelming-effect boundary.
Decision Rule

Scale the intervention only if:

the treatment improves completed trips per available vehicle-hour;
the effect meets the pre-specified MDE;
the confidence interval supports a practically meaningful improvement;
guardrails remain within their pre-defined limits.

If these conditions are not met, retain the existing capacity policy or redesign the intervention.

Important Limitation

MetroPulse historical data does not directly observe randomized capacity assignment, vehicle supply, unmet demand, driver acceptance, or passenger wait time.

Therefore the historical analysis supports where and when to run an experiment, but does not by itself establish that incremental capacity will cause the proposed productivity improvement.
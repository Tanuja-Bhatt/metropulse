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

### Pilot Duration

**4 weeks.**

The pilot should run for four consecutive weeks covering the selected airport-focused operating window. Treatment and control assignments should remain fixed for the pilot unless a pre-specified operational safety rule requires intervention.

### MDE / Sample-Size Reasoning

The historical dataset is observational and does not contain randomized treatment/control assignment or vehicle-hour supply. Therefore a definitive experimental sample size cannot be estimated directly from historical trip counts.

Before launch:

1. Estimate the baseline mean and standard deviation of completed airport trips per available vehicle-hour at the actual experimental-unit level.
2. Select the minimum detectable effect (MDE) as the smallest productivity improvement that would justify the incremental operating cost.
3. Calculate the required sample size for a two-sided comparison with equal-sized treatment and control groups:

```text
n ≈ 2 × (z_(1-α/2) + z_(1-β))² × σ² / δ²
```

where:

- α = 0.05 significance level
- 1-β = 0.80 statistical power
- σ = baseline standard deviation of the primary metric
- δ = pre-specified minimum detectable effect

The required number of experimental units should then be inflated for expected attrition, non-compliance, or unusable observations.

The final sample-size calculation must be completed before treatment assignment using the actual pilot-unit baseline variance.

If the required sample cannot be achieved within the four-week pilot, the experiment should be redesigned rather than treated as adequately powered.

### Stopping Rule

The pilot runs for the full **4-week period** unless a pre-defined safety, service, or operational failure requires early termination.

Do not repeatedly stop and restart the experiment based on interim statistical significance.

Before launch, pre-specify:

- 4-week pilot duration
- minimum number of experimental units
- primary metric
- MDE
- significance threshold
- guardrail thresholds

Early termination is allowed only for:

- a pre-defined safety/service failure
- a severe operational issue
- a pre-defined overwhelming-effect boundary established before launch

### Decision Rule

Proceed to scale if:

- the treatment effect on completed airport trips per available vehicle-hour is positive and statistically credible
- the estimated effect meets or exceeds the pre-specified MDE
- no material guardrail is breached

If the primary metric fails to meet the MDE or a material guardrail deteriorates, do not scale the intervention without further investigation.

---

## Initiative 2 — Citywide Evening Peak Capacity Planning

### Objective

Test whether planned incremental capacity during the citywide evening peak improves completed-trip productivity.

### Experimental Unit

The preferred unit is a comparable operating zone-shift or vehicle-shift.

Randomization should occur at the operational-unit level where feasible.

### Treatment

Treatment units receive incremental capacity during the selected evening peak window.

### Control

Control units remain under the existing capacity policy.

### Primary Metric

**Completed trips per available vehicle-hour.**

Again, this avoids interpreting higher raw trip counts as improved productivity when additional supply itself may explain the increase.

### Guardrails

Monitor:

- revenue per vehicle-hour
- trip completion
- service quality / wait-time proxy
- post-peak demand performance
- utilization
- non-peak service coverage

### Pilot Duration

**4 weeks.**

The pilot should run for four consecutive weeks covering the selected citywide evening peak window. Treatment and control assignments should remain fixed for the pilot unless a pre-specified operational safety rule requires intervention.

### MDE / Sample-Size Reasoning

The historical dataset is observational and does not contain randomized capacity assignment or vehicle-hour supply. Therefore historical trip counts cannot be used to claim a definitive experimental sample size.

Before launch:

1. Estimate the baseline mean and standard deviation of completed trips per available vehicle-hour at the actual experimental-unit level.
2. Define the MDE as the smallest increase in completed trips per available vehicle-hour that would economically justify the incremental capacity.
3. Calculate the required sample size for equal-sized treatment and control groups using:

```text
n ≈ 2 × (z_(1-α/2) + z_(1-β))² × σ² / δ²
```

with:

- α = 0.05 significance level
- 1-β = 0.80 statistical power
- σ = baseline standard deviation of the primary metric
- δ = pre-specified minimum detectable effect

The required number of experimental units should then be inflated for expected attrition, non-compliance, or unusable observations.

The final sample-size calculation must be completed before treatment assignment using the actual experimental-unit baseline variance.

If the required sample cannot be achieved within the four-week pilot, the intervention should be redesigned rather than treated as adequately powered.

### Stopping Rule

The pilot runs for the full **4-week period** unless a pre-defined safety, service, or operational failure requires early termination.

Do not terminate early merely because an interim result becomes statistically significant.

Before launch, pre-specify:

- 4-week pilot duration
- minimum sample size
- primary metric
- MDE
- significance threshold
- guardrail thresholds

Terminate early only for:

- predefined operational/safety failures
- predefined severe guardrail breaches
- a pre-specified overwhelming-effect boundary

### Decision Rule

Scale the intervention only if:

- the treatment improves completed trips per available vehicle-hour
- the effect meets the pre-specified MDE
- the confidence interval supports a practically meaningful improvement
- guardrails remain within their pre-defined limits

If these conditions are not met, retain the existing capacity policy or redesign the intervention.

---

## Important Limitation

MetroPulse historical data does not directly observe randomized capacity assignment, vehicle supply, unmet demand, driver acceptance, or passenger wait time.

Therefore the historical analysis supports where and when to run an experiment, but does not by itself establish that incremental capacity will cause the proposed productivity improvement.

The historical analysis is therefore used to identify and prioritize the operating windows for prospective experimentation rather than to claim causal uplift from additional capacity.
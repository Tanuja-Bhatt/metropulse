# MetroPulse — Executive Decision Memo

## Decision

MetroPulse recommends testing two controlled capacity interventions over four weeks:

1. Airport-Focused Capacity Allocation
2. Citywide Evening Peak Capacity Planning

These are proposed as prospective experiments, not as claims that additional capacity will causally improve productivity.

## What the Data Says

### 1. Demand is strongly concentrated in the evening

Taxi demand reaches its highest average hourly level around **18:00**, at approximately **8,416 trips per hour**.

Historical sensitivity analysis identifies materially higher demand across several afternoon/evening windows:

| Candidate window | Average hourly demand | Demand lift vs. outside window |
|---|---:|---:|
| 14:00–18:00 | 7,370 | 65.7% |
| 15:00–19:00 | 7,717 | 76.2% |
| 16:00–20:00 | 7,748 | 77.2% |

These results consistently identify the afternoon/evening period as the strongest historical demand concentration.

### 2. Airport-focused capacity is worth testing

Airport activity is sufficiently important to justify a dedicated operational experiment rather than treating airport demand as part of the general citywide peak.

The proposed experiment should allocate incremental capacity to eligible airport-focused operating units while maintaining comparable control units under the existing policy.

The primary outcome should be:

**Completed airport trips per available vehicle-hour.**

This controls for the possibility that simply adding more vehicles produces more trips without improving productivity.

### 3. Citywide evening capacity is also worth testing

The citywide evening period represents the strongest sustained demand concentration identified in the historical data.

The proposed experiment should test incremental capacity during the selected evening peak using comparable operating units.

The primary outcome should be:

**Completed trips per available vehicle-hour.**

## Experimental Design

Both interventions should run for **4 weeks**.

Treatment and control should be assigned at the operational-unit level where feasible to reduce contamination.

Before launch, the business should pre-specify:

- experimental unit
- treatment allocation
- control policy
- primary metric
- minimum detectable effect (MDE)
- required sample size
- significance threshold
- guardrail thresholds
- stopping rule

The MDE should represent the smallest productivity improvement that economically justifies the incremental capacity.

Sample size should be calculated from the baseline variance of the primary metric at the actual experimental-unit level using a two-sided a = 0.05 and 80% power, with additional allowance for attrition, non-compliance, and unusable observations.

## Guardrails

The interventions should not be scaled based on the primary metric alone.

Monitor:

- revenue per vehicle-hour
- non-airport trip productivity
- service quality / wait-time proxy where available
- post-peak service performance
- vehicle utilization
- non-peak service coverage

A positive productivity result should not justify scale-up if material service or operational deterioration occurs elsewhere.

## Data Quality Consideration

The assessment contains **10.78 million taxi trips**.

The quality-valid analytical population contains approximately **9.19 million trips**, representing **85.3% of all trips**, and accounts for approximately **88.7% of reported revenue**.

This demonstrates that data-quality rules can materially change the analytical population.

The dashboard therefore reports quality issues explicitly rather than treating overlapping issue counts as unique affected trips.

## Decision Rule

Scale an intervention only when:

1. the treatment improves the pre-specified primary productivity metric;
2. the estimated effect meets or exceeds the pre-specified MDE;
3. the confidence interval supports a practically meaningful improvement; and
4. no material guardrail is breached.

If these conditions are not satisfied, retain the existing capacity policy or redesign the intervention.

## Important Limitation

MetroPulse is an observational mobility analytics system.

The historical data does not directly observe randomized capacity assignment, vehicle supply, unmet demand, driver acceptance/rejection, or passenger wait time.

Therefore the historical analysis identifies **where and when an experiment is worth running**. It does not establish that incremental capacity will cause the observed historical demand patterns or produce a specific productivity uplift.

The recommended next step is therefore a controlled four-week operational experiment with pre-specified success criteria.

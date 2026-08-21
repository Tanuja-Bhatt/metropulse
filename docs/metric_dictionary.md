# MetroPulse Metric Dictionary

## Purpose

This dictionary is the source of truth for metrics displayed in the MetroPulse dashboard and executive outputs.

Core taxi measures represent **NYC market activity**, not the fictional company's own revenue, customers, or market share. Metrics are derived from the reproducible DuckDB warehouse and analytical marts.

## Global conventions

- **Assessment period:** 1 April 2024 through 30 June 2024.
- **Core taxi grain:** one row per taxi trip in `intermediate.trip_metrics`; analytical marts aggregate from this layer.
- **Hourly grain:** one row per canonical hour in `marts.hourly_mobility_summary`.
- **Zone grain:** one row per taxi zone in `marts.geographic_performance`.
- **Market interpretation:** taxi totals are market measures/opportunity estimates, not company financials.
- **Validity flags:** metrics that depend on duration, distance, revenue, passenger, or other fields use the corresponding validity rule instead of silently replacing invalid values.
- **Missing/invalid values:** excluded from metric-specific denominators unless explicitly stated.
- **Causality:** weather, subway, and other observational relationships are associations; they are not causal estimates.

---

## 1. Executive / market metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Total trips** | `COUNT(*)` / reconciled taxi trip count | Market / trip | All source records in assessment period | Represents NYC taxi market activity, not company trips |
| **Total passengers** | `SUM(passenger_count)` where passenger field is usable | Market / trip | Invalid/unknown passenger values excluded where validity is required | Passenger counts contain substantial unknown/zero values; not a unique-customer count |
| **Total fare amount** | `SUM(fare_amount)` | Market / trip | Reported fare field | Raw fare contains invalid/negative records; use validity-controlled measures for clean economics |
| **Total charged amount** | `SUM(total_amount)` | Market / trip | Reported total charge | Invalid/negative total amounts are retained for quality analysis but excluded from valid-revenue metrics |
| **Trip distance** | `SUM(trip_distance)` or average/median valid distance depending on display | Trip / hourly / zone | Valid-distance population for analytical measures | Distance contains invalid/zero/extreme values |
| **Trip duration** | `dropoff_datetime - pickup_datetime` | Trip | Valid positive duration required for duration metrics | Some records have invalid durations |
| **Airport-trip share** | `airport_trips / total_trips * 100` | Market | Airport classification from trip metrics | Measures observed trip classification, not airport service share |
| **Revenue-valid trips** | Count of trips passing the revenue-validity rule | Market / analytical population | Valid revenue required | Excludes negative/otherwise invalid revenue records |
| **Distance-valid trips** | Count of trips passing distance-validity rule | Market / analytical population | Valid distance required | Excludes zero/non-positive/extreme distance cases according to implemented rule |
| **Duration-valid trips** | Count of trips passing duration-validity rule | Market / analytical population | Positive duration required | Does not imply true travel-time accuracy |
| **Passenger-valid trips** | Count of trips with usable passenger count | Market / analytical population | Invalid/unknown/zero passenger records excluded according to rule | Passenger data quality is materially weaker than revenue/duration |

---

## 2. Unit economics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Fare per mile** | `fare_amount / trip_distance` | Valid trip | Valid fare and positive valid distance | Highly skewed; extreme-distance/low-distance trips can distort the mean |
| **Amount per trip** | `total_amount / trip_count` or valid-trip average | Trip / aggregate | Valid revenue where analytical version is used | Aggregate ratio is not identical to mean of raw ratios |
| **Amount per minute** | `total_amount / trip_duration_minutes` | Valid trip | Valid revenue and positive valid duration | Sensitive to very short trips |
| **Average speed (mph)** | `trip_distance / trip_duration_hours` | Valid trip | Positive valid distance and positive valid duration | Indicates recorded trip speed, not road speed; congestion and GPS/measurement errors are not directly observed |
| **Average trip distance** | `AVG(trip_distance)` on valid-distance trips | Analytical population | Valid distance | Mean is skew-sensitive |
| **Median trip distance** | `MEDIAN(trip_distance)` on valid-distance trips | Analytical population | Valid distance | Better represents the central trip than the mean under skew |
| **Average duration** | `AVG(trip_duration_minutes)` on valid-duration trips | Analytical population | Positive valid duration | Mean is sensitive to long-tail trips |
| **Median duration** | `MEDIAN(trip_duration_minutes)` on valid-duration trips | Analytical population | Positive valid duration | More robust to extreme durations |

---

## 3. Distribution metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Percentile (P90/P95/P99)** | `QUANTILE_CONT(metric, percentile)` | Selected metric population | Metric-specific valid population | Percentiles depend on the defined analytical population |
| **Median** | `MEDIAN(metric)` | Selected metric population | Metric-specific valid population | Not directly additive |
| **Standard deviation** | `STDDEV_SAMP(metric)` | Selected metric population | Metric-specific valid population | Sensitive to outliers |
| **Coefficient of variation (CV%)** | `STDDEV_SAMP(metric) / AVG(metric) * 100` | Time/zone population | Mean must be positive | Unstable when mean approaches zero |

---

## 4. Demand and temporal metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Hourly taxi demand** | `SUM(trip_count)` | Canonical hour | All taxi trips represented in hourly summary | Market demand, not fulfilled demand |
| **Average hourly demand by hour-of-day** | `AVG(taxi_trip_count)` grouped by `hour_of_day` | Hour-of-day profile | Complete canonical hours | Does not model supply availability |
| **Peak hour** | Hour with highest average or total demand, depending on analysis | Hour-of-day | Full assessment period | Peak can vary by weekday/weekend |
| **Peak-hour share** | `trips in selected peak hour(s) / relevant total trips * 100` | Market / day-part | Defined peak window | Share depends on peak-window definition |
| **Top-N-hour concentration** | Sum of demand in top N hours divided by total demand | Market / weekday-weekend | Rank based on total trips | Concentration depends on selected N |
| **Demand index (%)** | `hourly_trip_count / overall_avg_hourly_demand * 100` | Hour | Canonical hourly series | Index is relative to this dataset's overall average |
| **Hourly volatility** | `STDDEV_SAMP(taxi_trip_count)` | Hour-of-day / weekday-weekend | Complete observations | Captures observed variation, not supply volatility |
| **Demand CV%** | `hourly_sd / avg_hourly_trips * 100` | Hour | Positive average demand | High CV can occur when mean demand is low |
| **Weekday/weekend demand** | Aggregate / average demand grouped by `is_weekend` | Day type / hour | Canonical hourly observations | Day-type difference is observational |

---

## 5. Geographic metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Pickup trips by zone** | `SUM(pickup_trips)` | Zone | Mapped pickup zones | Measures observed pickup activity |
| **Dropoff trips by zone** | `SUM(dropoff_trips)` | Zone | Mapped dropoff zones | Measures observed dropoff activity |
| **Zone activity** | `pickup_trips + dropoff_trips` | Zone | Mapped zone records | Counts both sides of trips; not unique trips for ranking unless defined that way |
| **Zone activity contribution %** | `zone_activity / total_market_activity * 100` | Zone | Valid zone aggregate | Contribution is based on defined activity metric |
| **Zone revenue contribution %** | `zone_revenue / total_market_revenue * 100` | Zone | Revenue aggregation | Uses market revenue, not company revenue |
| **Revenue per zone activity** | `total_zone_revenue / total_zone_activity` | Zone | Activity > 0 | Blends pickup/dropoff activity; not equivalent to per-trip revenue |
| **Activity percentile** | `PERCENT_RANK()` over zone activity | Zone | All zone rows | A rank, not a probability or service-quality score |
| **Activity rank** | `RANK() OVER (ORDER BY total_zone_activity DESC)` | Zone | All zones | Ties can share rank |
| **Revenue rank** | `RANK() OVER (ORDER BY total_zone_revenue DESC)` | Zone | All zones | Ties can share rank |
| **Below-median activity indicator** | `TRUE` when `total_zone_activity < median_zone_activity` and activity > 0 | Zone | Non-zero zones | **Demand-side screening only; does not prove unmet demand or insufficient supply** |
| **Activity segment** | `Below Median Activity` vs `At/Above Median Activity` | Zone | Based on zone activity vs market median | Descriptive segmentation |
| **Airport pickup/dropoff share** | Airport pickups/dropoffs divided by zone activity | Zone | Airport classification | Measures observed airport-linked activity composition |

### Underserved-zone interpretation

`below_median_activity_indicator` replaced the misleading name `underserved_indicator`.

The dataset does **not** contain direct supply, wait-time, rejection, idle-vehicle, or availability measures. Therefore this field must never be described as observed unmet demand.

---

## 6. Airport metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Airport trips** | Count of trips classified as airport pickup, airport dropoff, or airport-to-airport | Trip / airport type | Airport classification rules | Classification depends on mapped airport zone IDs |
| **Airport-trip share** | `airport_trips / total_trips * 100` | Market | All trips | Not airport market share |
| **Airport revenue** | Sum of valid total amount for airport trips | Airport type | Revenue-valid population | Valid-revenue only where stated |
| **Airport revenue per trip** | Valid airport revenue / airport trips in analysis population | Airport type / hour | Valid revenue | Sensitive to fare-quality exclusions |
| **Airport peak-window stability** | Share of observed days where daily airport peak hour falls inside selected window | Airport type | One peak hour per day | Stability metric depends on selected window |

---

## 7. Fare, payment, and tipping metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Payment-type mix** | Count and percentage of trips by payment type | Payment type | All classified records | Unknown/invalid payment codes require separate labelling |
| **Valid revenue by payment type** | Sum of valid total amount by payment type | Payment type | Valid revenue | Not a causal payment effect |
| **Median valid fare** | Median fare among valid revenue trips | Payment type | Valid revenue | Better than mean under skew |
| **Average valid tip** | Mean tip among valid trips | Payment type | Valid tip population | Cash tips may be unrecorded |
| **Tipped-trip rate** | `trips with tip_amount > 0 / valid trips * 100` | Payment type | Valid tip population | Recorded tipping, not necessarily actual gratuity behaviour |
| **Tip percentage** | `tip_amount / fare or charged amount` per implemented definition | Trip / payment type | Valid fare/tip records | Definition must remain fixed across dashboard |
| **Tip percentiles** | Median/P90/P95/P99 of recorded tip amount | Payment type | Valid tip population | Recorded amount only |

---

## 8. Weather metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Temperature** | Hourly `temperature_2m` | Canonical hour | Time-aligned weather | Weather is city-level context, not zone-specific |
| **Precipitation** | Hourly precipitation value | Canonical hour | Time-aligned weather | Weather API measurement is external to trip records |
| **Rain flag** | `1` when precipitation > 0, else `0` | Canonical hour | Complete weather hours | Threshold is operational, not causal |
| **Precipitation category** | Dry / Light Rain / Moderate Rain / Heavy Rain based on configured thresholds | Canonical hour | Complete precipitation | Heavy-rain category has very few observed hours in this period |
| **Temperature category** | Cold / Mild / Warm / Hot based on configured thresholds | Canonical hour | Complete temperature | Bands are analytical bins, not causal thresholds |
| **Weather-linked demand** | Taxi demand summarized by weather category/intensity | Hour | Aligned hourly taxi/weather data | Observational; confounded by time and season |
| **Weather-linked trip economics** | Revenue, distance, duration and amount per trip by weather category | Hour | Valid analytical populations | Observational and non-causal |

---

## 9. Transit metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Subway ridership** | Hourly MTA ridership aligned to canonical hour | Hour | Time-aligned subway data | Aggregate subway activity, not rider-level movement |
| **Subway transfers** | Hourly MTA transfer count aligned to canonical hour | Hour | Time-aligned subway data | Aggregate transfer activity |
| **Taxi/subway raw correlation** | `CORR(taxi_trip_count, subway_ridership)` | Hour | Complete aligned hours | Shared temporal structure can inflate raw correlation |
| **Temporal-residual subway correlation** | Correlation between subway ridership and taxi-demand residuals after temporal baseline controls | Hour | Complete regression sample | Still observational; not causal |
| **Subway-to-taxi ratio** | `subway_ridership / taxi_trip_count` | Hour | Taxi demand > 0 | Descriptive ratio only |

---

## 10. Statistical metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Test R²** | Out-of-sample coefficient of determination | Regression model | Chronological test set | Not comparable to in-sample R² without context |
| **MAE** | Mean absolute prediction error | Regression test set | Chronological split | Same unit as taxi trips |
| **RMSE** | Square root of mean squared prediction error | Regression test set | Chronological split | Penalizes large errors more heavily |
| **Adjusted R²** | R² adjusted for number of predictors | Training model | OLS | In-sample measure |
| **Coefficient p-value** | OLS significance test for coefficient = 0 | Model coefficient | Model-specific assumptions | Does not establish causality |
| **Confidence interval** | Model-based interval around coefficient estimate | Model coefficient | OLS assumptions | Sensitive to specification and multicollinearity |
| **VIF** | Variance inflation factor | Predictor | Regression design matrix | High VIF indicates collinearity/unstable coefficient interpretation |
| **Residual** | `actual - predicted` | Observation | Test/train as specified | Residual pattern can reveal misspecification |

### Statistical interpretation rule

The regression models are designed primarily to assess predictive usefulness and conditional associations. They must **not** be described as causal estimates.

---

## 11. Data-quality metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Invalid duration trips** | Count failing positive-duration rule | Trip | DQ rule | Quality indicator, not automatically removed from every metric |
| **Invalid distance trips** | Count failing distance-validity rule | Trip | DQ rule | Includes zero/non-positive/extreme cases according to implemented rule |
| **Invalid revenue trips** | Count failing revenue-validity rule | Trip | DQ rule | Negative/invalid charges retained for DQ visibility |
| **Invalid passenger trips** | Count failing passenger-validity rule | Trip | DQ rule | Passenger quality materially weaker |
| **Unknown payment trips** | Count of unknown/unmapped payment types | Trip | Payment classification | Does not mean transaction is economically invalid |
| **Missing zone trips** | Count of missing pickup/dropoff zone mappings | Trip | Zone mapping rule | Current warehouse mapping is complete for analysed records |
| **Temporal gaps** | Count of canonical-hour discontinuities | Hour | Ordered hourly spine | Current spine has zero observed gaps |
| **Weather completeness %** | Covered canonical hours / canonical hours * 100 | Hour | Canonical spine | City-level weather coverage |
| **Subway completeness %** | Covered canonical hours / canonical hours * 100 | Hour | Canonical spine | Aggregate subway source |
| **Warehouse quality status** | PASS when required reconciliation/test conditions pass; otherwise REVIEW | Warehouse | Automated validation suite | Status summarizes implemented rules only |

---

## 12. Anomaly metrics

| Metric | Formula / definition | Grain | Filters / exclusions | Known limitations |
|---|---|---|---|---|
| **Anomalous trips** | Count meeting configured DQ/anomaly rule | Trip | Valid analytical population where applicable | Rule-based, not a fraud determination |
| **Anomalous revenue** | Sum of revenue associated with anomaly population | Trip | Same anomaly rule | Economic effect can be sensitive to threshold choice |
| **Anomaly sensitivity** | Compare KPI values before vs after anomaly exclusion | Analytical population | Same base validity filters | Measures robustness of aggregate KPI, not anomaly prevalence |

---

## 13. Recommendation metrics

### Initiative 1 — Airport-focused capacity allocation

**Primary experimental metric:** completed airport trips per available vehicle-hour.

**Secondary metric:** airport revenue per available vehicle-hour.

**Guardrails:** total revenue per available vehicle-hour, non-airport completed trips, wait/rejection/fulfilment measures.

**Historical evidence:** airport demand is high-value and its daily peaks repeatedly concentrate in the 14:00–18:00 window.

**Important limitation:** the historical dataset does not observe vehicle supply or unmet demand.

### Initiative 2 — Multi-hour citywide peak-capacity planning

**Primary experimental metric:** completed trips per available vehicle-hour in the 16:00–20:00 window.

**Secondary metric:** revenue per available vehicle-hour.

**Guardrails:** wait/rejection, utilization, post-20:00 service, total revenue.

**Historical evidence:** the 16:00–20:00 period represents a large share of observed market demand.

**Important limitation:** historical demand does not itself prove that additional capacity will increase completed trips.

---

## 14. Dashboard implementation rules

The dashboard must query analytical marts rather than recompute core metrics from raw trip data.

Recommended mart ownership:

- **Executive overview:** `marts.executive_mobility`
- **Temporal demand:** `marts.temporal_demand`, `marts.hourly_mobility_summary`
- **Geographic performance:** `marts.geographic_performance`
- **Fares & payments:** `marts.fare_payment_analysis`
- **Weather & transit:** `marts.weather_transit_analysis`
- **Quality / anomaly status:** `intermediate.data_quality_metrics` plus validated anomaly outputs where available
- **Statistical findings:** `marts.statistical_analysis` and reproducible analysis outputs

Important dashboard filters should be applied to the appropriate mart grain and must not cause double counting.

## 15. Required wording for the dashboard

Use:

- “NYC market trips”
- “NYC taxi market revenue”
- “observed market activity”
- “screening indicator”
- “association”
- “experimental target”

Avoid:

- “our revenue”
- “our customers”
- “market share”
- “underserved” without the explicit data limitation
- “weather causes”
- “subway causes”
- “expected uplift” when the range is only an experimental target

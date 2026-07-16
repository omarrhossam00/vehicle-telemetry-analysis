# vehicle-telemetry-analysis

Python data analysis of vehicle OBD-II telemetry using pandas and matplotlib — practice run before applying the same pipeline to real SparkX Racing telemetry.

## Data

(https://www.kaggle.com/datasets/pedro2025/obd2-panel-opel-2012/data) — ~789k rows of logged OBD-II signals (RPM, speed, throttle position, engine load, coolant/intake temp, torque, power, fuel usage) across multiple driving sessions.

This is **not** SparkX data — SparX telemetry wasn't available for this pass, so a public OBD-II dataset was used to build and validate the pipeline first. The goal was to prove the analysis approach (cleaning, plotting, extracting a real insight) on a large, messy real-world dataset before pointing it at SparkX CAN logs.

## Approach

- Dropped columns that were either constant, redundant, or not useful for this pass (`OBD_STATUS`, `ENGINE_STATUS`, `FUEL_LEVEL`, `ELM_VOLTAGE`, `ABSOLUTE_LOAD`).
- `GEAR` is missing in ~11% of rows whenever the car is in neutral or the clutch is in — filled with `0` (neutral) rather than dropped, so coasting time stays visible instead of being discarded.
- For all other columns, missing values come from ECU read latency / dropped OBD polls rather than a real sensor state, so rows are dropped per-plot only for the columns that plot needs, instead of dropping the whole dataset upfront.
- Six plots, each answering a specific question:
  - `speed.png` / `rpm.png` — average speed / RPM per test session, to see session-to-session driving style
  - `speed_vs_rpm.png` — RPM vs. speed scatter, colored by gear, to check gear-shift behavior
  - `throttle_pos.png` / `engine_load.png` — distribution of throttle and load, to see how aggressively the car is driven overall
  - `timeseries.png` — RPM over time for a single session, a closer look at one drive

## Results

- 789,308 RPM samples, 789,326 speed samples logged across all sessions.
- Mean RPM: **1953**, mean speed: **53.7 km/h**, mean engine load: **15.5%**.
- RPM–speed correlation: **0.89** — strong positive relationship, with visible diagonal bands in the scatter plot consistent with discrete gear changes.
- **44.1%** of samples were under 30% throttle — driving in this dataset is dominated by light-to-moderate throttle inputs, not sustained hard acceleration.
- Gear 5 is the most common non-neutral gear observed.
- Known data quirks, not filtered out for this pass:
  - `SPEED` has a max of 255 km/h, which is almost certainly an OBD-II sensor/protocol ceiling rather than a real speed.
  - `TORQUE` and `POWER` are only populated for ~22% of rows (174,528 of 789,308) — any torque/power claim is based on a smaller slice of the data than the rest of the stats.
  - `REAL_FUEL_USAGE_ML_MIN` has a long right tail (75th percentile 76 ml/min, max 1049.7 ml/min), likely short bursts during hard acceleration.


<img width="1000" height="500" alt="speed_vs_rpm" src="https://github.com/user-attachments/assets/a4c41733-9cb6-445e-b104-8a7487767a08" />

## What I'd do differently with real SparkX data

- Use actual CAN frame timestamps instead of session-file grouping, so plots reflect real lap/session boundaries rather than file boundaries.
- Cross-check `SPEED` against wheel-speed sensor data (if logged separately) instead of trusting a single OBD PID, given the 255 km/h ceiling seen here.
- Add a lap-by-lap comparison view once SparX sessions are labeled by track/lap, instead of just per-session averages.
- Investigate the fuel-usage outlier tail against throttle/RPM at the same timestamps, to confirm it's genuine hard-acceleration behavior and not a logging glitch.

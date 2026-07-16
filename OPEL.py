"""
OPEL.py
Analyzes OBD-II telemetry data from a 2012 Opel to understand driving
behavior patterns (RPM, speed, throttle, engine load, gear).

Produces:
  - plots/timeseries.png    (RPM over one session)
  - plots/distribution.png  (throttle position histogram)
  - plots/correlation.png   (RPM vs SPEED scatter, colored by gear)
  - printed basic stats + a written insight
"""

import os
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import dates as mpl_dates

plt.style.use('fivethirtyeight')

os.makedirs('plots', exist_ok=True)

df = pd.read_csv('dataset.csv', index_col='segment_id')
df['timestamp'] = pd.to_datetime(df['timestamp'])

pd.set_option('display.max_columns', 30)
pd.set_option('display.max_rows', 30)

df = df.drop(columns=['OBD_STATUS','ENGINE_STATUS','FUEL_LEVEL','ELM_VOLTAGE','ABSOLUTE_LOAD']
             , errors='ignore')

# GEAR is missing (~11% of rows) whenever the car is in neutral/clutch-in,
# since the ECU has no gear to report in that state. We treat missing GEAR
# as 0 = neutral rather than dropping those rows, so coasting/neutral time
# is still visible in the correlation plot instead of being discarded.
df['GEAR'] = df['GEAR'].fillna(0)
df['GEAR'] = df['GEAR'].astype(int)


# Remaining missing values (RPM, SPEED, THROTTLE_POS, ENGINE_LOAD, etc.)
# come from ECU read latency / dropped OBD polls, not from real sensor
# states, so for the stats and plots below we simply drop rows missing
# the specific column(s) needed for that step, rather than dropping the
# whole dataset upfront (which would waste far more usable data).

cols = [
    'RPM',       
    'SPEED',           
    'ENGINE_LOAD',     
    'MAF',             
    'COOLANT_TEMP',
    'INTAKE_TEMP',     
    'TORQUE',           
    'POWER',            
    'REAL_FUEL_USAGE_ML_MIN'   
]
print("=== Basic stats ===")
print(df[cols].describe())


"""first figure """

session_avg_speed = (
    df.groupby('segment_file')
      .agg(
          avg_speed=('SPEED', 'mean'),
          start_time=('timestamp', 'min')
      )
      .dropna()
      .sort_values('start_time')
)

plt.figure(1, figsize=(10,5))
plt.plot(
    session_avg_speed['start_time'],
    session_avg_speed['avg_speed']
)

plt.xlabel('Date')
plt.ylabel('Average Speed (km/h)')
plt.title('Average Speed Per Test Session')
plt.grid(True)
plt.gcf().autofmt_xdate()
plt.gca().xaxis.set_major_formatter(
    mpl_dates.DateFormatter('%b, %d %Y')
)
plt.tight_layout()
plt.savefig('plots/speed.png')
plt.close()

"""second figure """
session_avg_rpm = (
    df.groupby('segment_file')
      .agg(
          avg_rpm=('RPM', 'mean'),
          start_time=('timestamp', 'min')
      )
      .dropna()
      .sort_values('start_time')
)

plt.figure(2, figsize=(10,5))
plt.plot(
    session_avg_rpm['start_time'],
    session_avg_rpm['avg_rpm']
)

plt.xlabel('Date')
plt.ylabel('Average RPM')
plt.title('Average RPM Per Test Session')

plt.grid(True)
plt.gcf().autofmt_xdate()
plt.gca().xaxis.set_major_formatter(
    mpl_dates.DateFormatter('%b, %d %Y')
)
plt.tight_layout()
plt.savefig('plots/rpm.png')
plt.close()

"""third figure """
plot_df = df[['RPM', 'SPEED', 'GEAR']].dropna(subset=['RPM', 'SPEED'])
plt.figure(3, figsize=(10,5))
plt.scatter(plot_df['SPEED'], plot_df['RPM'],
            c=plot_df['GEAR'],
            cmap='viridis',
            edgecolors='black',
            s=3,
            alpha=0.2
)
cbar=plt.colorbar()
cbar.set_label('Gear (0 = Neutral)')
plt.xlabel('Speed (km/h)')
plt.ylabel('RPM')
plt.title('RPM vs Speed')
plt.tight_layout()
plt.savefig('plots/speed_vs_rpm.png')
plt.close()

"""forth figure """
throttle = df['THROTTLE_POS'].dropna()
plt.figure(4, figsize=(8,6))
plt.hist(throttle,
        bins=30,
        color='steelblue',
        edgecolor='black',
        log=True
)
plt.xlabel('Throttle Position (%)')
plt.ylabel('Number of samples')
plt.title('Distribution of Throttle Position')
plt.tight_layout()
plt.savefig('plots/throttle_pos.png')
plt.close()

"""fifth figure"""
engine_load = df['ENGINE_LOAD'].dropna()
plt.figure(5, figsize=(10,5))
plt.hist(engine_load,
        bins=30,
        color="#30aefc",
        edgecolor='black',
        log=True
)
plt.xlabel('Engine Load (%)')
plt.ylabel('Number of samples')
plt.title('Distribution of Engine Load')
plt.tight_layout()
plt.savefig('plots/engine_load.png')
plt.close()

"""single session"""
session_name = df['segment_file'].iloc[0]
session = (
    df[df['segment_file'] == session_name]
    .sort_values('timestamp')
)

plt.figure(6, figsize=(10,5))
plt.plot(session['timestamp'], session['RPM'])

plt.xlabel('Time')
plt.ylabel('RPM')
plt.title(f'RPM Over Time ({session_name})')
plt.grid(True)
plt.gcf().autofmt_xdate()
plt.gca().xaxis.set_major_formatter(
    mpl_dates.DateFormatter('%H:%M:%S')
)
plt.tight_layout()
plt.savefig('plots/timeseries.png')
plt.close()


# Compute correlation coefficient for the README numbers section
rpm_speed_corr = plot_df['RPM'].corr(plot_df['SPEED'])

"""some insight"""
mean_rpm = df['RPM'].mean()
dominant_gear = plot_df[plot_df['GEAR'] > 0]['GEAR'].mode()[0]
pct_low_throttle = (throttle < 30).mean() * 100

insight = (
    f"RPM vs speed shows distinct diagonal bands consistent with gear "
    f"changes (RPM-SPEED correlation: {rpm_speed_corr:.2f}). Mean RPM "
    f"across all sessions is {mean_rpm:.0f}, and {pct_low_throttle:.1f}% "
    f"of samples were under 30% throttle, suggesting driving is dominated "
    f"by light-to-moderate acceleration rather than sustained high-RPM "
    f"or high-throttle inputs. Gear {dominant_gear} is the most common "
    f"non-neutral gear observed."
)

print("=== Insight ===")
print(insight)


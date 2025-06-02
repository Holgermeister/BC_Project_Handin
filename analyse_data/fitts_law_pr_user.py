import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

# File paths
fitt_data = "fitts_rectangles.csv"
filename = "p1_real2_2025-05-16_09-28-37.csv"
real_data = 'combined_cleaned.csv'

# Load user log data
df = pd.read_csv(real_data)

# Filter out invalid rows
df = df[df['elapsed_task_time'].notna() & df['result'].notna()]

# Create start and target columns
df['start'] = df['result'].shift(1)
df['target'] = df['result']
df = df.dropna(subset=['start'])

# Select relevant columns
movement_df = df[['start', 'target', 'elapsed_task_time', 'method', 'game_mode', 'participant']].copy()

# Adjust hotcorner method to have consistent origin
hotcorner_mask = movement_df['method'] == "hotcorner"
movement_df.loc[hotcorner_mask, 'start'] = movement_df.loc[hotcorner_mask, 'target']
movement_df.loc[hotcorner_mask, 'target'] = str((1, 7))  # Ensure match with fitts_df

# Load Fitts geometry data
fitts_df = pd.read_csv(fitt_data)  # must include: start, target, D, W and ID

# Merge to get D and W for each movement
merged = pd.merge(movement_df, fitts_df, on=['start', 'target'], suffixes=('', '_orig'))
print(merged[['start', 'target', 'D', 'W', 'ID']].drop_duplicates())


# Group by method, game_mode, and participant
grouped = merged.groupby(['method', 'game_mode', 'participant'])

# Prepare to collect results
results = []

for (method, game_mode, participant), group in grouped:

    X = sm.add_constant(group['ID'])
    y = group['elapsed_task_time']
    model = sm.OLS(y, X).fit()

    results.append({
        'method': method,
        'game_mode': game_mode,
        'participant': participant,
        'a': model.params['const'],
        'b': model.params['ID'],
        'R_squared': model.rsquared,
        'n_points': len(group)
    })

# Create a DataFrame with results
results_df = pd.DataFrame(results)

# Save to CSV
results_df.to_csv("fitts_fit_results_by_method_gamemode_participant.csv", index=False)
print("Saved regression fit results to 'fitts_fit_results_by_method_gamemode_participant.csv'")


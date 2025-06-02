import glob
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt

# Get list of CSV files
csv_files = glob.glob('data/*.csv')  # e.g., './data/*.csv'

# Prepare list to hold cleaned DataFrames
cleaned_dfs = []

for file in csv_files:
    df = pd.read_csv(file)
    
    # Keep only rows where 'task_index' <= 215
    df_cleaned = df[df['task_index'] <= 215]
    
    cleaned_dfs.append(df_cleaned)

# Concatenate all cleaned DataFrames
combined_df = pd.concat(cleaned_dfs, ignore_index=True)
# Save the combined DataFrame to a new CSV file
#combined_df.to_csv('combined_cleaned_with_useLess.csv', index=False)

required_columns = [
    'from_highlighted_to_selected',
    'elapsed_task_time',
    'correct_res',
    'gaze_movement_pr_task'
]
df_clean = combined_df.dropna(subset=required_columns)
df_clean.to_csv('combined_cleaned_with_useLess.csv', index=False)
# Count how many useLess are True per method and task_index
useLess_counts = df_clean.groupby(['method', 'game_mode'])['useLess'].sum().reset_index()
useLess_counts = useLess_counts.rename(columns={'useLess': 'useLess_true_count'})


useLess_counts.to_csv('useLess_counts_by_method_and_task.csv', index=False)






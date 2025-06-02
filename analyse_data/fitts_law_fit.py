import pandas as pd
import numpy as np
import statsmodels.api as sm
import sys
import os
import matplotlib.pyplot as plt
import math
import csv
# Setup paths

def calc_fitts():
    # Dimensions of the rectangles (targets)
    w = 255   # width (horizontal)
    h = 288  # height (vertical)

    #  (1,7) er hotcorner select center 
    cells= [(1, 3),(1, 4),(1, 5),(2, 3),(2, 4),(2, 5),(3, 3),(3, 4),(3, 5),(1,7)]
    centers = [(896.0, 432.0),(1152.0, 432.0),(1408.0, 432.0),(896.0, 720.0),(1152.0, 720.0),(1408.0, 720.0),(896.0, 1008.0),(1152.0, 1008.0),(1408.0, 1008.0),(1905,1080)]
    print(len(cells), len(centers))


    results = []

    for start_idx, (start_x, start_y) in enumerate(centers):
        for target_idx, (target_x, target_y) in enumerate(centers):
            if start_idx == target_idx:
                continue  # skip same-cell movements

            dx = target_x - start_x
            dy = target_y - start_y
            distance = math.hypot(dx, dy)

            unit_dx = dx / distance
            unit_dy = dy / distance

            # Effective width for a rectangle based on approach angle
            W = 1 / math.sqrt((unit_dx / w) ** 2 + (unit_dy / h) ** 2)
            
            if target_idx == 9:
                # Hotcorner target (1, 7) is treated as a special case
                W = 200
            
            # Fitts' Law Index of Difficulty
            ID = math.log2(distance / W + 1)

            results.append({
                "start": cells[start_idx],
                "target": cells[target_idx],
                "D": round(distance, 2),
                "W": round(W, 2),
                "ID": round(ID,2)
            })

    # Print results
    for r in results:
        print(f"From {r['start']} to {r['target']}: D = {r['D']}, W = {r['W']}, ID = {r['ID']}")

    # Optional: save to CSV
    with open("fitts_rectangles.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["start", "target", "D", "W", "ID"])
        writer.writeheader()
        writer.writerows(results)
#calc_fitts()
# quit()
def remove_outliers(df, columns, z_thresh=1):
    df_filtered = df.copy()
    for col in columns:
        mean = df_filtered[col].mean()
        std = df_filtered[col].std()
        z = (df_filtered[col] - mean) / std
        df_filtered = df_filtered[abs(z) <= z_thresh]
    return df_filtered

def remove_outliers_iqr(df, col='elapsed_task_time'):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[col] >= lower) & (df[col] <= upper)]


def standard_fit():
    fitt_data = "fitts_rectangles.csv"
    filename = "p1_real2_2025-05-16_09-28-37.csv"
    real_data = 'combined_cleaned.csv'

    # Load user log data
    df = pd.read_csv(real_data)

    # Keep rows with necessary data
    df = df[df['elapsed_task_time'].notna() & df['result'].notna()]

    # Create start/target columns from result sequence
    df['start'] = df['result'].shift(1)
    df['target'] = df['result']
    df = df.dropna(subset=['start'])
    df['start'] = df['start']
    df['target'] = df['target']

    # Keep only relevant columns
    movement_df = df[['start', 'target', 'elapsed_task_time', 'method', 'game_mode']].copy()


    # Fix start/target for hotcorner method: treat movement as from target to (1, 7)
    hotcorner_mask = movement_df['method'] == "hotcorner"

    # Reassign start and target for hotcorner movements
    movement_df.loc[hotcorner_mask, 'start'] = movement_df.loc[hotcorner_mask, 'target']
    movement_df.loc[hotcorner_mask, 'target'] = str((1, 7))  # match format in fitts_df

    # Load Fitts rectangle geometric data
    fitts_df = pd.read_csv(fitt_data)  # must include: start, target, D, W

    # Merge movement data with D and W
    merged = pd.merge(movement_df, fitts_df, on=['start', 'target'], suffixes=('', '_orig'))
    merged.to_csv('merged_movement_fitts.csv', index=False)

    # Group by method and game_mode
    grouped = merged.groupby(['method', 'game_mode'])

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(18, 10))
    axes = axes.flatten()  # Flatten to make indexing easier

    # Loop through groups and plot
    for i, ((method, game_mode), group) in enumerate(grouped):
        
        group = remove_outliers_iqr(group)
        agg = group.groupby('ID', as_index=False)['elapsed_task_time'].median()
        agg['TP'] = agg['ID'] / agg['elapsed_task_time']
        mean_tp = agg['TP'].mean()

        # Write the output to a file instead of printing
        with open("mean_tp_summary.txt", "a") as f:
            f.write(f"Method: {method}, Game Mode: {game_mode}, Number of unique IDs: {len(agg['ID'].unique())}\n")
            f.write(f"Mean TP for Method: {method}, Game Mode: {game_mode} = {mean_tp:.3f} bits/s\n")
        
        X = sm.add_constant(agg['ID'])
        y = agg['elapsed_task_time']
        model = sm.OLS(y, X).fit()
        
        print(model.summary())
        a = model.params['const']
        b = model.params['ID']

        ax = axes[i]
        ax.scatter(agg['ID'], y, alpha=0.4, label='Observed')
        ax.plot(agg['ID'], model.predict(X), color='red', label=f'Fit: MT = {a:.2f} + {b:.2f}·ID')
        ax.set_xlabel("ID (log2(D / W + 1))")
        ax.set_ylabel("Movement Time (s)")
        ax.set_title(f"Method: {method}, Mode: {game_mode}")
        ax.legend()
        ax.grid(True)

    # Remove any unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.show()
standard_fit()

def combined_fitts_plot():
    fitt_data = "fitts_rectangles.csv"
    real_data = 'combined_cleaned.csv'

    # Load and preprocess user log data
    df = pd.read_csv(real_data)
    df = df[df['elapsed_task_time'].notna() & df['result'].notna()]
    df['start'] = df['result'].shift(1)
    df['target'] = df['result']
    df = df.dropna(subset=['start'])
    movement_df = df[['start', 'target', 'elapsed_task_time', 'method', 'game_mode']].copy()

    # Handle hotcorner fix
    hotcorner_mask = movement_df['method'] == "hotcorner"
    movement_df.loc[hotcorner_mask, 'start'] = movement_df.loc[hotcorner_mask, 'target']
    movement_df.loc[hotcorner_mask, 'target'] = str((1, 7))

    # Load Fitts data
    fitts_df = pd.read_csv(fitt_data)
    merged = pd.merge(movement_df, fitts_df, on=['start', 'target'], suffixes=('', '_orig'))

    # Group by method and game_mode
    grouped = merged.groupby(['method', 'game_mode'])

    # Prepare a combined plot
    plt.figure(figsize=(12, 8))
    colors = plt.cm.get_cmap('tab10', len(grouped))

    for idx, ((method, game_mode), group) in enumerate(grouped):

        group = remove_outliers_iqr(group)

        agg = group.groupby('ID', as_index=False)['elapsed_task_time'].median()
        X = sm.add_constant(agg['ID'])
        y = agg['elapsed_task_time']
        model = sm.OLS(y, X).fit()
        a = model.params['const']
        b = model.params['ID']

        label = f'{method}, {game_mode} (R²={model.rsquared:.2f})'
        plt.scatter(agg['ID'], y, alpha=0.5, color=colors(idx), label=f'{label} - data')
        plt.plot(agg['ID'], model.predict(X), color=colors(idx), linestyle='--', label=f'{label} - fit')

    plt.xlabel("ID (log₂(D / W + 1))")
    plt.ylabel("Movement Time (s)")
    plt.title("Fitts' Law Regression Across All Methods and Game Modes")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

combined_fitts_plot()

def combined_fitts_plot_with_points():
    fitt_data = "fitts_rectangles.csv"
    real_data = 'combined_cleaned.csv'

    # Load and preprocess user log data
    df = pd.read_csv(real_data)
    df = df[df['elapsed_task_time'].notna() & df['result'].notna()]
    df['start'] = df['result'].shift(1)
    df['target'] = df['result']
    df = df.dropna(subset=['start'])
    movement_df = df[['start', 'target', 'elapsed_task_time', 'method', 'game_mode']].copy()

    # Handle hotcorner fix
    hotcorner_mask = movement_df['method'] == "hotcorner"
    movement_df.loc[hotcorner_mask, 'start'] = movement_df.loc[hotcorner_mask, 'target']
    movement_df.loc[hotcorner_mask, 'target'] = str((1, 7))

    # Load Fitts data
    fitts_df = pd.read_csv(fitt_data)
    merged = pd.merge(movement_df, fitts_df, on=['start', 'target'], suffixes=('', '_orig'))

    # Group by method and game_mode
    grouped = merged.groupby(['method', 'game_mode'])

    # Prepare the plot
    plt.figure(figsize=(12, 8))
    methods = sorted(merged['method'].unique())
    cmap = plt.cm.get_cmap('tab10', len(methods))
    method_to_color = {method: cmap(i) for i, method in enumerate(methods)}
    used_labels = set()

    for (method, game_mode), group in grouped:
        color = method_to_color[method]

        # Plot all raw data points (light color)
        raw_label = f'{method}, {game_mode} - raw'
        if raw_label not in used_labels:
            plt.scatter(group['ID'], group['elapsed_task_time'], color=color, alpha=0.2, label=raw_label)
            used_labels.add(raw_label)
        else:
            plt.scatter(group['ID'], group['elapsed_task_time'], color=color, alpha=0.2)

        # Median + regression
        stats = group.groupby('ID')['elapsed_task_time'].agg(['median', 'std', 'count']).reset_index()
        stats['stderr'] = stats['std'] / np.sqrt(stats['count'])
        X = sm.add_constant(stats['ID'])
        model = sm.OLS(stats['median'], X).fit()
        y_pred = model.predict(X)

        fit_label = f'{method}, {game_mode} - fit (R²={model.rsquared:.2f})'
        plt.errorbar(stats['ID'], stats['median'], yerr=stats['stderr'], fmt='o',
                     color=color, capsize=3, label=f'{method}, {game_mode} - median')
        plt.plot(stats['ID'], y_pred, color=color, linewidth=2.5, label=fit_label)

    plt.xlabel("ID (log₂(D / W + 1))")
    plt.ylabel("Movement Time (s)")
    plt.title("Fitts' Law Regression with Raw Data, Medians, and Fit Lines")
    plt.legend()
    plt.tight_layout()
    plt.show()
#combined_fitts_plot_with_points()


def styled_combined_fitts_plot():
    fitt_data = "fitts_rectangles.csv"
    real_data = "combined_cleaned.csv"

    # Load and clean data
    df = pd.read_csv(real_data)
    df = df[df['elapsed_task_time'].notna() & df['result'].notna()]
    df['start'] = df['result'].shift(1)
    df['target'] = df['result']
    df = df.dropna(subset=['start'])
    movement_df = df[['start', 'target', 'elapsed_task_time', 'method', 'game_mode']].copy()

    # Fix hotcorner movements
    hotcorner_mask = movement_df['method'] == "hotcorner"
    movement_df.loc[hotcorner_mask, 'start'] = movement_df.loc[hotcorner_mask, 'target']
    movement_df.loc[hotcorner_mask, 'target'] = str((1, 7))

    # Load Fitts geometry data and merge
    fitts_df = pd.read_csv(fitt_data)
    merged = pd.merge(movement_df, fitts_df, on=['start', 'target'])

    grouped = merged.groupby(['method', 'game_mode'])

    plt.figure(figsize=(6, 5))
    method_labels = {}  # To avoid duplicate labels in legend
    methods = sorted(merged['method'].unique())
    cmap = plt.cm.get_cmap('tab10', len(methods))
    method_to_color = {method: cmap(i) for i, method in enumerate(methods)}

    for (method, game_mode), group in grouped:
        stats = group.groupby('ID')['elapsed_task_time'].agg(['median', 'std', 'count']).reset_index()
        stats['stderr'] = stats['std'] / np.sqrt(stats['count'])

        X = sm.add_constant(stats['ID'])
        y = stats['median']
        model = sm.OLS(y, X).fit()
        y_pred = model.predict(X)

        color = method_to_color[method]
        label = method.capitalize()

        # Avoid repeating legend labels
        show_label = label not in method_labels
        method_labels[label] = True

        plt.errorbar(
            stats['ID'], stats['median'],
            yerr=stats['stderr'],
            fmt='o', capsize=3,
            color=color, ecolor=color,
            label=label if show_label else None
        )

        plt.plot(stats['ID'], y_pred, color=color, linewidth=3)

    plt.xlabel("ID")
    plt.ylabel("MT")

    plt.legend()
    plt.tight_layout()
    plt.show()

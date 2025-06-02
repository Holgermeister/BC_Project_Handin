
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

    df_cleaned = df_cleaned[df_cleaned['useLess'] == False]
    
    cleaned_dfs.append(df_cleaned)

# Concatenate all cleaned DataFrames
combined_df = pd.concat(cleaned_dfs, ignore_index=True)
# Save the combined DataFrame to a new CSV file
combined_df.to_csv('combined_cleaned.csv', index=False)



def remove_outliers(df, columns, z_thresh=2):
    df_filtered = df.copy()
    for col in columns:
        mean = df_filtered[col].mean()
        std = df_filtered[col].std()
        z = (df_filtered[col] - mean) / std
        df_filtered = df_filtered[abs(z) <= z_thresh]
    return df_filtered

def remove_outliers_iqr(df, columns):
    df_filtered = df.copy()
    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df_filtered = df[(df[col] >= lower) & (df[col] <= upper)]
    return df_filtered

def genereat_stats(file):

    # Load combined CSV
    df = pd.read_csv(file)
    required_columns = [
        'from_highlighted_to_selected',
        'elapsed_task_time',
        'correct_res',
        'gaze_movement_pr_task'
    ]
    df_clean = df.dropna(subset=required_columns)

    # Convert correct_res to boolean
    df_clean['correct_res'] = df_clean['correct_res'].astype(bool)

    # Add error rate
    df_clean['error_rate'] = 1 - df_clean['correct_res']

    outlier_columns = [
        'from_highlighted_to_selected',
        'elapsed_task_time'
    ]
    
    df_clean = remove_outliers_iqr(df_clean, outlier_columns)
    
    
    # --- Overall Summary ---
    main_summary = df_clean.groupby(['method', 'game_mode']).agg(
        avg_from_highlighted_to_selected=('from_highlighted_to_selected', 'mean'),
        std_from_highlighted_to_selected=('from_highlighted_to_selected', 'std'),
        error_rate=('correct_res', lambda x: 1 - x.mean()),
        avg_elapsed_task_time=('elapsed_task_time', 'mean'),
        std_elapsed_task_time=('elapsed_task_time', 'std')
    ).reset_index()

    # Find the last task_index for each participant and method
    last_gaze = (
        df_clean.sort_values('task_index')
        .groupby(['participant', 'method', 'game_mode'])
        .tail(1)
    )
    #last_gaze.to_csv("last_gaze.csv", index=False)

    gaze_summary = last_gaze.groupby('method').agg(
        avg_gaze_movement=('gaze_movement_pr_task', 'mean'),
        std_gaze_movement=('gaze_movement_pr_task', 'std')
    ).reset_index()

    
    main_summary.to_csv("main_summary.csv", index=False)

    # --- Participant Summary Separated by Game Mode ---
    participant_summary = df_clean.groupby(['participant', 'method', 'game_mode']).agg(
        avg_from_highlighted_to_selected=('from_highlighted_to_selected', 'mean'),
        error_rate=('correct_res', lambda x: 1 - x.mean()),
        avg_elapsed_task_time=('elapsed_task_time', 'mean')
    ).reset_index()
    #print(participant_summary)
    participant_summary.to_csv("participant_summary_by_game_mode.csv", index=False)

    return main_summary, df_clean, last_gaze

def plot_stats(main_summary, df_clean, last_gaze):
    # Set seaborn style
    sns.set(style="whitegrid")

    # --- Plots for Overall Data ---
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_clean, x="method", y="from_highlighted_to_selected", hue="game_mode", errorbar="sd")
    plt.title("Avg Time from Highlighted to Selected by Method and Game Mode")
    plt.ylabel("Time (seconds)")
    plt.xlabel("Method")
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10, 6))
    sns.barplot(data=main_summary, x="method", y="error_rate", hue="game_mode", errorbar="sd")
    plt.title("Error Rate by Method and Game Mode")
    plt.ylabel("Error Rate")
    plt.xlabel("Method")
    plt.tight_layout()
    plt.show()
    

    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_clean, x="method", y="elapsed_task_time", hue="game_mode", errorbar="sd")
    plt.title("Avg Elapsed Task Time by Method and Game Mode")
    plt.ylabel("Time (seconds)")
    plt.xlabel("Method")
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(8, 6))
    sns.barplot(data=last_gaze, x="method", y="gaze_movement_pr_task",hue="game_mode", palette="Set2", errorbar="sd")
    plt.title("Avg Gaze Movement per Task by Method")
    plt.ylabel("Gaze Movement")
    plt.xlabel("Method")
    plt.tight_layout()
    plt.show()

    
    plt.figure(figsize=(10, 6))

    # First draw the boxplot
    sns.boxplot(
        data=df_clean,
        x="method",
        y="elapsed_task_time",
        hue="game_mode",
        showfliers=False,  # Optional: hide boxplot outliers so swarmplot points are more visible
        palette="pastel"
    )

    # Then overlay the swarmplot
    sns.swarmplot(
        data=df_clean,
        x="method",
        y="elapsed_task_time",
        hue="game_mode",
        dodge=True,        # Makes sure swarm points don't overlap between hue categories
        color=".25",       # Slightly transparent black/dark dots
        alpha=0.7
    )

    # Avoid double legends
    handles, labels = plt.gca().get_legend_handles_labels()
    n_hue = df_clean['game_mode'].nunique()
    plt.legend(handles[:n_hue], labels[:n_hue], title="Game Mode")

    plt.title("Elapsed Task Time by Method and Game Mode")
    plt.ylabel("Elapsed Task Time (s)")
    plt.xlabel("Method")
    plt.tight_layout()
    plt.show()


    # --- Participant Comparison Separated by Game Mode ---
    # for metric, ylabel in [
    #     ('from_highlighted_to_selected', 'Time from Highlighted to Selected (s)'),
    #     ('error_rate', 'Error Rate'),
    #     ('gaze_movement_pr_task', 'Gaze Movement per Task')
    # ]:
    #     g = sns.catplot(
    #         data=df_clean,
    #         kind="bar",
    #         x="participant",
    #         y=metric,
    #         hue="method",
    #         col="game_mode",
    #         errorbar="sd",
    #         height=6,
    #         aspect=1.5
    #     )
    #     g.set_titles("{col_name}")
    #     g.set_axis_labels("Participant", ylabel)
    #     g.set_xticklabels(rotation=45)
    #     g.fig.suptitle(f"{ylabel} by Participant, Method, and Game Mode", y=1.03)
    #     plt.tight_layout()
    #     plt.show()

    os.makedirs("learning_curves", exist_ok=True)

    # Group data for plotting (per participant, method, game_mode, and task index)
    learning_curve = df_clean.groupby(['participant', 'method', 'game_mode', 'task_index'])['elapsed_task_time'].mean().reset_index()

    # Get list of unique participants
    participants = learning_curve['participant'].unique()

    # Plot for each participant
    for participant_id in participants:
        participant_data = learning_curve[learning_curve['participant'] == participant_id]

        plt.figure(figsize=(10, 6))
        sns.lineplot(
            data=participant_data,
            x="task_index",
            y="elapsed_task_time",
            hue="method",  # different line per method
            style="game_mode",  # optional: different line style for game modes
            marker="o"
        )

        plt.title(f"Learning Curve for Participant {participant_id}")
        plt.xlabel("Task Index")
        plt.ylabel("Avg Elapsed Task Time (s)")
        plt.legend(title="Method / Game Mode", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        filename = f"learning_curves/participant_{participant_id}.png"
        plt.savefig(filename)
        plt.close()

genereat_stats('combined_cleaned.csv')
main_summary, df_clean, last_gaze = genereat_stats('combined_cleaned.csv')
plot_stats(main_summary, df_clean, last_gaze)
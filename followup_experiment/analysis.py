# analysis.py  (lives in followup_experiment/)
#
# Analyses the follow-up experiment results (L-shape + C-shape sweep).
# Saves all figures as PDFs into the same run folder as the CSVs.
#
# Usage:
#   python followup_experiment/analysis.py
#   python followup_experiment/analysis.py followup_run_20260622_105804
#
# If no run folder is specified the most recent run is used automatically.

import sys
import os
import glob

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

# ---------------------------------------------------------------------------
# Locate the run folder
# ---------------------------------------------------------------------------

_here = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(_here, "results")

if len(sys.argv) > 1:
    run_folder = os.path.join(RESULTS_ROOT, sys.argv[1])
else:
    runs = sorted(glob.glob(os.path.join(RESULTS_ROOT, "followup_run_*")))
    if not runs:
        print("No result folders found in followup_experiment/results/")
        sys.exit(1)
    run_folder = runs[-1]

print(f"Analysing: {run_folder}")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

dfs = []
for shape in ["L-shape", "C-shape"]:
    path = os.path.join(run_folder, f"{shape}.csv")
    if os.path.exists(path):
        dfs.append(pd.read_csv(path))

if not dfs:
    print("No CSV files found in run folder.")
    sys.exit(1)

df = pd.concat(dfs, ignore_index=True)
df["Success"] = df["Success"].astype(bool)

shapes   = df["Shape_Type"].unique()
sizes    = sorted(df["Swarm_Size"].unique())
sr_levels = sorted(df["Shuffle_Randomness"].unique())
dur_levels = sorted(df["Shuffle_Duration"].unique())

# Output folder = same as run folder
out = run_folder
print(f"Saving PDFs to: {out}\n")

SHAPE_COLORS = {"L-shape": "#2196F3", "C-shape": "#E91E63"}


def save(fig, name):
    path = os.path.join(out, name + ".pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {name}.pdf")


# ---------------------------------------------------------------------------
# 01 — Overall success rate by shape
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5, 4))
overall = df.groupby("Shape_Type")["Success"].mean() * 100
bars = ax.bar(overall.index, overall.values,
              color=[SHAPE_COLORS.get(s, "#888") for s in overall.index])
ax.set_ylabel("Success Rate (%)")
ax.set_title("Overall Success Rate by Shape (Pilot)")
ax.set_ylim(0, 100)
for bar, val in zip(bars, overall.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=10)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
fig.tight_layout()
save(fig, "01_overall_success_by_shape")

# ---------------------------------------------------------------------------
# 02 — Success rate vs swarm size, per shape
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(5 * len(shapes), 4), sharey=True)
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape]
    sr_by_size = sub.groupby("Swarm_Size")["Success"].mean() * 100
    ax.plot(sr_by_size.index, sr_by_size.values, "o-",
            color=SHAPE_COLORS.get(shape, "#888"), linewidth=2)
    ax.set_title(shape)
    ax.set_xlabel("Swarm Size")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
axes[0].set_ylabel("Success Rate (%)")
fig.suptitle("Success Rate vs Swarm Size", y=1.02)
fig.tight_layout()
save(fig, "02_success_by_swarm_size")

# ---------------------------------------------------------------------------
# 03 — Success rate vs Shuffle Randomness, per shape
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(5 * len(shapes), 4), sharey=True)
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape]
    sr_by_sr = sub.groupby("Shuffle_Randomness")["Success"].mean() * 100
    ax.plot(sr_by_sr.index, sr_by_sr.values, "o-",
            color=SHAPE_COLORS.get(shape, "#888"), linewidth=2)
    ax.set_title(shape)
    ax.set_xlabel("Shuffle Randomness")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
axes[0].set_ylabel("Success Rate (%)")
fig.suptitle("Success Rate vs Shuffle Randomness", y=1.02)
fig.tight_layout()
save(fig, "03_success_by_shuffle_randomness")

# ---------------------------------------------------------------------------
# 04 — Success rate vs Shuffle Duration, per shape
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(5 * len(shapes), 4), sharey=True)
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape]
    sr_by_dur = sub.groupby("Shuffle_Duration")["Success"].mean() * 100
    ax.plot(sr_by_dur.index, sr_by_dur.values, "s-",
            color=SHAPE_COLORS.get(shape, "#888"), linewidth=2)
    ax.set_title(shape)
    ax.set_xlabel("Shuffle Duration (s)")
    ax.set_xticks(dur_levels)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
axes[0].set_ylabel("Success Rate (%)")
fig.suptitle("Success Rate vs Shuffle Duration", y=1.02)
fig.tight_layout()
save(fig, "04_success_by_shuffle_duration")

# ---------------------------------------------------------------------------
# 05 — Heatmap: SR × Swarm Size (success rate), one per shape
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(6 * len(shapes), 5))
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape]
    pivot = sub.groupby(["Swarm_Size", "Shuffle_Randomness"])["Success"].mean().unstack() * 100
    im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=100,
                   cmap="RdYlGn", origin="lower")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{v:.1f}" for v in pivot.columns], fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Shuffle Randomness")
    ax.set_ylabel("Swarm Size")
    ax.set_title(f"{shape} — Success Rate (%)")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=7, color="black")
plt.colorbar(im, ax=axes[-1], label="Success Rate (%)")
fig.suptitle("Success Rate: Swarm Size × Shuffle Randomness", y=1.02)
fig.tight_layout()
save(fig, "05_heatmap_SR_vs_size")

# ---------------------------------------------------------------------------
# 06 — Heatmap: Shuffle Duration × Shuffle Randomness (success rate)
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(7 * len(shapes), 4))
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape]
    pivot = sub.groupby(["Shuffle_Duration", "Shuffle_Randomness"])["Success"].mean().unstack() * 100
    im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=100,
                   cmap="RdYlGn", origin="lower")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{v:.1f}" for v in pivot.columns], fontsize=7)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{v}s" for v in pivot.index])
    ax.set_xlabel("Shuffle Randomness")
    ax.set_ylabel("Shuffle Duration")
    ax.set_title(f"{shape} — Success Rate (%)")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=7, color="black")
plt.colorbar(im, ax=axes[-1], label="Success Rate (%)")
fig.suptitle("Success Rate: Shuffle Duration × Shuffle Randomness", y=1.02)
fig.tight_layout()
save(fig, "06_heatmap_duration_vs_SR")

# ---------------------------------------------------------------------------
# 07 — Num Jams vs Success Rate scatter
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(5 * len(shapes), 4), sharey=False)
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape]
    colors = sub["Success"].map({True: "#4CAF50", False: "#F44336"})
    ax.scatter(sub["Num_Jams"], sub["Completion_Time"], c=colors, alpha=0.4, s=15)
    ax.set_xlabel("Num Jams Triggered")
    ax.set_ylabel("Completion Time (s)")
    ax.set_title(shape)
    from matplotlib.lines import Line2D
    legend = [Line2D([0], [0], marker='o', color='w', markerfacecolor='#4CAF50', label='Success'),
              Line2D([0], [0], marker='o', color='w', markerfacecolor='#F44336', label='Failure')]
    ax.legend(handles=legend)
fig.suptitle("Jams Triggered vs Completion Time", y=1.02)
fig.tight_layout()
save(fig, "07_jams_vs_completion_time")

# ---------------------------------------------------------------------------
# 08 — Final Payload Distance distribution (failed trials only)
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(5 * len(shapes), 4), sharey=True)
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[(df["Shape_Type"] == shape) & (~df["Success"])]
    if sub.empty:
        ax.set_title(f"{shape} (no failures)")
        continue
    ax.hist(sub["Final_Payload_Distance"], bins=20, range=(0, 1),
            color=SHAPE_COLORS.get(shape, "#888"), edgecolor="white", alpha=0.85)
    ax.set_xlabel("Payload Distance (0=no movement, 1=reached goal)")
    ax.set_title(shape)
axes[0].set_ylabel("Count")
fig.suptitle("Failed Trials — How Far Did the Payload Get?", y=1.02)
fig.tight_layout()
save(fig, "08_failed_payload_distance")

# ---------------------------------------------------------------------------
# 09 — Time to first attachment distribution
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(shapes), figsize=(5 * len(shapes), 4), sharey=True)
if len(shapes) == 1:
    axes = [axes]
for ax, shape in zip(axes, shapes):
    sub = df[df["Shape_Type"] == shape].dropna(subset=["Time_To_First_Attachment"])
    colors = sub["Success"].map({True: "#4CAF50", False: "#F44336"})
    ax.hist([sub[sub["Success"]]["Time_To_First_Attachment"],
             sub[~sub["Success"]]["Time_To_First_Attachment"]],
            bins=20, label=["Success", "Failure"],
            color=["#4CAF50", "#F44336"], alpha=0.7, stacked=False)
    ax.set_xlabel("Time to First Attachment (s)")
    ax.set_title(shape)
    ax.legend()
axes[0].set_ylabel("Count")
fig.suptitle("Time to First Attachment: Success vs Failure", y=1.02)
fig.tight_layout()
save(fig, "09_time_to_first_attachment")

# ---------------------------------------------------------------------------
# Summary CSV
# ---------------------------------------------------------------------------

summary = (df.groupby(["Shape_Type", "Swarm_Size", "Shuffle_Randomness", "Shuffle_Duration"])
             .agg(
                 Trials=("Success", "count"),
                 Success_Rate=("Success", "mean"),
                 Mean_Completion_Time=("Completion_Time", "mean"),
                 Mean_Peak_Attached=("Peak_Attached", "mean"),
                 Mean_Num_Jams=("Num_Jams", "mean"),
                 Mean_Total_Shuffles=("Total_Shuffles", "mean"),
                 Mean_Final_Payload_Distance=("Final_Payload_Distance", "mean"),
             )
             .reset_index())
summary["Success_Rate"] = (summary["Success_Rate"] * 100).round(1)
summary_path = os.path.join(out, "summary.csv")
summary.to_csv(summary_path, index=False)
print(f"  saved summary.csv")

print(f"\nDone. {len(df)} trials analysed, {int(df['Success'].sum())} successes ({df['Success'].mean()*100:.1f}%).")

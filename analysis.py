"""
analysis.py
Full analysis of swarm robotics collective transport experiment.
Reads all 4 shape CSVs, computes statistics, saves all plots.

Output: results/analysis/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import os

# ── Config ────────────────────────────────────────────────────────────────────
RESULTS_FOLDER = "results/run_20260608_140959"
OUTPUT_FOLDER  = "results/analysis"
SHAPES         = ["Circle", "Square", "L-shape", "C-shape"]
SHAPE_COLORS   = {
    "Circle":  "#2196F3",
    "Square":  "#4CAF50",
    "L-shape": "#FF9800",
    "C-shape": "#F44336",
}
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
dfs = {}
for s in SHAPES:
    df = pd.read_csv(f"{RESULTS_FOLDER}/{s}.csv")
    df["Success"] = df["Success"].astype(str).str.strip().str.lower() == "true"
    df["Shape"] = s
    dfs[s] = df

all_df = pd.concat(dfs.values(), ignore_index=True)
success_df = all_df[all_df["Success"]]

print(f"Loaded {len(all_df)} trials across {len(SHAPES)} shapes.")
print(f"Saving plots to: {OUTPUT_FOLDER}/\n")

# ── Helper ────────────────────────────────────────────────────────────────────
def save(name):
    path = f"{OUTPUT_FOLDER}/{name}.pdf"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {name}.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 1 — Overall success rate by shape (bar chart)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
by_shape = all_df.groupby("Shape")["Success"].mean() * 100
by_shape = by_shape.reindex(SHAPES)
bars = ax.bar(SHAPES, by_shape.values,
              color=[SHAPE_COLORS[s] for s in SHAPES],
              edgecolor="white", linewidth=1.2, width=0.55)
for bar, val in zip(bars, by_shape.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylim(0, 110)
ax.set_ylabel("Success Rate (%)", fontsize=12)
ax.set_title("Overall Success Rate by Payload Shape", fontsize=13, fontweight="bold")
ax.axhline(50, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("01_overall_success_by_shape")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 2 — Success rate by shape × swarm size (line plot)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for shape in SHAPES:
    df = dfs[shape]
    sr = df.groupby("Swarm_Size")["Success"].mean() * 100
    ax.plot(sr.index, sr.values, marker="o", label=shape,
            color=SHAPE_COLORS[shape], linewidth=2.2, markersize=7)
ax.set_xlabel("Swarm Size", fontsize=12)
ax.set_ylabel("Success Rate (%)", fontsize=12)
ax.set_title("Success Rate vs Swarm Size by Shape", fontsize=13, fontweight="bold")
ax.set_xticks([15, 20, 25, 30, 35])
ax.set_ylim(0, 105)
ax.axhline(50, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
ax.legend(fontsize=11)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("02_success_by_swarm_size")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 3 — Success rate by shape × shuffle randomness (line plot)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for shape in SHAPES:
    df = dfs[shape]
    sr = df.groupby("Shuffle_Randomness")["Success"].mean() * 100
    ax.plot(sr.index, sr.values, marker="o", label=shape,
            color=SHAPE_COLORS[shape], linewidth=2.2, markersize=7)
ax.set_xlabel("Shuffle Randomness", fontsize=12)
ax.set_ylabel("Success Rate (%)", fontsize=12)
ax.set_title("Success Rate vs Shuffle Randomness by Shape", fontsize=13, fontweight="bold")
ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
ax.set_ylim(0, 105)
ax.axhline(50, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
ax.legend(fontsize=11)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("03_success_by_shuffle_randomness")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 4 — Heatmaps: success rate (swarm size × shuffle) for each shape
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
axes = axes.flatten()
for i, shape in enumerate(SHAPES):
    df = dfs[shape]
    pivot = df.groupby(["Swarm_Size","Shuffle_Randomness"])["Success"].mean().unstack() * 100
    sns.heatmap(pivot, ax=axes[i], annot=True, fmt=".0f", cmap="RdYlGn",
                vmin=0, vmax=100, linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Success Rate (%)"})
    axes[i].set_title(f"{shape}", fontsize=13, fontweight="bold",
                      color=SHAPE_COLORS[shape])
    axes[i].set_xlabel("Shuffle Randomness", fontsize=10)
    axes[i].set_ylabel("Swarm Size", fontsize=10)
fig.suptitle("Success Rate (%) — Swarm Size × Shuffle Randomness per Shape",
             fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
save("04_heatmaps_success_rate")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 5 — Mean completion time by shape × swarm size
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for shape in SHAPES:
    df = dfs[shape][dfs[shape]["Success"]]
    ct = df.groupby("Swarm_Size")["Completion_Time"].mean()
    ax.plot(ct.index, ct.values, marker="s", label=shape,
            color=SHAPE_COLORS[shape], linewidth=2.2, markersize=7)
ax.set_xlabel("Swarm Size", fontsize=12)
ax.set_ylabel("Mean Completion Time (s)", fontsize=12)
ax.set_title("Mean Completion Time vs Swarm Size\n(successful trials only)", fontsize=13, fontweight="bold")
ax.set_xticks([15, 20, 25, 30, 35])
ax.legend(fontsize=11)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("05_completion_time_by_swarm_size")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 6 — Mean peak attached by shape × swarm size
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for shape in SHAPES:
    df = dfs[shape]
    pa = df.groupby("Swarm_Size")["Peak_Attached"].mean()
    ax.plot(pa.index, pa.values, marker="^", label=shape,
            color=SHAPE_COLORS[shape], linewidth=2.2, markersize=8)
# Add diagonal reference line (if all ants attached)
ax.plot([15,20,25,30,35],[15,20,25,30,35], linestyle=":", color="grey",
        linewidth=1.2, label="All ants attached")
ax.set_xlabel("Swarm Size", fontsize=12)
ax.set_ylabel("Mean Peak Attached", fontsize=12)
ax.set_title("Mean Peak Attached vs Swarm Size by Shape", fontsize=13, fontweight="bold")
ax.set_xticks([15, 20, 25, 30, 35])
ax.legend(fontsize=11)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("06_peak_attached_by_swarm_size")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 7 — Peak attached vs success rate scatter (all conditions)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for shape in SHAPES:
    df = dfs[shape]
    grouped = df.groupby(["Swarm_Size","Shuffle_Randomness"]).agg(
        success_rate=("Success","mean"),
        peak_attached=("Peak_Attached","mean")
    ).reset_index()
    ax.scatter(grouped["peak_attached"], grouped["success_rate"]*100,
               color=SHAPE_COLORS[shape], label=shape, s=60, alpha=0.8)
ax.set_xlabel("Mean Peak Attached", fontsize=12)
ax.set_ylabel("Success Rate (%)", fontsize=12)
ax.set_title("Peak Attached vs Success Rate\n(each point = one condition)", fontsize=13, fontweight="bold")
ax.legend(fontsize=11)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("07_peak_attached_vs_success_rate")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 8 — L-shape and C-shape: success rate heatmap with shuffle randomness effect
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for i, shape in enumerate(["L-shape", "C-shape"]):
    df = dfs[shape]
    pivot = df.groupby(["Swarm_Size","Shuffle_Randomness"])["Success"].mean().unstack() * 100
    sns.heatmap(pivot, ax=axes[i], annot=True, fmt=".0f", cmap="RdYlGn",
                vmin=0, vmax=100, linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Success Rate (%)"})
    axes[i].set_title(f"{shape} — Non-Convex Shape", fontsize=12, fontweight="bold",
                      color=SHAPE_COLORS[shape])
    axes[i].set_xlabel("Shuffle Randomness", fontsize=10)
    axes[i].set_ylabel("Swarm Size", fontsize=10)
fig.suptitle("Non-Convex Shapes: How Shuffle Randomness Interacts with Swarm Size",
             fontsize=13, fontweight="bold")
plt.tight_layout()
save("08_nonconvex_heatmaps")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 9 — Summary dashboard (all key metrics in one figure)
# ═══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 10))
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

# Top-left: overall success by shape
ax1 = fig.add_subplot(gs[0, 0])
by_shape = all_df.groupby("Shape")["Success"].mean().reindex(SHAPES) * 100
bars = ax1.bar(SHAPES, by_shape.values,
               color=[SHAPE_COLORS[s] for s in SHAPES], edgecolor="white")
for bar, val in zip(bars, by_shape.values):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5,
             f"{val:.0f}%", ha="center", fontsize=9, fontweight="bold")
ax1.set_ylim(0, 115)
ax1.set_title("Overall Success Rate", fontsize=11, fontweight="bold")
ax1.set_ylabel("Success Rate (%)")
ax1.spines[["top","right"]].set_visible(False)
ax1.tick_params(axis="x", labelsize=8)

# Top-middle: success by swarm size
ax2 = fig.add_subplot(gs[0, 1])
for shape in SHAPES:
    sr = dfs[shape].groupby("Swarm_Size")["Success"].mean() * 100
    ax2.plot(sr.index, sr.values, marker="o", label=shape,
             color=SHAPE_COLORS[shape], linewidth=2)
ax2.set_title("Success vs Swarm Size", fontsize=11, fontweight="bold")
ax2.set_xlabel("Swarm Size"); ax2.set_ylabel("Success Rate (%)")
ax2.set_xticks([15,20,25,30,35]); ax2.set_ylim(0,105)
ax2.legend(fontsize=8); ax2.spines[["top","right"]].set_visible(False)

# Top-right: success by shuffle randomness
ax3 = fig.add_subplot(gs[0, 2])
for shape in SHAPES:
    sr = dfs[shape].groupby("Shuffle_Randomness")["Success"].mean() * 100
    ax3.plot(sr.index, sr.values, marker="o", label=shape,
             color=SHAPE_COLORS[shape], linewidth=2)
ax3.set_title("Success vs Shuffle Randomness", fontsize=11, fontweight="bold")
ax3.set_xlabel("Shuffle Randomness"); ax3.set_ylabel("Success Rate (%)")
ax3.set_xticks([0.0,0.25,0.5,0.75,1.0]); ax3.set_ylim(0,105)
ax3.legend(fontsize=8); ax3.spines[["top","right"]].set_visible(False)

# Bottom-left: completion time
ax4 = fig.add_subplot(gs[1, 0])
for shape in SHAPES:
    ct = dfs[shape][dfs[shape]["Success"]].groupby("Swarm_Size")["Completion_Time"].mean()
    ax4.plot(ct.index, ct.values, marker="s", label=shape,
             color=SHAPE_COLORS[shape], linewidth=2)
ax4.set_title("Completion Time (successes)", fontsize=11, fontweight="bold")
ax4.set_xlabel("Swarm Size"); ax4.set_ylabel("Mean Time (s)")
ax4.set_xticks([15,20,25,30,35])
ax4.legend(fontsize=8); ax4.spines[["top","right"]].set_visible(False)

# Bottom-middle: peak attached
ax5 = fig.add_subplot(gs[1, 1])
for shape in SHAPES:
    pa = dfs[shape].groupby("Swarm_Size")["Peak_Attached"].mean()
    ax5.plot(pa.index, pa.values, marker="^", label=shape,
             color=SHAPE_COLORS[shape], linewidth=2)
ax5.plot([15,20,25,30,35],[15,20,25,30,35], ":", color="grey", linewidth=1)
ax5.set_title("Mean Peak Attached", fontsize=11, fontweight="bold")
ax5.set_xlabel("Swarm Size"); ax5.set_ylabel("Peak Attached")
ax5.set_xticks([15,20,25,30,35])
ax5.legend(fontsize=8); ax5.spines[["top","right"]].set_visible(False)

# Bottom-right: peak attached vs success scatter
ax6 = fig.add_subplot(gs[1, 2])
for shape in SHAPES:
    df = dfs[shape]
    g = df.groupby(["Swarm_Size","Shuffle_Randomness"]).agg(
        sr=("Success","mean"), pa=("Peak_Attached","mean")).reset_index()
    ax6.scatter(g["pa"], g["sr"]*100, color=SHAPE_COLORS[shape], label=shape, s=40, alpha=0.8)
ax6.set_title("Peak Attached vs Success Rate", fontsize=11, fontweight="bold")
ax6.set_xlabel("Mean Peak Attached"); ax6.set_ylabel("Success Rate (%)")
ax6.legend(fontsize=8); ax6.spines[["top","right"]].set_visible(False)

fig.suptitle("Swarm Robotics Collective Transport — Full Results Dashboard",
             fontsize=14, fontweight="bold", y=1.01)
save("09_dashboard")


# ═══════════════════════════════════════════════════════════════════════════════
# SAVE SUMMARY CSV
# ═══════════════════════════════════════════════════════════════════════════════
summary = all_df.groupby(["Shape","Swarm_Size","Shuffle_Randomness"]).agg(
    Success_Rate=("Success","mean"),
    N_Successes=("Success","sum"),
    N_Trials=("Success","count"),
    Mean_Completion_Time=("Completion_Time", lambda x: x[all_df.loc[x.index,"Success"]].mean()),
    Mean_Peak_Attached=("Peak_Attached","mean"),
).reset_index()
summary["Success_Rate"] = (summary["Success_Rate"]*100).round(1)
summary["Mean_Completion_Time"] = summary["Mean_Completion_Time"].round(2)
summary["Mean_Peak_Attached"] = summary["Mean_Peak_Attached"].round(2)
summary.to_csv(f"{OUTPUT_FOLDER}/summary_all_conditions.csv", index=False)
print(f"  Saved: summary_all_conditions.csv")

print(f"\nAll done. {OUTPUT_FOLDER}/ contains 9 plots + 1 summary CSV.")

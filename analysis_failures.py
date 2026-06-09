"""
analysis_failures.py
Root cause analysis of simulation failures.

Uses Peak_Attached as a proxy to classify failure type:
  - Search failure : failed AND Peak_Attached <= 2
                     (ants never found / attached to the object)
  - Stuck failure  : failed AND Peak_Attached >= 3
                     (ants attached but couldn't complete transport)

Output: results/analysis/failure_*.pdf
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import os

RESULTS_FOLDER = "results/run_20260608_140959"
OUTPUT_FOLDER  = "results/analysis"
SHAPES         = ["Circle", "Square", "L-shape", "C-shape"]
SHAPE_COLORS   = {
    "Circle":  "#2196F3",
    "Square":  "#4CAF50",
    "L-shape": "#FF9800",
    "C-shape": "#F44336",
}
SEARCH_THRESHOLD = 2   # Peak_Attached <= this → search failure
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
dfs = {}
for s in SHAPES:
    df = pd.read_csv(f"{RESULTS_FOLDER}/{s}.csv")
    df["Success"] = df["Success"].astype(str).str.strip().str.lower() == "true"
    df["Shape"] = s
    dfs[s] = df

all_df = pd.concat(dfs.values(), ignore_index=True)

# ── Classify failures ─────────────────────────────────────────────────────────
failed = all_df[~all_df["Success"]].copy()
failed["Failure_Type"] = failed["Peak_Attached"].apply(
    lambda p: "Search failure" if p <= SEARCH_THRESHOLD else "Stuck failure"
)

def save(name):
    path = f"{OUTPUT_FOLDER}/{name}.pdf"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {name}.pdf")


# ── Print summary ─────────────────────────────────────────────────────────────
print("=" * 65)
print("FAILURE ROOT CAUSE ANALYSIS")
print(f"Classification threshold: Peak_Attached <= {SEARCH_THRESHOLD} = Search failure")
print("=" * 65)

total_failed = len(failed)
search = (failed["Failure_Type"] == "Search failure").sum()
stuck  = (failed["Failure_Type"] == "Stuck failure").sum()
print(f"\nTotal failures : {total_failed} / {len(all_df)} ({total_failed/len(all_df)*100:.1f}%)")
print(f"Search failures: {search} ({search/total_failed*100:.1f}%)")
print(f"Stuck failures : {stuck}  ({stuck/total_failed*100:.1f}%)")

print("\n--- FAILURE TYPE BY SHAPE ---")
ft = failed.groupby(["Shape","Failure_Type"]).size().unstack(fill_value=0)
ft["Total_Failures"] = ft.sum(axis=1)
ft["Search_%"] = (ft.get("Search failure",0) / ft["Total_Failures"] * 100).round(1)
ft["Stuck_%"]  = (ft.get("Stuck failure",0)  / ft["Total_Failures"] * 100).round(1)
print(ft.to_string())

print("\n--- FAILURE TYPE BY SHAPE x SWARM SIZE ---")
ft2 = failed.groupby(["Shape","Swarm_Size","Failure_Type"]).size().unstack(fill_value=0)
print(ft2.to_string())


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 1 — Failure type breakdown by shape (stacked bar)
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: absolute counts
counts = failed.groupby(["Shape","Failure_Type"]).size().unstack(fill_value=0).reindex(SHAPES)
counts.plot(kind="bar", ax=axes[0], color=["#E57373","#64B5F6"],
            edgecolor="white", width=0.6)
axes[0].set_title("Failure Count by Type per Shape", fontsize=12, fontweight="bold")
axes[0].set_xlabel("")
axes[0].set_ylabel("Number of Failed Trials")
axes[0].set_xticklabels(SHAPES, rotation=0)
axes[0].legend(["Search failure\n(never attached)", "Stuck failure\n(attached but didn't finish)"],
               fontsize=9)
axes[0].spines[["top","right"]].set_visible(False)

# Right: percentage of failures
pct = counts.div(counts.sum(axis=1), axis=0) * 100
pct.plot(kind="bar", stacked=True, ax=axes[1], color=["#E57373","#64B5F6"],
         edgecolor="white", width=0.6)
axes[1].set_title("Failure Type Composition (%) per Shape", fontsize=12, fontweight="bold")
axes[1].set_xlabel("")
axes[1].set_ylabel("% of Failures")
axes[1].set_xticklabels(SHAPES, rotation=0)
axes[1].legend(["Search failure", "Stuck failure"], fontsize=9)
axes[1].spines[["top","right"]].set_visible(False)

plt.suptitle("Root Cause of Simulation Failures", fontsize=13, fontweight="bold")
plt.tight_layout()
save("failure_01_type_by_shape")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 2 — Failure type by swarm size for each shape
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
axes = axes.flatten()

for i, shape in enumerate(SHAPES):
    df_f = failed[failed["Shape"] == shape]
    ct = df_f.groupby(["Swarm_Size","Failure_Type"]).size().unstack(fill_value=0)
    # ensure both columns exist
    for col in ["Search failure","Stuck failure"]:
        if col not in ct:
            ct[col] = 0
    ct[["Search failure","Stuck failure"]].plot(
        kind="bar", ax=axes[i], color=["#E57373","#64B5F6"],
        edgecolor="white", width=0.65)
    axes[i].set_title(f"{shape}", fontsize=12, fontweight="bold",
                      color=SHAPE_COLORS[shape])
    axes[i].set_xlabel("Swarm Size")
    axes[i].set_ylabel("Failed Trials")
    axes[i].set_xticklabels([15,20,25,30,35], rotation=0)
    axes[i].legend(["Search failure","Stuck failure"], fontsize=9)
    axes[i].spines[["top","right"]].set_visible(False)

plt.suptitle("Failure Type by Swarm Size per Shape",
             fontsize=13, fontweight="bold")
plt.tight_layout()
save("failure_02_by_swarm_size")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 3 — Peak attached distribution: successes vs failures
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
axes = axes.flatten()

for i, shape in enumerate(SHAPES):
    df = dfs[shape]
    success_peak = df[df["Success"]]["Peak_Attached"]
    fail_peak    = df[~df["Success"]]["Peak_Attached"]
    bins = range(0, int(df["Peak_Attached"].max()) + 2)
    axes[i].hist(success_peak, bins=bins, alpha=0.6, color="#4CAF50",
                 label=f"Success (n={len(success_peak)})", density=True)
    axes[i].hist(fail_peak, bins=bins, alpha=0.6, color="#F44336",
                 label=f"Failure (n={len(fail_peak)})", density=True)
    axes[i].axvline(SEARCH_THRESHOLD + 0.5, color="black", linestyle="--",
                    linewidth=1.2, label=f"Search/Stuck threshold ({SEARCH_THRESHOLD})")
    axes[i].set_title(f"{shape}", fontsize=12, fontweight="bold",
                      color=SHAPE_COLORS[shape])
    axes[i].set_xlabel("Peak Attached")
    axes[i].set_ylabel("Density")
    axes[i].legend(fontsize=8)
    axes[i].spines[["top","right"]].set_visible(False)

plt.suptitle("Peak Attached Distribution: Successes vs Failures",
             fontsize=13, fontweight="bold")
plt.tight_layout()
save("failure_03_peak_attached_distribution")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 4 — Failure type heatmap by swarm size × shuffle randomness (per shape)
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 4, figsize=(18, 8))

for i, shape in enumerate(SHAPES):
    df_f = failed[failed["Shape"] == shape]
    total_f = dfs[shape][~dfs[shape]["Success"]]

    # search failure rate = search failures / total trials in that condition
    n_trials = dfs[shape].groupby(["Swarm_Size","Shuffle_Randomness"]).size()

    search_f = df_f[df_f["Failure_Type"] == "Search failure"].groupby(
        ["Swarm_Size","Shuffle_Randomness"]).size().reindex(n_trials.index, fill_value=0)
    stuck_f  = df_f[df_f["Failure_Type"] == "Stuck failure"].groupby(
        ["Swarm_Size","Shuffle_Randomness"]).size().reindex(n_trials.index, fill_value=0)

    search_pct = (search_f / n_trials * 100).unstack()
    stuck_pct  = (stuck_f  / n_trials * 100).unstack()

    sns.heatmap(search_pct, ax=axes[0][i], annot=True, fmt=".0f",
                cmap="Reds", vmin=0, vmax=50,
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "% of trials"})
    axes[0][i].set_title(f"{shape}\nSearch failures", fontsize=10,
                         fontweight="bold", color=SHAPE_COLORS[shape])
    axes[0][i].set_xlabel("Shuffle Randomness")
    axes[0][i].set_ylabel("Swarm Size")

    sns.heatmap(stuck_pct, ax=axes[1][i], annot=True, fmt=".0f",
                cmap="Blues", vmin=0, vmax=50,
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "% of trials"})
    axes[1][i].set_title(f"{shape}\nStuck failures", fontsize=10,
                         fontweight="bold", color=SHAPE_COLORS[shape])
    axes[1][i].set_xlabel("Shuffle Randomness")
    axes[1][i].set_ylabel("Swarm Size")

plt.suptitle("Failure Root Cause Heatmaps (% of all trials per condition)",
             fontsize=13, fontweight="bold")
plt.tight_layout()
save("failure_04_heatmaps")


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 5 — Mean peak attached: failed trials only, by shape × swarm size
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for shape in SHAPES:
    df_f = failed[failed["Shape"] == shape]
    pa = df_f.groupby("Swarm_Size")["Peak_Attached"].mean()
    ax.plot(pa.index, pa.values, marker="o", label=shape,
            color=SHAPE_COLORS[shape], linewidth=2.2, markersize=7)
ax.axhline(SEARCH_THRESHOLD, color="black", linestyle="--", linewidth=1,
           label=f"Search/Stuck threshold ({SEARCH_THRESHOLD})")
ax.set_xlabel("Swarm Size", fontsize=12)
ax.set_ylabel("Mean Peak Attached (failed trials)", fontsize=12)
ax.set_title("How 'close' were failed trials?\nMean Peak Attached in failures by Swarm Size",
             fontsize=12, fontweight="bold")
ax.set_xticks([15,20,25,30,35])
ax.legend(fontsize=10)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
save("failure_05_peak_in_failures")

print(f"\nDone. Failure analysis saved to {OUTPUT_FOLDER}/")

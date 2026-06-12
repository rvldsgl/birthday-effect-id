# Birthday Effect — Indonesia
# Analysis: Are Indonesians more likely to die on their birthday?
#
# Run: python analysis.py
# Input:  data/indonesian_deaths_raw.csv
# Output: data/charts/ (PNG charts)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import os
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
INPUT_FILE  = "data/indonesian_deaths_raw.csv"
CHART_DIR   = "data/charts"
os.makedirs(CHART_DIR, exist_ok=True)

# Color palette (clean, publication-ready)
C_BASE     = "#CCCCCC"   # default bars
C_HIGHLIGHT = "#E05A4E"  # birthday spike
C_LINE      = "#333333"  # average line
C_TEXT      = "#333333"

plt.rcParams.update({
    "font.family":     "serif",
    "font.size":       11,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.dpi":         150,
})


# ─────────────────────────────────────────────
# Step 1 — Load data
# ─────────────────────────────────────────────
def load_data(path):
    print(f"[1/5] Loading data from {path}...")
    df = pd.read_csv(path, parse_dates=["birth_date", "death_date"])
    print(f"      {len(df):,} records loaded")
    return df


# ─────────────────────────────────────────────
# Step 2 — Calculate birthday distance
#
# For each person, find how many days their death
# was from their nearest birthday.
#   0  = died on their birthday
#  +30 = died 30 days AFTER their birthday
#  -30 = died 30 days BEFORE their birthday
#
# Range: -182 to +182 (roughly ±6 months)
# ─────────────────────────────────────────────
def birthday_distance(birth_date, death_date):
    """
    Calculate days between death and the nearest birthday.
    Returns integer in range [-182, 182].
    """
    try:
        # Construct this year's birthday in the death year
        birthday_this_year = birth_date.replace(year=death_date.year)
    except ValueError:
        # Feb 29 leap year edge case — use Feb 28
        birthday_this_year = birth_date.replace(year=death_date.year, day=28)

    delta = (death_date - birthday_this_year).days

    # If more than +182 days after birthday, use NEXT year's birthday
    if delta > 182:
        delta -= 365
    # If more than -182 days before birthday, use PREVIOUS year's birthday
    elif delta < -182:
        delta += 365

    return delta


def compute_distances(df):
    print("[2/5] Computing birthday distances...")
    df["birthday_distance"] = df.apply(
        lambda row: birthday_distance(row["birth_date"], row["death_date"]),
        axis=1
    )

    # Count deaths on each relative day
    dist_counts = df["birthday_distance"].value_counts().sort_index()

    # Fill any missing days with 0
    full_range = pd.Series(0, index=range(-182, 183))
    dist_counts = (dist_counts + full_range).fillna(0).astype(int)

    on_birthday = dist_counts[0]
    avg_other_days = dist_counts[dist_counts.index != 0].mean()
    pct_excess = ((on_birthday - avg_other_days) / avg_other_days) * 100

    print(f"      Deaths on birthday (day 0)  : {on_birthday}")
    print(f"      Average deaths on other days: {avg_other_days:.1f}")
    print(f"      Excess on birthday          : {pct_excess:+.1f}%")

    return df, dist_counts, on_birthday, avg_other_days, pct_excess


# ─────────────────────────────────────────────
# Step 3 — Statistical test
# Is the spike at day 0 statistically significant?
# ─────────────────────────────────────────────
def statistical_test(dist_counts):
    print("[3/5] Running statistical test...")

    # Expected: if birthdays don't matter, deaths should be
    # uniformly distributed across all 365 days
    observed  = dist_counts[0]
    expected  = dist_counts.mean()
    n_days    = len(dist_counts)
    n_total   = dist_counts.sum()

    # Binomial test: is the number of birthday deaths
    # significantly higher than expected (1/365)?
    p_expected = 1 / n_days
    result = stats.binomtest(int(observed), int(n_total), p_expected, alternative="greater")
    p_value = result.pvalue

    print(f"      Observed birthday deaths : {observed}")
    print(f"      Expected (if random)     : {expected:.1f}")
    print(f"      p-value                  : {p_value:.4f}")
    print(f"      Significant (p<0.05)     : {'YES' if p_value < 0.05 else 'NO'}")

    return p_value


# ─────────────────────────────────────────────
# Chart 1 — Main distribution chart
# ─────────────────────────────────────────────
def chart_main_distribution(dist_counts, avg_other_days, pct_excess, p_value, n):
    print("[4/5] Creating charts...")

    fig, ax = plt.subplots(figsize=(12, 5))

    days  = dist_counts.index.tolist()
    counts = dist_counts.values.tolist()
    colors = [C_HIGHLIGHT if d == 0 else C_BASE for d in days]

    ax.bar(days, counts, color=colors, width=1.0, linewidth=0)

    # Average line
    ax.axhline(avg_other_days, color=C_LINE, linestyle="--",
               linewidth=1.2, label=f"Daily average ({avg_other_days:.1f})")

    # Annotate the birthday spike
    birthday_count = dist_counts[0]
    ax.annotate(
        f"Birthday\n{int(birthday_count)} deaths\n({pct_excess:+.1f}%)",
        xy=(0, birthday_count),
        xytext=(25, birthday_count + 2),
        fontsize=9,
        color=C_HIGHLIGHT,
        arrowprops=dict(arrowstyle="-", color=C_HIGHLIGHT, lw=1.2),
        ha="left"
    )

    # Labels
    ax.set_xlabel("Days relative to birthday  (0 = birthday, negative = before, positive = after)",
                  fontsize=10, color=C_TEXT)
    ax.set_ylabel("Number of deaths", fontsize=10, color=C_TEXT)
    ax.set_title(
        f"Are Indonesians more likely to die on their birthday?\n"
        f"n = {n:,} notable Indonesians from Wikidata  |  "
        f"p = {p_value:.3f}",
        fontsize=12, color=C_TEXT, pad=12
    )

    # X-axis labels
    ax.set_xticks([-180, -120, -60, 0, 60, 120, 180])
    ax.set_xticklabels(["-6 mo", "-4 mo", "-2 mo", "Birthday", "+2 mo", "+4 mo", "+6 mo"],
                       fontsize=9)

    legend_patch = mpatches.Patch(color=C_HIGHLIGHT, label="Birthday (day 0)")
    ax.legend(handles=[legend_patch,
                        plt.Line2D([0], [0], color=C_LINE, linestyle="--", label=f"Daily avg ({avg_other_days:.1f})")],
              frameon=False, fontsize=9)

    plt.tight_layout()
    path = f"{CHART_DIR}/01_birthday_distribution.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"      Saved: {path}")


# ─────────────────────────────────────────────
# Chart 2 — Zoom in: ±30 days around birthday
# ─────────────────────────────────────────────
def chart_zoomed(dist_counts, avg_other_days):
    fig, ax = plt.subplots(figsize=(10, 4))

    window = 30
    days   = list(range(-window, window + 1))
    counts = [dist_counts.get(d, 0) for d in days]
    colors = [C_HIGHLIGHT if d == 0 else C_BASE for d in days]

    ax.bar(days, counts, color=colors, width=0.85, linewidth=0)
    ax.axhline(avg_other_days, color=C_LINE, linestyle="--",
               linewidth=1.2, label=f"Daily average")

    ax.set_xlabel("Days relative to birthday", fontsize=10)
    ax.set_ylabel("Number of deaths", fontsize=10)
    ax.set_title("Zoomed view: 30 days around birthday", fontsize=12, pad=10)
    ax.set_xticks(range(-30, 31, 5))

    birthday_count = dist_counts[0]
    ax.annotate(
        f"{int(birthday_count)}",
        xy=(0, birthday_count),
        xytext=(0, birthday_count + 0.5),
        ha="center", fontsize=9, color=C_HIGHLIGHT, fontweight="bold"
    )

    ax.legend(frameon=False, fontsize=9)
    plt.tight_layout()
    path = f"{CHART_DIR}/02_birthday_zoomed.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"      Saved: {path}")


# ─────────────────────────────────────────────
# Chart 3 — Breakdown by gender
# ─────────────────────────────────────────────
def chart_by_gender(df):
    genders = df["gender"].dropna().unique()
    main_genders = [g for g in ["male", "female"] if g in genders]

    if len(main_genders) < 2:
        print("      Skipping gender chart (insufficient data)")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=False)

    for ax, gender in zip(axes, main_genders):
        subset = df[df["gender"] == gender]
        dist = subset["birthday_distance"].value_counts().sort_index()
        full = pd.Series(0, index=range(-182, 183))
        dist = (dist + full).fillna(0).astype(int)

        avg = dist[dist.index != 0].mean()
        days   = dist.index.tolist()
        counts = dist.values.tolist()
        colors = [C_HIGHLIGHT if d == 0 else C_BASE for d in days]

        ax.bar(days, counts, color=colors, width=1.0, linewidth=0)
        ax.axhline(avg, color=C_LINE, linestyle="--", linewidth=1.2)

        on_bday = dist[0]
        pct = ((on_bday - avg) / avg) * 100
        ax.set_title(f"{gender.capitalize()}  (n={len(subset):,})\nBirthday: {int(on_bday)} deaths  ({pct:+.1f}%)",
                     fontsize=11)
        ax.set_xticks([-180, -90, 0, 90, 180])
        ax.set_xticklabels(["-6mo", "-3mo", "Bday", "+3mo", "+6mo"], fontsize=8)
        ax.set_ylabel("Deaths", fontsize=9)

    plt.suptitle("Birthday effect by gender", fontsize=13, y=1.01)
    plt.tight_layout()
    path = f"{CHART_DIR}/03_birthday_by_gender.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"      Saved: {path}")


# ─────────────────────────────────────────────
# Chart 4 — Breakdown by age group
# ─────────────────────────────────────────────
def chart_by_age(df):
    bins   = [0, 40, 60, 75, 200]
    labels = ["Under 40", "40-59", "60-74", "75+"]
    df["age_group"] = pd.cut(df["age_at_death_years"], bins=bins, labels=labels)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=False)

    for ax, group in zip(axes, labels):
        subset = df[df["age_group"] == group]
        if len(subset) < 20:
            ax.set_title(f"{group}\n(too few records)")
            ax.axis("off")
            continue

        dist = subset["birthday_distance"].value_counts().sort_index()
        full = pd.Series(0, index=range(-182, 183))
        dist = (dist + full).fillna(0).astype(int)

        avg  = dist[dist.index != 0].mean()
        on_bday = dist[0]
        pct  = ((on_bday - avg) / avg) * 100

        days   = dist.index.tolist()
        counts = dist.values.tolist()
        colors = [C_HIGHLIGHT if d == 0 else C_BASE for d in days]

        ax.bar(days, counts, color=colors, width=1.0, linewidth=0)
        ax.axhline(avg, color=C_LINE, linestyle="--", linewidth=1.0)
        ax.set_title(f"{group}  (n={len(subset):,})\n{int(on_bday)} bday deaths  ({pct:+.1f}%)",
                     fontsize=10)
        ax.set_xticks([-180, 0, 180])
        ax.set_xticklabels(["-6mo", "Bday", "+6mo"], fontsize=8)

    plt.suptitle("Birthday effect by age group", fontsize=13, y=1.01)
    plt.tight_layout()
    path = f"{CHART_DIR}/04_birthday_by_age.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"      Saved: {path}")


# ─────────────────────────────────────────────
# Step 5 — Print article-ready findings
# ─────────────────────────────────────────────
def print_findings(df, dist_counts, avg_other_days, pct_excess, p_value):
    print("\n[5/5] Key findings for your article")
    print("=" * 50)

    n = len(df)
    on_birthday = dist_counts[0]

    print(f"  Dataset         : {n:,} notable Indonesians")
    print(f"  Date range      : {df['death_date'].min().year} - {df['death_date'].max().year}")
    print(f"  Avg age at death: {df['age_at_death_years'].mean():.1f} years")
    print()
    print(f"  Deaths on birthday   : {int(on_birthday)}")
    print(f"  Expected (avg day)   : {avg_other_days:.1f}")
    print(f"  Excess on birthday   : {pct_excess:+.1f}%")
    print(f"  Statistically sig?   : {'YES (p < 0.05)' if p_value < 0.05 else 'NO (p >= 0.05)'}")
    print(f"  p-value              : {p_value:.4f}")
    print()

    # Day before and after for context
    day_minus1 = dist_counts.get(-1, 0)
    day_plus1  = dist_counts.get(1, 0)
    print(f"  Deaths day before bday : {int(day_minus1)}")
    print(f"  Deaths on birthday     : {int(on_birthday)}")
    print(f"  Deaths day after bday  : {int(day_plus1)}")
    print()
    print(f"  Charts saved to: {CHART_DIR}/")
    print("=" * 50)

    if p_value < 0.05:
        print()
        print("  FINDING: Yes, Indonesians are more likely to")
        print(f"  die on their birthday ({pct_excess:+.1f}% above average).")
        print("  The effect is statistically significant.")
    else:
        print()
        print("  FINDING: The data does not show a statistically")
        print("  significant birthday effect in this sample.")
        print("  This could be due to small sample size or")
        print("  the Wikidata bias toward notable people.")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  Birthday Effect - Indonesia  |  Analysis")
    print("=" * 50)
    print()

    df = load_data(INPUT_FILE)
    print()

    df, dist_counts, on_birthday, avg_other_days, pct_excess = compute_distances(df)
    print()

    p_value = statistical_test(dist_counts)
    print()

    chart_main_distribution(dist_counts, avg_other_days, pct_excess, p_value, len(df))
    chart_zoomed(dist_counts, avg_other_days)
    chart_by_gender(df)
    chart_by_age(df)

    print_findings(df, dist_counts, avg_other_days, pct_excess, p_value)


if __name__ == "__main__":
    main()

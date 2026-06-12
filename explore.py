# Birthday Effect â€” Indonesia
# Deeper exploration
#
# Run: python explore.py
# Input:  data/indonesian_deaths_raw.csv
# Output: prints findings + saves extra charts to data/charts/

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import requests
import json
import os
import warnings
warnings.filterwarnings("ignore")

CHART_DIR = "data/charts"
os.makedirs(CHART_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family":        "serif",
    "font.size":          11,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.dpi":         150,
})

C_BASE      = "#CCCCCC"
C_HIGHLIGHT = "#E05A4E"
C_SMOOTH    = "#2C7BB6"
C_LINE      = "#333333"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Helpers
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def birthday_distance(birth_date, death_date):
    try:
        bday = birth_date.replace(year=death_date.year)
    except ValueError:
        bday = birth_date.replace(year=death_date.year, day=28)
    delta = (death_date - bday).days
    if delta > 182:
        delta -= 365
    elif delta < -182:
        delta += 365
    return delta


def build_dist(df):
    counts = df["birthday_distance"].value_counts().sort_index()
    full   = pd.Series(0, index=range(-182, 183))
    return (counts + full).fillna(0).astype(int)


def excess_and_pvalue(dist_counts, n_total):
    on_bday  = dist_counts[0]
    avg      = dist_counts[dist_counts.index != 0].mean()
    pct      = ((on_bday - avg) / avg) * 100
    result   = stats.binomtest(int(on_bday), int(n_total), 1/len(dist_counts), alternative="greater")
    return int(on_bday), avg, pct, result.pvalue


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. Load + compute distances
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("=" * 55)
print("  Birthday Effect - Indonesia  |  Deep Exploration")
print("=" * 55)

df = pd.read_csv("data/indonesian_deaths_raw.csv",
                 parse_dates=["birth_date", "death_date"])

df["birthday_distance"] = df.apply(
    lambda r: birthday_distance(r["birth_date"], r["death_date"]), axis=1
)

print(f"\nLoaded {len(df):,} records")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. Who are the 17 birthday deaths?
#    Inspect them to check for data artifacts
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "â”€" * 55)
print("  SECTION 1: Who died on their birthday?")
print("â”€" * 55)

birthday_deaths = df[df["birthday_distance"] == 0].copy()
birthday_deaths["age"] = birthday_deaths["age_at_death_years"]

cols = ["name", "birth_date", "death_date", "age", "gender"]
available = [c for c in cols if c in birthday_deaths.columns]
print(birthday_deaths[available].to_string(index=False))
print(f"\nTotal: {len(birthday_deaths)} people")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3. 7-day birthday window
#    Do people die more in the WEEK of their birthday?
#    (not just the exact day)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "â”€" * 55)
print("  SECTION 2: 7-day birthday window (-3 to +3 days)")
print("â”€" * 55)

window_deaths = df[df["birthday_distance"].between(-3, 3)]
window_count  = len(window_deaths)
expected_week = (len(df) / 365) * 7
pct_week      = ((window_count - expected_week) / expected_week) * 100

result_week = stats.binomtest(
    window_count, len(df), 7/365, alternative="greater"
)

print(f"  Deaths in birthday week (-3 to +3): {window_count}")
print(f"  Expected if random               : {expected_week:.1f}")
print(f"  Excess                           : {pct_week:+.1f}%")
print(f"  p-value                          : {result_week.pvalue:.4f}")
print(f"  Significant (p<0.05)             : {'YES' if result_week.pvalue < 0.05 else 'NO'}")

# Day-by-day breakdown of the window
print(f"\n  Day-by-day breakdown:")
for d in range(-3, 4):
    count = len(df[df["birthday_distance"] == d])
    marker = " <-- birthday" if d == 0 else ""
    print(f"    Day {d:+d}: {count} deaths{marker}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 4. Age subgroup: 60+ vs under 60
#    Birthday effect should be stronger in elderly
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "â”€" * 55)
print("  SECTION 3: Age subgroup analysis")
print("â”€" * 55)

for label, subset in [("Under 60", df[df["age_at_death_years"] < 60]),
                       ("Age 60-74", df[(df["age_at_death_years"] >= 60) & (df["age_at_death_years"] < 75)]),
                       ("Age 75+",  df[df["age_at_death_years"] >= 75])]:
    if len(subset) < 10:
        continue
    dist  = build_dist(subset)
    on_b, avg, pct, pval = excess_and_pvalue(dist, len(subset))
    sig   = "YES" if pval < 0.05 else "no"
    print(f"  {label:<12}  n={len(subset):>4}  bday deaths={on_b:>2}  "
          f"avg={avg:.1f}  excess={pct:+.1f}%  p={pval:.3f}  sig={sig}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 5. Decade analysis
#    Does the effect vary by era?
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "â”€" * 55)
print("  SECTION 4: By decade of death")
print("â”€" * 55)

df["decade"] = (df["death_date"].dt.year // 10) * 10
for decade, subset in df.groupby("decade"):
    if len(subset) < 30:
        continue
    dist  = build_dist(subset)
    on_b, avg, pct, pval = excess_and_pvalue(dist, len(subset))
    sig   = "*" if pval < 0.05 else ""
    print(f"  {decade}s  n={len(subset):>4}  bday={on_b:>2}  "
          f"avg={avg:.1f}  excess={pct:+.1f}%  p={pval:.3f} {sig}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 6. Fetch additional data: people BORN in Indonesia
#    (different from citizenship â€” catches diaspora
#    and historical figures from pre-independence era)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "â”€" * 55)
print("  SECTION 5: Expanding dataset")
print("  Fetching people BORN in Indonesia from Wikidata...")
print("â”€" * 55)

QUERY_BORN = """
SELECT DISTINCT ?person ?personLabel ?birthDate ?deathDate ?genderLabel WHERE {
  ?person wdt:P31 wd:Q5 .
  ?person wdt:P19 wd:Q252 .

  ?person p:P569 ?birthStatement .
  ?birthStatement psv:P569 ?birthValue .
  ?birthValue wikibase:timeValue ?birthDate .
  ?birthValue wikibase:timePrecision ?birthPrecision .

  ?person p:P570 ?deathStatement .
  ?deathStatement psv:P570 ?deathValue .
  ?deathValue wikibase:timeValue ?deathDate .
  ?deathValue wikibase:timePrecision ?deathPrecision .

  OPTIONAL { ?person wdt:P21 ?gender . }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,id" . }

  FILTER(?birthPrecision >= 11)
  FILTER(?deathPrecision >= 11)
  FILTER(?deathDate >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
}
ORDER BY ?deathDate
"""

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS  = {
    "User-Agent": "BirthdayEffectResearch/1.0",
    "Accept":     "application/json",
}

try:
    resp = requests.get(ENDPOINT,
                        params={"query": QUERY_BORN, "format": "json"},
                        headers=HEADERS, timeout=90)
    resp.raise_for_status()
    born_results = resp.json()["results"]["bindings"]
    print(f"  [OK] Got {len(born_results)} raw records (born in Indonesia)")

    from datetime import datetime

    born_records = []
    seen = set()
    for row in born_results:
        try:
            pid        = row["person"]["value"].split("/")[-1]
            name       = row.get("personLabel", {}).get("value", "Unknown")
            birth_str  = row["birthDate"]["value"]
            death_str  = row["deathDate"]["value"]
            gender     = row.get("genderLabel", {}).get("value", None)

            birth_date = datetime.fromisoformat(birth_str.replace("Z", "+00:00")).date()
            death_date = datetime.fromisoformat(death_str.replace("Z", "+00:00")).date()

            if death_date <= birth_date:
                continue
            age_days = (death_date - birth_date).days
            if age_days < 1 or age_days > 130 * 365:
                continue

            key = (pid, str(birth_date), str(death_date))
            if key in seen:
                continue
            seen.add(key)

            born_records.append({
                "person_id":          pid,
                "name":               name,
                "birth_date":         str(birth_date),
                "death_date":         str(death_date),
                "birth_month":        birth_date.month,
                "birth_day":          birth_date.day,
                "death_month":        death_date.month,
                "death_day":          death_date.day,
                "age_at_death_days":  age_days,
                "age_at_death_years": round(age_days / 365.25, 1),
                "gender":             gender,
            })
        except Exception:
            continue

    df_born = pd.DataFrame(born_records)
    df_born["birth_date"] = pd.to_datetime(df_born["birth_date"])
    df_born["death_date"] = pd.to_datetime(df_born["death_date"])

    print(f"  [OK] {len(df_born):,} unique records (born in Indonesia)")

    # Merge with citizenship dataset, drop duplicates
    df_combined = pd.concat([df, df_born], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=["person_id"]).reset_index(drop=True)

    df_combined["birthday_distance"] = df_combined.apply(
        lambda r: birthday_distance(r["birth_date"], r["death_date"]), axis=1
    )

    df_combined.to_csv("data/indonesian_deaths_combined.csv", index=False)
    print(f"  [OK] Combined dataset: {len(df_combined):,} records saved to data/indonesian_deaths_combined.csv")

    # Run analysis on combined dataset
    dist_comb = build_dist(df_combined)
    on_b, avg, pct, pval = excess_and_pvalue(dist_comb, len(df_combined))

    print(f"\n  COMBINED RESULTS:")
    print(f"  Total records     : {len(df_combined):,}")
    print(f"  Birthday deaths   : {on_b}")
    print(f"  Daily average     : {avg:.1f}")
    print(f"  Excess            : {pct:+.1f}%")
    print(f"  p-value           : {pval:.4f}")
    print(f"  Significant       : {'YES' if pval < 0.05 else 'NO'}")

    use_df = df_combined

except Exception as e:
    print(f"  [FAIL] Could not fetch born-in-Indonesia data: {e}")
    print("  Continuing with existing dataset only.")
    use_df = df


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 7. Chart: smoothed distribution
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "â”€" * 55)
print("  Generating smoothed chart...")

dist_use = build_dist(use_df)
avg_use  = dist_use[dist_use.index != 0].mean()
days     = dist_use.index.tolist()
counts   = dist_use.values.tolist()

# 7-day rolling average
series   = pd.Series(counts, index=days)
smoothed = series.rolling(7, center=True, min_periods=1).mean()

fig, ax = plt.subplots(figsize=(12, 5))

bar_colors = [C_HIGHLIGHT if d == 0 else C_BASE for d in days]
ax.bar(days, counts, color=bar_colors, width=1.0, linewidth=0, alpha=0.7, label="Daily deaths")
ax.plot(days, smoothed.values, color=C_SMOOTH, linewidth=2, label="7-day rolling avg")
ax.axhline(avg_use, color=C_LINE, linestyle="--", linewidth=1.2, label=f"Daily avg ({avg_use:.1f})")

on_b_use = dist_use[0]
pct_use  = ((on_b_use - avg_use) / avg_use) * 100
ax.annotate(
    f"Birthday\n{int(on_b_use)} deaths ({pct_use:+.1f}%)",
    xy=(0, on_b_use),
    xytext=(30, on_b_use + 2),
    fontsize=9, color=C_HIGHLIGHT,
    arrowprops=dict(arrowstyle="-", color=C_HIGHLIGHT, lw=1.2),
)

ax.set_xlabel("Days relative to birthday  (0 = birthday)", fontsize=10)
ax.set_ylabel("Number of deaths", fontsize=10)
ax.set_title(
    f"Birthday effect â€” Indonesia  |  n = {len(use_df):,}  |  +{pct_use:.1f}% on birthday",
    fontsize=12, pad=12
)
ax.set_xticks([-180, -120, -60, 0, 60, 120, 180])
ax.set_xticklabels(["-6 mo", "-4 mo", "-2 mo", "Birthday", "+2 mo", "+4 mo", "+6 mo"])
ax.legend(frameon=False, fontsize=9)

plt.tight_layout()
path = f"{CHART_DIR}/05_smoothed_distribution.png"
plt.savefig(path, bbox_inches="tight")
plt.close()
print(f"  Saved: {path}")

print("\n" + "=" * 55)
print("  Exploration complete.")
print("=" * 55)


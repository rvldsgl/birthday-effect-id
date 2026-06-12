# Birthday Effect — Indonesia
# Are Indonesians more likely to die on their birthday?
#
# Data source: Wikidata (structured Wikipedia database)
# Query: All notable Indonesians with known birth date + death date
#
# Run: python scraper.py
# Output: data/indonesian_deaths_raw.csv

import requests
import pandas as pd
import time
import json
from datetime import datetime

# ─────────────────────────────────────────────
# Wikidata SPARQL endpoint
# ─────────────────────────────────────────────
ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "BirthdayEffectResearch/1.0 (personal research project; contact via github)",
    "Accept": "application/json",
}

# ─────────────────────────────────────────────
# SPARQL query
# Gets all notable Indonesians with both birth
# and death dates recorded on Wikidata.
# ─────────────────────────────────────────────
QUERY = """
SELECT DISTINCT ?person ?personLabel ?birthDate ?deathDate ?birthPrecision ?deathPrecision ?genderLabel WHERE {

  # Must be a human
  ?person wdt:P31 wd:Q5 .

  # Must have Indonesian citizenship
  ?person wdt:P27 wd:Q252 .

  # Birth date — with precision check
  ?person p:P569 ?birthStatement .
  ?birthStatement psv:P569 ?birthValue .
  ?birthValue wikibase:timeValue ?birthDate .
  ?birthValue wikibase:timePrecision ?birthPrecision .

  # Death date — with precision check
  ?person p:P570 ?deathStatement .
  ?deathStatement psv:P570 ?deathValue .
  ?deathValue wikibase:timeValue ?deathDate .
  ?deathValue wikibase:timePrecision ?deathPrecision .

  # Optional: gender
  OPTIONAL { ?person wdt:P21 ?gender . }

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en,id" .
  }

  # CRITICAL: Only keep dates with day-level precision (11)
  # 9 = year only, 10 = month only, 11 = full day — we want 11
  FILTER(?birthPrecision >= 11)
  FILTER(?deathPrecision >= 11)

  # Only post-1900 deaths
  FILTER(?deathDate >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
}
ORDER BY ?deathDate
"""

def fetch_wikidata(query, retries=3, delay=5):
    """
    Query the Wikidata SPARQL endpoint.
    Returns list of result bindings, or None on failure.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"  Querying Wikidata... (attempt {attempt}/{retries})")
            response = requests.get(
                ENDPOINT,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            results = data["results"]["bindings"]
            print(f"  [OK] Got {len(results)} raw records")
            return results

        except requests.exceptions.Timeout:
            print(f"  [FAIL] Timeout on attempt {attempt}")
        except requests.exceptions.HTTPError as e:
            print(f"  [FAIL] HTTP error: {e}")
        except json.JSONDecodeError:
            print(f"  [FAIL] Failed to parse JSON response")
        except Exception as e:
            print(f"  [FAIL] Unexpected error: {e}")

        if attempt < retries:
            print(f"  Waiting {delay}s before retry...")
            time.sleep(delay)

    return None


def parse_results(results):
    """
    Parse raw Wikidata SPARQL results into a clean list of dicts.
    """
    records = []
    seen = set()  # deduplicate by person + dates

    for row in results:
        try:
            person_id   = row["person"]["value"].split("/")[-1]
            name        = row.get("personLabel", {}).get("value", "Unknown")
            birth_str   = row["birthDate"]["value"]
            death_str   = row["deathDate"]["value"]
            gender      = row.get("genderLabel", {}).get("value", None)
            occupation  = row.get("occupationLabel", {}).get("value", None)

            # Parse ISO datetime strings → date only
            birth_date = datetime.fromisoformat(birth_str.replace("Z", "+00:00")).date()
            death_date = datetime.fromisoformat(death_str.replace("Z", "+00:00")).date()

            # Skip clearly bad data (died before born, or same year edge cases)
            if death_date <= birth_date:
                continue

            # Skip if age at death is implausibly high (>130) or low (<1 day)
            age_at_death = (death_date - birth_date).days
            if age_at_death < 1 or age_at_death > 130 * 365:
                continue

            # Deduplicate (Wikidata can return multiple rows per person
            # if they have multiple occupations)
            key = (person_id, str(birth_date), str(death_date))
            if key in seen:
                continue
            seen.add(key)

            records.append({
                "person_id":   person_id,
                "name":        name,
                "birth_date":  str(birth_date),
                "death_date":  str(death_date),
                "birth_month": birth_date.month,
                "birth_day":   birth_date.day,
                "death_month": death_date.month,
                "death_day":   death_date.day,
                "age_at_death_days": age_at_death,
                "age_at_death_years": round(age_at_death / 365.25, 1),
                "gender":      gender,
                "occupation":  occupation,
                # Key field: days between death and nearest birthday
                # 0 = died on birthday
                # We compute this in analysis.py
            })

        except Exception as e:
            # Skip malformed rows silently
            continue

    return records


def save(records, path="data/indonesian_deaths_raw.csv"):
    df = pd.DataFrame(records)

    # Sort by death date
    df["death_date"] = pd.to_datetime(df["death_date"])
    df["birth_date"] = pd.to_datetime(df["birth_date"])
    df = df.sort_values("death_date").reset_index(drop=True)

    df.to_csv(path, index=False)
    print(f"  [OK] Saved {len(df)} records to {path}")
    return df


def main():
    print("=" * 50)
    print("  Birthday Effect — Indonesia")
    print("  Data collection via Wikidata SPARQL")
    print("=" * 50)
    print()

    # 1. Fetch
    print("[1/3] Fetching from Wikidata...")
    results = fetch_wikidata(QUERY)
    if not results:
        print("\n[FAIL] Failed to fetch data. Check your internet connection.")
        return

    # 2. Parse
    print("\n[2/3] Parsing and cleaning records...")
    records = parse_results(results)
    print(f"  [OK] {len(records)} clean unique records after deduplication")

    if len(records) == 0:
        print("\n[FAIL] No valid records found. The query may have timed out.")
        print("  Try running again — Wikidata can be slow.")
        return

    # 3. Save
    print("\n[3/3] Saving to CSV...")
    df = save(records)

    # Quick summary
    print()
    print("-" * 50)
    print("  SUMMARY")
    print("-" * 50)
    print(f"  Total records    : {len(df):,}")
    print(f"  Date range       : {df['death_date'].min().year} – {df['death_date'].max().year}")
    print(f"  Avg age at death : {df['age_at_death_years'].mean():.1f} years")
    if "gender" in df.columns:
        gender_counts = df["gender"].value_counts()
        for g, n in gender_counts.head(3).items():
            print(f"  {g:<20}: {n:,}")
    print()
    print("  -> Next step: run  python analysis.py")
    print("=" * 50)


if __name__ == "__main__":
    main()

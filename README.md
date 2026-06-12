# Birthday Effect — Indonesia

**Are Indonesians more likely to die on their birthday?**

A personal data project replicating [The Pudding's birthday effect analysis](https://pudding.cool/2025/04/birthday-effect) using Indonesian data from Wikidata.

## Findings

- **3,924 notable Indonesians** with precise birth and death dates (1902–2026)
- Exact birthday: **17 deaths** vs 10.7 expected → **+58%, p = 0.047** (barely significant)
- Birthday week (±3 days): **93 deaths** vs 75.3 expected → **+23.6%, p = 0.025** (more convincing)
- Effect is directionally consistent with global research but not definitive given the small, biased sample

Full write-up: [revaldosagala.me/writing/birthday-effect](https://revaldosagala.me/writing/birthday-effect)

## Data Source

[Wikidata](https://www.wikidata.org) via SPARQL — filtered for day-level precision dates only (`wikibase:timePrecision >= 11`). Imprecise dates default to January 1st and create a fake birthday spike; the precision filter removes this artifact.

## Files

| File | Description |
|---|---|
| `scraper.py` | Fetches data from Wikidata SPARQL API |
| `analysis.py` | Birthday distance calculation + charts |
| `explore.py` | Deeper analysis — age groups, decades, birthday week |
| `data/indonesian_deaths_raw.csv` | Clean dataset (3,924 records) |
| `data/charts/` | Generated charts |
| `article_draft.md` | Article text |

## Run it yourself

```bash
pip install -r requirements.txt
python scraper.py       # fetch data → data/indonesian_deaths_raw.csv
python analysis.py      # run analysis → data/charts/
python explore.py       # deeper exploration
```

## Limitations

- Wikidata only covers notable Indonesians, not the general population
- Sample size (3,924) is small compared to proper mortality studies
- No cause-of-death data available
- No seasonal death rate correction applied

A proper study would require access to Indonesia's Dukcapil civil registration records.

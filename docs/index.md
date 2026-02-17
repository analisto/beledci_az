# Documentation Index

**Project:** Beledci.az Customer Experience Intelligence
**Platform:** [beledci.az](https://beledci.az) — Azerbaijan's leading consumer review portal
**Scope:** 139 companies · 16 industry sectors · 2,856 customer reviews

---

## Project Structure

```
beledci_az/
├── data/
│   ├── companies.csv       # 139 companies across 16 categories
│   └── feedbacks.csv       # 2,856 customer reviews (all 106 pages)
├── charts/                 # 12 PNG charts (generated)
├── scripts/
│   ├── feedback.py         # Scrapes review feed → feedbacks.csv
│   ├── companies.py        # Scrapes company profiles → companies.csv
│   └── generate_charts.py  # Reads both CSVs → produces all charts
├── docs/                   # This documentation
│   ├── index.md            # This file
│   ├── data_dictionary.md  # Field definitions for both CSV files
│   ├── scripts.md          # Usage guide and architecture for all scripts
│   └── charts.md           # Catalogue of all 12 charts
└── README.md               # Executive report (12 findings + recommendations)
```

---

## Quick Start

### 1. Re-collect data

```bash
# Scrape all reviews
python scripts/feedback.py

# Scrape all company profiles
python scripts/companies.py
```

### 2. Regenerate charts

```bash
python scripts/generate_charts.py
```

Requirements: `pip install requests beautifulsoup4 pandas matplotlib numpy`

### 3. Read the report

Open `README.md` for the full 12-finding executive analysis with strategic recommendations.

---

## Documentation Pages

| File | Contents |
|---|---|
| [data_dictionary.md](data_dictionary.md) | Field-by-field definitions for `feedbacks.csv` and `companies.csv`, including the full category reference table. |
| [scripts.md](scripts.md) | CLI usage, arguments, scraping flow, and architecture notes for all three scripts. |
| [charts.md](charts.md) | Catalogue of all 12 charts: chart type, data source, key finding, and README cross-reference for each. |

---

## Key Numbers

| Metric | Value |
|---|---|
| Total reviews | 2,856 |
| 1-star reviews | 86.6% |
| Total companies | 139 |
| Companies rated "Low" | 80 (57.6%) |
| Companies with zero reviews | 44 (31.7%) |
| Sectors covered | 16 |
| Highest-volume sector | Internet Providers (645 reviews) |
| Best average sector rating | Beauty & Care (2.0 / 5.0) |
| Charts generated | 12 |

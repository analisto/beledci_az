# Scripts Reference

All scripts live in the `scripts/` directory and are run from the project root.

---

## feedback.py

Scrapes the public review feed from beledci.az and writes all reviews to `data/feedbacks.csv`.

### Usage

```bash
# Scrape all pages (auto-detects last page)
python scripts/feedback.py

# Scrape with a slower delay to reduce server load
python scripts/feedback.py --delay 1.0

# Scrape a specific page range
python scripts/feedback.py --start 50 --end 60
```

### CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--start` | `1` | First page to scrape. |
| `--end` | auto | Last page to scrape. If omitted, auto-detected from the pagination element on the first page. |
| `--delay` | `0.5` | Seconds to wait between page requests. |

### How It Works

1. Fetches the homepage (`/?page=1`) and reads `div.pagination span.last a` to find the last page number.
2. Iterates pages 1 through N, parsing each `div.review` block.
3. For each review extracts: `review_id` (from element id), `reviewer_name`, `company_name`, `company_slug`, `company_url`, `rating` (filled star count), `review_text`, `review_url`, `has_images`, `page`.
4. Flushes rows to CSV after each page so partial runs are not lost.

### Output

`data/feedbacks.csv` — 2,856 rows across 106 pages (full platform as of collection date).

---

## companies.py

Scrapes all 139 company profiles from beledci.az across 16 categories, enriched with numeric ratings from individual profile pages.

### Usage

```bash
# Full two-pass scrape (category listings + profile pages)
python scripts/companies.py

# Faster run — skip individual profile pages (less data)
python scripts/companies.py --skip-profile

# Custom delay
python scripts/companies.py --delay 1.0
```

### CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--delay` | `0.5` | Seconds to wait between requests. |
| `--skip-profile` | off | If set, skips Step 2 (profile page fetch). `rating_value` and `category_label` fields will be empty. |

### How It Works

**Step 1 — Category listing pages:**
Fetches `/cat/{slug}` for each of the 16 hardcoded categories. Parses each `a.company-card` element to extract: `slug`, `name`, `photo_url`, `rating_stars`, `rating_label`, `review_count`. Deduplicates companies that appear under multiple categories (keeps first occurrence).

**Step 2 — Company profile pages:**
Fetches `/{slug}` for each unique company. Extracts `rating_value` (numeric, from `div.company-general div.rate`) and `category_label` (from `a.company-category`).

### Output

`data/companies.csv` — 139 companies, sorted by `category_slug` then `name`.

---

## generate_charts.py

Reads both CSV files and produces all 12 analysis charts into `charts/`.

### Usage

```bash
python scripts/generate_charts.py
```

No CLI arguments. Overwrites existing PNG files in `charts/`.

### Dependencies

```
pandas
matplotlib
numpy
```

Install with:

```bash
pip install pandas matplotlib numpy
```

### Architecture

The script is structured as a series of independent chart functions, each called from `main()`.

```
main()
├── load_data()              # reads feedbacks.csv + companies.csv → DataFrames
├── chart_01_sentiment()
├── chart_02_top_companies()
├── chart_03_one_star_rate()
├── chart_04_review_volume()
├── chart_05_avg_rating()
├── chart_06_rating_labels()
├── chart_07_zero_review_gap()
├── chart_08_photo_evidence()
├── chart_09_best_performers()
├── chart_10_crisis_matrix()
├── chart_11_review_stream()
└── chart_12_top3_per_category()
```

A shared `save(fig, name)` helper writes each figure to `charts/{name}.png` at 150 DPI and closes the figure.

### Key Design Decisions

- **No pie charts.** All proportional comparisons use horizontal bar charts.
- **Consistent color scheme.** Brand red `#E63946`, neutral blue `#457B9D`, gold `#F4A261`.
- **Chart 10 (Sector Risk Matrix)** uses a dual annotation system:
  - Left column (6 low-volume categories): stacked vertically at data x=−200, connected to their data points via leader lines (`arrowprops`).
  - Right group (10 remaining categories): per-category `(dx, dy)` offset in points using `textcoords='offset points'`.
  - Quadrant label positions are computed in axes-fraction coordinates using `(data_x - xlim_lo) / (xlim_hi - xlim_lo)` to correctly account for the negative left x-limit.

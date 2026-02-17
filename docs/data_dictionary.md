# Data Dictionary

Reference for all fields in the two primary datasets.

---

## feedbacks.csv

**Location:** `data/feedbacks.csv`
**Records:** 2,856 reviews
**Source:** All 106 pages of the public review feed at beledci.az

| Field | Type | Description |
|---|---|---|
| `review_id` | integer | Unique review ID extracted from the HTML element `id` attribute on `p.review-text`. Assigned by beledci.az. |
| `reviewer_name` | string | Display name of the reviewer as shown on the platform. |
| `company_name` | string | Name of the company being reviewed. |
| `company_slug` | string | URL path for the company, e.g. `/araz-supermarket`. Leading slash included as scraped. |
| `company_url` | string | Full absolute URL to the company's profile page. |
| `rating` | integer | Star rating given by the reviewer. Range: 1–5. Derived by counting `img[src*='star_filled.svg']` elements in the review card. |
| `review_text` | string | Full text of the review as written by the reviewer. May be empty if the reviewer submitted only a star rating. |
| `review_url` | string | Direct permalink to the individual review, constructed as `{company_url}/{review_id}`. |
| `has_images` | boolean | `True` if the reviewer attached one or more photos to the review; `False` otherwise. |
| `page` | integer | Page number of the review feed from which this record was scraped (1–106). |

### Notes

- Reviews are ordered newest-first on the platform. Page 1 contains the most recent reviews; page 106 contains the oldest.
- `review_text` preserves the original Azerbaijani text including any Unicode characters.
- `company_slug` values in this file may be cross-referenced with the `slug` field in `companies.csv`.

---

## companies.csv

**Location:** `data/companies.csv`
**Records:** 139 companies
**Source:** 16 category listing pages + individual company profile pages

| Field | Type | Description |
|---|---|---|
| `slug` | string | Unique URL identifier for the company (no leading slash). Primary key for cross-referencing with `feedbacks.csv`. Example: `araz-supermarket`. |
| `name` | string | Display name of the company as shown on its category listing card. |
| `company_url` | string | Full absolute URL to the company's profile page on beledci.az. |
| `category_slug` | string | URL slug for the category the company belongs to, e.g. `supermarket`, `bank`, `taxi`. |
| `category_name` | string | Azerbaijani display name of the category, e.g. `Supermarketlər`, `Banklar`. |
| `category_label` | string | Full category label text as shown on the individual company profile page. May differ slightly from `category_name` (e.g. singular vs plural). |
| `rating_value` | float | Numeric average rating as displayed on the company profile page. Format: one decimal place (e.g. `1.4`). Empty string if the company has no reviews. |
| `rating_label` | string | Platform-assigned rating label in Azerbaijani. Known values: `Mükəmməl` (Excellent), `Yaxşı` (Good), `Orta` (Average), `Aşağı` (Low), `Yoxdur` (None). |
| `rating_stars` | integer | Number of filled stars shown on the category listing card. Range: 0–5. |
| `review_count` | integer | Total number of reviews listed on the category listing card. |
| `photo_url` | string | Absolute URL to the company's avatar/logo image hosted on beledci.az's S3 bucket. |

### Category Reference

The 16 categories and their slugs:

| `category_slug` | `category_name` |
|---|---|
| `restaurant` | Restoranlar |
| `tourism` | Turizm |
| `electronics-store` | Elektronika |
| `supermarket` | Supermarketlər |
| `services` | Xidmətlər |
| `bank` | Banklar |
| `apparel-store` | Geyim mağazaları |
| `carrier` | Mobil operatorlar |
| `internet-provider` | İnternet provayderlər |
| `taxi` | Taksi |
| `beauty` | Gözəllik və baxım |
| `clinics` | Tibb mərkəzləri |
| `education` | Tədris mərkəzləri |
| `hotel` | Otellər |
| `cargo` | Karqo |
| `entertainment` | Əyləncə |

### Notes

- `rating_value` is sourced from the company's own profile page (Step 2 of the scraper). It may differ slightly from what the category listing shows if the platform updates ratings between requests.
- Companies are sorted by `category_slug` then `name` in the output file.
- `review_count` from the category listing card is the source of truth used in analysis. It can differ from the actual count of matching rows in `feedbacks.csv` because `feedbacks.csv` only covers reviews that appeared in the platform's main feed during scraping.

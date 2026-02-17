"""
Business Intelligence Charts for beledci.az
Generates all charts into charts/ directory.

Usage:
    python scripts/generate_charts.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
CHARTS_DIR = ROOT / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

COMPANIES_CSV = ROOT / "data" / "companies.csv"
FEEDBACKS_CSV = ROOT / "data" / "feedbacks.csv"

# ── Style ──────────────────────────────────────────────────────────────────
BRAND_RED    = "#C0392B"
BRAND_ORANGE = "#E67E22"
BRAND_YELLOW = "#F1C40F"
BRAND_GREEN  = "#27AE60"
BRAND_BLUE   = "#2980B9"
BRAND_GRAY   = "#BDC3C7"
BRAND_DARK   = "#2C3E50"

PALETTE_5 = [BRAND_RED, BRAND_ORANGE, BRAND_YELLOW, BRAND_BLUE, BRAND_GREEN]

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.35,
    "grid.linestyle":   "--",
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.titlepad":    12,
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "figure.facecolor": "white",
    "axes.facecolor":   "#FAFAFA",
})

def save(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path.name}")


# ── Load data ──────────────────────────────────────────────────────────────
companies = pd.read_csv(COMPANIES_CSV)
feedbacks = pd.read_csv(FEEDBACKS_CSV)

# Merge feedbacks with companies to get category
fb = feedbacks.merge(
    companies[["name", "category_name", "category_slug"]],
    left_on="company_name", right_on="name", how="left",
)

print("Generating charts …\n")

# ═══════════════════════════════════════════════════════════════════════════
# Chart 1 — Overall 1-Star vs Rest breakdown (horizontal stacked bar, one row per category)
# ═══════════════════════════════════════════════════════════════════════════
def chart_01_category_sentiment():
    order = (
        fb.groupby("category_name")["rating"]
        .count()
        .sort_values(ascending=False)
        .index
    )
    order = [c for c in order if c in fb["category_name"].dropna().unique()]

    rows = []
    for cat in order:
        sub = fb[fb["category_name"] == cat]["rating"]
        if len(sub) == 0:
            continue
        rows.append({
            "category": cat,
            "1-Star"  : (sub == 1).mean() * 100,
            "2-Star"  : (sub == 2).mean() * 100,
            "3-Star"  : (sub == 3).mean() * 100,
            "4-Star"  : (sub == 4).mean() * 100,
            "5-Star"  : (sub == 5).mean() * 100,
            "total"   : len(sub),
        })

    df = pd.DataFrame(rows).set_index("category")
    stars = ["1-Star", "2-Star", "3-Star", "4-Star", "5-Star"]
    colors = [BRAND_RED, BRAND_ORANGE, BRAND_YELLOW, BRAND_BLUE, BRAND_GREEN]

    fig, ax = plt.subplots(figsize=(13, 7))
    left = np.zeros(len(df))
    for col, color in zip(stars, colors):
        ax.barh(df.index, df[col], left=left, color=color, label=col, height=0.65)
        left += df[col].values

    # Annotate total reviews
    for i, (cat, row) in enumerate(df.iterrows()):
        ax.text(102, i, f"n={int(row['total'])}", va="center", fontsize=8.5,
                color=BRAND_DARK)

    ax.set_xlim(0, 115)
    ax.set_xlabel("Share of Reviews (%)")
    ax.set_title("Customer Sentiment by Industry Category\n"
                 "How reviews are distributed across star ratings per sector")
    ax.legend(loc="lower right", ncol=5, framealpha=0.7, fontsize=9)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.invert_yaxis()
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "01_category_sentiment.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 2 — Top 15 Most Reviewed Companies (volume of feedback)
# ═══════════════════════════════════════════════════════════════════════════
def chart_02_top_complained():
    top = (
        fb.groupby("company_name")["rating"]
        .count()
        .sort_values(ascending=False)
        .head(15)
    )

    fig, ax = plt.subplots(figsize=(13, 6))
    bars = ax.barh(top.index[::-1], top.values[::-1], color=BRAND_RED, height=0.65)

    for bar, val in zip(bars, top.values[::-1]):
        ax.text(bar.get_width() + 4, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9, color=BRAND_DARK)

    ax.set_xlabel("Number of Customer Reviews")
    ax.set_title("Top 15 Most Reviewed Companies\n"
                 "High volume signals strong public attention — positive or negative")
    ax.set_xlim(0, top.max() * 1.15)
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "02_top_reviewed_companies.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 3 — 1-Star Rate for Top 15 Companies (crisis radar)
# ═══════════════════════════════════════════════════════════════════════════
def chart_03_one_star_rate():
    top15 = (
        fb.groupby("company_name")["rating"]
        .count()
        .sort_values(ascending=False)
        .head(15)
        .index
    )
    sub = fb[fb["company_name"].isin(top15)]
    rate = (
        sub.groupby("company_name")["rating"]
        .apply(lambda x: (x == 1).mean() * 100)
        .sort_values(ascending=True)
    )

    colors = [
        BRAND_RED if v >= 90 else (BRAND_ORANGE if v >= 80 else BRAND_YELLOW)
        for v in rate.values
    ]

    fig, ax = plt.subplots(figsize=(13, 6))
    bars = ax.barh(rate.index, rate.values, color=colors, height=0.65)

    for bar, val in zip(bars, rate.values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9, color=BRAND_DARK)

    ax.axvline(90, color=BRAND_RED, linestyle="--", linewidth=1.2,
               label="90% Danger threshold")
    ax.set_xlabel("1-Star Review Rate (%)")
    ax.set_title("1-Star Review Rate — Crisis Radar (Top 15 Companies)\n"
                 "Companies above 90% are in critical reputation risk territory")
    ax.set_xlim(0, 112)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(fontsize=9)
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "03_one_star_rate_top15.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 4 — Review Volume by Category (total reviews per sector)
# ═══════════════════════════════════════════════════════════════════════════
def chart_04_reviews_by_category():
    cat_vol = (
        companies.groupby("category_name")["review_count"]
        .sum()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    colors = [BRAND_RED if v >= 400 else BRAND_BLUE for v in cat_vol.values]
    bars = ax.barh(cat_vol.index, cat_vol.values, color=colors, height=0.65)

    for bar, val in zip(bars, cat_vol.values):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9, color=BRAND_DARK)

    ax.set_xlabel("Total Reviews Received")
    ax.set_title("Total Customer Feedback Volume by Industry Sector\n"
                 "Red = sectors with highest public scrutiny (400+ reviews)")
    ax.set_xlim(0, cat_vol.max() * 1.15)
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "04_review_volume_by_category.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 5 — Average Rating per Category (bar)
# ═══════════════════════════════════════════════════════════════════════════
def chart_05_avg_rating_by_category():
    cat_rated = companies[companies["rating_value"] > 0]
    avg = (
        cat_rated.groupby("category_name")["rating_value"]
        .mean()
        .sort_values(ascending=True)
    )

    colors = []
    for v in avg.values:
        if v >= 3:    colors.append(BRAND_GREEN)
        elif v >= 2:  colors.append(BRAND_YELLOW)
        else:         colors.append(BRAND_RED)

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(avg.index, avg.values, color=colors, height=0.65)

    for bar, val in zip(bars, avg.values):
        ax.text(bar.get_width() + 0.04, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=9, color=BRAND_DARK)

    ax.axvline(2.5, color=BRAND_GRAY, linestyle="--", linewidth=1.2,
               label="Midpoint (2.5)")
    ax.set_xlabel("Average Rating (out of 5.0)")
    ax.set_xlim(0, 5.5)
    ax.set_title("Average Company Rating by Industry Sector\n"
                 "Green = acceptable (3+) · Yellow = at risk (2–3) · Red = critical (<2)")
    ax.legend(fontsize=9)
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "05_avg_rating_by_category.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 6 — Rating Label Distribution across all companies
# ═══════════════════════════════════════════════════════════════════════════
def chart_06_rating_label_distribution():
    label_order = ["Əla", "Yaxşı", "Orta", "Aşağı", "Yoxdur"]
    label_colors = [BRAND_GREEN, BRAND_BLUE, BRAND_YELLOW, BRAND_ORANGE, BRAND_GRAY]
    counts = companies["rating_label"].value_counts().reindex(label_order, fill_value=0)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(counts.index, counts.values, color=label_colors, width=0.6,
                  edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                str(val), ha="center", va="bottom", fontsize=11, fontweight="bold",
                color=BRAND_DARK)

    ax.set_ylabel("Number of Companies")
    ax.set_title("Overall Reputation Health of All 139 Companies\n"
                 "Platform-wide distribution of official rating labels")
    ax.set_ylim(0, counts.max() * 1.15)
    ax.grid(axis="y")
    ax.grid(axis="x", alpha=0)

    save(fig, "06_rating_label_distribution.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 7 — Companies with Zero Reviews (engagement gap by sector)
# ═══════════════════════════════════════════════════════════════════════════
def chart_07_zero_review_gap():
    gap = companies.groupby("category_name").apply(
        lambda g: pd.Series({
            "with_reviews":   (g["review_count"] > 0).sum(),
            "without_reviews":(g["review_count"] == 0).sum(),
        })
    ).sort_values("without_reviews", ascending=True)

    gap = gap[gap.sum(axis=1) > 0]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(gap.index, gap["with_reviews"],    color=BRAND_BLUE,  label="Has Reviews",    height=0.55)
    ax.barh(gap.index, gap["without_reviews"], color=BRAND_GRAY,  label="No Reviews Yet", height=0.55,
            left=gap["with_reviews"])

    for i, (idx, row) in enumerate(gap.iterrows()):
        pct_no = row["without_reviews"] / (row["with_reviews"] + row["without_reviews"]) * 100
        if pct_no > 0:
            ax.text(row["with_reviews"] + row["without_reviews"] + 0.2, i,
                    f"{pct_no:.0f}% silent", va="center", fontsize=8.5, color=BRAND_GRAY)

    ax.set_xlabel("Number of Companies")
    ax.set_title("Customer Engagement Gap by Sector\n"
                 "Grey = companies on the platform but never reviewed")
    ax.legend(fontsize=9)
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "07_zero_review_gap.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 8 — Photo Evidence Rate by Star Rating
# ═══════════════════════════════════════════════════════════════════════════
def chart_08_photo_evidence():
    img_rate = feedbacks.groupby("rating")["has_images"].mean() * 100
    star_labels = ["1★", "2★", "3★", "4★", "5★"]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [BRAND_RED, BRAND_ORANGE, BRAND_YELLOW, BRAND_BLUE, BRAND_GREEN]
    bars = ax.bar(star_labels, img_rate.values, color=colors, width=0.55,
                  edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, img_rate.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=10,
                fontweight="bold", color=BRAND_DARK)

    ax.set_ylabel("% of Reviews with Photo Attachments")
    ax.set_ylim(0, img_rate.max() * 1.2)
    ax.set_title("Photo Evidence Attached by Star Rating\n"
                 "4-star reviewers attach photos most often — suggests genuine praise with proof")
    ax.grid(axis="y")
    ax.grid(axis="x", alpha=0)

    save(fig, "08_photo_evidence_by_rating.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 9 — Best-performing companies (avg rating, min 3 reviews)
# ═══════════════════════════════════════════════════════════════════════════
def chart_09_best_performers():
    agg = (
        fb.groupby("company_name")["rating"]
        .agg(count="count", avg="mean")
        .query("count >= 3")
        .sort_values("avg", ascending=True)
        .tail(15)
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    colors_bar = [BRAND_GREEN if v >= 3 else BRAND_YELLOW for v in agg["avg"].values]
    bars = ax.barh(agg.index, agg["avg"], color=colors_bar, height=0.65)

    for bar, (idx, row) in zip(bars, agg.iterrows()):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{row['avg']:.2f}  (n={int(row['count'])})",
                va="center", fontsize=9, color=BRAND_DARK)

    ax.axvline(2.5, color=BRAND_GRAY, linestyle="--", linewidth=1.2)
    ax.set_xlabel("Average Customer Rating (out of 5.0)")
    ax.set_xlim(0, 5.5)
    ax.set_title("Top 15 Best-Performing Companies\n"
                 "Minimum 3 reviews — Green = strong performer (3.0+)")
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "09_best_performing_companies.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 10 — Sector Crisis Matrix: Review Volume vs Average Rating
# ═══════════════════════════════════════════════════════════════════════════
def chart_10_crisis_matrix():
    cat_agg = (
        companies[companies["rating_value"] > 0]
        .groupby("category_name")
        .agg(
            avg_rating=("rating_value", "mean"),
            total_reviews=("review_count", "sum"),
            count=("slug", "count"),
        )
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 7))

    scatter = ax.scatter(
        cat_agg["total_reviews"],
        cat_agg["avg_rating"],
        s=cat_agg["count"] * 28,
        c=cat_agg["avg_rating"],
        cmap="RdYlGn",
        vmin=1, vmax=5,
        alpha=0.85,
        edgecolors="white",
        linewidth=1.5,
        zorder=3,
    )

    for _, row in cat_agg.iterrows():
        ax.annotate(
            row["category_name"],
            xy=(row["total_reviews"], row["avg_rating"]),
            xytext=(8, 0), textcoords="offset points",
            fontsize=8.5, color=BRAND_DARK,
        )

    ax.axhline(2.5, color=BRAND_GRAY, linestyle="--", linewidth=1, label="Rating midpoint")
    ax.axvline(300, color=BRAND_GRAY, linestyle=":",  linewidth=1, label="High-volume threshold")

    # Quadrant labels
    ax.text(320,  4.5, "High Scrutiny\nGood Reputation",  fontsize=8, color=BRAND_GREEN, alpha=0.7)
    ax.text(320,  1.2, "HIGH RISK\n(Volume + Bad Rating)", fontsize=8, color=BRAND_RED,   alpha=0.7,
            fontweight="bold")
    ax.text(10,   4.5, "Low Visibility\nGood Reputation",  fontsize=8, color=BRAND_BLUE,  alpha=0.7)
    ax.text(10,   1.2, "Emerging Risk\n(Bad + Low Volume)", fontsize=8, color=BRAND_ORANGE,alpha=0.7)

    plt.colorbar(scatter, ax=ax, label="Avg Rating", shrink=0.7)
    ax.set_xlabel("Total Reviews (Bubble size = number of companies in sector)")
    ax.set_ylabel("Average Rating (out of 5.0)")
    ax.set_ylim(0.5, 5.5)
    ax.set_title("Sector Risk Matrix: Volume of Feedback vs. Average Rating\n"
                 "Bottom-right = highest business risk for brands and regulators")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)

    save(fig, "10_sector_risk_matrix.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 11 — Review stream: page-by-page volume (proxy for time trend)
# ═══════════════════════════════════════════════════════════════════════════
def chart_11_review_stream():
    # page 1 = most recent, page 106 = oldest
    page_vol = feedbacks.groupby("page")["review_id"].count().reset_index()
    page_vol.columns = ["page", "reviews"]
    # Invert: page 106 = oldest (left), page 1 = newest (right)
    page_vol["period"] = page_vol["page"].max() - page_vol["page"] + 1

    # Rolling average
    page_vol = page_vol.sort_values("period")
    page_vol["rolling"] = page_vol["reviews"].rolling(5, center=True).mean()

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.fill_between(page_vol["period"], page_vol["reviews"],
                    alpha=0.25, color=BRAND_BLUE)
    ax.plot(page_vol["period"], page_vol["reviews"],
            color=BRAND_BLUE, linewidth=0.8, alpha=0.6, label="Reviews per page")
    ax.plot(page_vol["period"], page_vol["rolling"],
            color=BRAND_RED, linewidth=2.2, label="5-page rolling average")

    ax.set_xlabel("Chronological Order (oldest → newest)")
    ax.set_ylabel("Reviews per Page")
    ax.set_title("Review Activity Over Time\n"
                 "Each page represents a batch of chronologically ordered reviews")
    ax.legend(fontsize=9)
    ax.grid(axis="y")
    ax.grid(axis="x", alpha=0)

    save(fig, "11_review_stream.png")


# ═══════════════════════════════════════════════════════════════════════════
# Chart 12 — Most Reviewed Companies per Category (top 3 per sector)
# ═══════════════════════════════════════════════════════════════════════════
def chart_12_top_per_category():
    top3 = (
        companies[companies["review_count"] > 0]
        .sort_values("review_count", ascending=False)
        .groupby("category_name")
        .head(3)
        .copy()
    )
    top3["label"] = top3["name"] + "\n(" + top3["category_name"] + ")"
    top3 = top3.sort_values("review_count", ascending=True)

    # Color by category
    cats = top3["category_name"].unique().tolist()
    cmap = plt.cm.get_cmap("tab20", len(cats))
    cat_color = {c: cmap(i) for i, c in enumerate(cats)}
    colors = [cat_color[c] for c in top3["category_name"]]

    fig, ax = plt.subplots(figsize=(13, max(8, len(top3) * 0.38)))
    bars = ax.barh(top3["label"], top3["review_count"], color=colors, height=0.7)

    for bar, val in zip(bars, top3["review_count"]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=8.5, color=BRAND_DARK)

    ax.set_xlabel("Total Reviews")
    ax.set_title("Top 3 Most-Reviewed Companies per Industry Sector\n"
                 "Reveals which brands dominate public attention in each category")
    ax.set_xlim(0, top3["review_count"].max() * 1.13)
    ax.grid(axis="x")
    ax.grid(axis="y", alpha=0)

    save(fig, "12_top3_per_category.png")


# ── Run all ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chart_01_category_sentiment()
    chart_02_top_complained()
    chart_03_one_star_rate()
    chart_04_reviews_by_category()
    chart_05_avg_rating_by_category()
    chart_06_rating_label_distribution()
    chart_07_zero_review_gap()
    chart_08_photo_evidence()
    chart_09_best_performers()
    chart_10_crisis_matrix()
    chart_11_review_stream()
    chart_12_top_per_category()

    print(f"\n✓ All 12 charts saved to {CHARTS_DIR}/")

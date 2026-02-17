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
        .sort_values("total_reviews", ascending=False)
        .reset_index(drop=True)
    )

    VOL_THRESHOLD    = 200
    RATING_THRESHOLD = 1.5   # meaningful split: all data lives in 1.0–2.1

    # Categories with very few reviews (x < 30) — put in left column
    LEFT_COL = ["Otellər", "Tibb mərkəzləri", "Gözəllik və baxım",
                "Əyləncə", "Geyim mağazaları", "Tədris mərkəzləri"]
    left_order = (
        cat_agg[cat_agg["category_name"].isin(LEFT_COL)]
        .sort_values("avg_rating", ascending=False)["category_name"]
        .tolist()
    )

    fig, ax = plt.subplots(figsize=(18, 9))
    fig.patch.set_facecolor("white")

    xmax  = cat_agg["total_reviews"].max() * 1.22
    y_lo, y_hi = 0.85, 2.45   # tight zoom on actual data range

    y_frac = (RATING_THRESHOLD - y_lo) / (y_hi - y_lo)
    x_frac = VOL_THRESHOLD / xmax

    # ── Quadrant backgrounds ──────────────────────────────────────────────
    ax.axvspan(0,            VOL_THRESHOLD, ymin=y_frac, ymax=1,
               color="#EBF5FB", alpha=0.50, zorder=0)   # top-left   blue
    ax.axvspan(VOL_THRESHOLD, xmax,         ymin=y_frac, ymax=1,
               color="#EAFAF1", alpha=0.50, zorder=0)   # top-right  green
    ax.axvspan(0,            VOL_THRESHOLD, ymin=0,      ymax=y_frac,
               color="#FEF9E7", alpha=0.55, zorder=0)   # bot-left   yellow
    ax.axvspan(VOL_THRESHOLD, xmax,         ymin=0,      ymax=y_frac,
               color="#FDEDEC", alpha=0.65, zorder=0)   # bot-right  red

    # ── Dividers ──────────────────────────────────────────────────────────
    ax.axhline(RATING_THRESHOLD, color="#95A5A6", linestyle="--",
               linewidth=1.3, zorder=1)
    ax.axvline(VOL_THRESHOLD,    color="#95A5A6", linestyle=":",
               linewidth=1.3, zorder=1)

    # ── Quadrant labels ───────────────────────────────────────────────────
    # xlim = [-260, xmax].  Convert data coords to axes fractions correctly:
    #   axes_frac = (data_x - xlim_lo) / (xlim_hi - xlim_lo)
    xlim_lo = -260
    xlim_span = xmax - xlim_lo
    x0_frac  = (0              - xlim_lo) / xlim_span   # data x=0
    xv_frac  = (VOL_THRESHOLD  - xlim_lo) / xlim_span   # data x=VOL_THRESHOLD
    tl_x = x0_frac + 0.01     # just inside left data quadrant (0 → 200)
    tr_x = xv_frac + 0.015    # just inside right data quadrant (200 → xmax)

    q_bbox_tl = dict(boxstyle="round,pad=0.3", facecolor="#EBF5FB",
                     edgecolor="#AED6F1", linewidth=0.9, alpha=0.90)
    q_bbox_tr = dict(boxstyle="round,pad=0.3", facecolor="#EAFAF1",
                     edgecolor="#A9DFBF", linewidth=0.9, alpha=0.90)
    q_bbox_bl = dict(boxstyle="round,pad=0.3", facecolor="#FEF9E7",
                     edgecolor="#F9E79F", linewidth=0.9, alpha=0.90)
    q_bbox_br = dict(boxstyle="round,pad=0.3", facecolor="#FDEDEC",
                     edgecolor="#F1948A", linewidth=1.0, alpha=0.92)

    ax.text(tl_x, 0.99, "CONTAINED RISK\nLow Volume · Rating >1.5",
            color="#1A5276", fontweight="bold", fontsize=9, va="top",
            transform=ax.transAxes, alpha=0.85, bbox=q_bbox_tl)

    ax.text(tr_x, 0.99, "ELEVATED RISK\nHigh Volume · Rating >1.5",
            color="#1E8449", fontweight="bold", fontsize=9, va="top",
            transform=ax.transAxes, alpha=0.85, bbox=q_bbox_tr)

    ax.text(tl_x, 0.02, "SERIOUS RISK\nLow Volume · Rating <1.5",
            color="#784212", fontweight="bold", fontsize=9, va="bottom",
            transform=ax.transAxes, alpha=0.85, bbox=q_bbox_bl)

    ax.text(tr_x, 0.02, "⚠  CRITICAL ZONE\nHigh Volume · Rating <1.5",
            color=BRAND_RED, fontweight="bold", fontsize=9.5, va="bottom",
            transform=ax.transAxes, alpha=0.92, bbox=q_bbox_br)

    # ── Scatter ───────────────────────────────────────────────────────────
    norm = plt.Normalize(vmin=1.0, vmax=3.5)
    cmap = plt.cm.RdYlGn
    dot_colors = [cmap(norm(v)) for v in cat_agg["avg_rating"]]

    ax.scatter(
        cat_agg["total_reviews"],
        cat_agg["avg_rating"],
        s=210, c=dot_colors,
        edgecolors="white", linewidth=2.0,
        zorder=4,
    )

    # ── Labels: right-side cluster (not in LEFT_COL) ──────────────────────
    # Manually tuned offsets (dx pts, dy pts) for each non-left-col category
    RIGHT_OFFSETS = {
        "İnternet provayderlər": (  0,  22),
        "Taksi":                 (  0, -26),
        "Supermarketlər":        (  0,  22),
        "Xidmətlər":             (  0, -26),
        "Banklar":               (-10,  22),
        "Mobil operatorlar":     ( 10, -26),
        "Elektronika":           (  0,  22),
        "Restoranlar":           (  0,  22),
        "Turizm":                (  0, -26),
        "Karqo":                 (  0,  22),
    }
    label_bbox = dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#D5D8DC", linewidth=0.8, alpha=0.93)
    arrow_kw   = dict(arrowstyle="-", color="#AAAAAA", lw=0.9,
                      shrinkA=0, shrinkB=7)

    for _, row in cat_agg.iterrows():
        cat = row["category_name"]
        if cat in LEFT_COL:
            continue
        dx, dy = RIGHT_OFFSETS.get(cat, (0, 22))
        label = f"{cat}  ({int(row['total_reviews'])} rev · {row['avg_rating']:.1f}★)"
        ax.annotate(
            label,
            xy=(row["total_reviews"], row["avg_rating"]),
            xytext=(dx, dy), textcoords="offset points",
            fontsize=8.5, color=BRAND_DARK, fontweight="bold",
            ha="center", va="center",
            arrowprops=arrow_kw, bbox=label_bbox, zorder=5,
        )

    # ── Labels: left-column cluster (stacked, sorted by rating) ──────────
    # Place in a vertical column at x ≈ -200 (data coords), evenly spaced
    x_col = -200
    n_left = len(left_order)
    y_positions = np.linspace(y_hi - 0.08, y_lo + 0.08, n_left)

    for i, cat in enumerate(left_order):
        row = cat_agg[cat_agg["category_name"] == cat].iloc[0]
        label = f"{cat}  ({int(row['total_reviews'])} rev · {row['avg_rating']:.1f}★)"
        ax.annotate(
            label,
            xy=(row["total_reviews"], row["avg_rating"]),
            xytext=(x_col, y_positions[i]),
            textcoords="data",
            fontsize=8.5, color=BRAND_DARK, fontweight="bold",
            ha="right", va="center",
            arrowprops=dict(arrowstyle="-", color="#AAAAAA", lw=0.8,
                            shrinkA=0, shrinkB=7),
            bbox=label_bbox,
            zorder=5,
        )

    # ── Colour bar ────────────────────────────────────────────────────────
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.60, pad=0.01)
    cbar.set_label("Avg Rating", fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    # ── Legend for threshold lines ────────────────────────────────────────
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color="#95A5A6", linestyle="--", lw=1.3,
               label=f"Rating threshold ({RATING_THRESHOLD})"),
        Line2D([0], [0], color="#95A5A6", linestyle=":",  lw=1.3,
               label=f"Volume threshold ({VOL_THRESHOLD} reviews)"),
    ]
    ax.legend(handles=handles, fontsize=9, loc="lower right",
              framealpha=0.85, edgecolor="#D5D8DC")

    ax.set_xlabel("Total Reviews Received by Sector", fontsize=11)
    ax.set_ylabel("Average Company Rating (out of 5.0)", fontsize=11)
    ax.set_xlim(-260, xmax)
    ax.set_ylim(y_lo, y_hi)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.25))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.set_title(
        "Sector Risk Matrix — Volume of Customer Feedback vs. Average Rating\n"
        "Bottom-right = highest urgency for brand action and regulatory oversight",
        fontsize=13,
    )
    ax.grid(True, alpha=0.18, zorder=0)
    # Hide x-tick labels in negative territory
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: "" if v < 0 else f"{int(v)}")
    )

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

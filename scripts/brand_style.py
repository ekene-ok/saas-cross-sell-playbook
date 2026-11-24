"""Shared chart style for Ekene Okafor's portfolio.

One message per chart, stated in a sentence-case headline (regular weight, not bold or all caps),
a short deck underneath, one highlight colour with grey for context, direct labels instead of legends,
no gridlines, horizontal text only, bars from zero, and a source line.
Colours are validated with the dataviz palette checks (lightness band, chroma, contrast, CVD).
"""
import matplotlib
import matplotlib.pyplot as plt

INK = "#14213d"        # navy: headlines, values, key labels
MUTED = "#5f6470"      # deck, axis labels, source line (5.9:1 on white)
CONTEXT = "#c4c1ba"    # grey for everything that is not the message (always direct-labelled)
HAIRLINE = "#dedbd4"   # baselines and reference lines
SURFACE = "#ffffff"
BRAND_ACCENT = "#e0612e"  # signature orange

# One highlight colour per project, so each repo is recognisable; never mixed in one chart
PROJECT = {
    "city-expansion-scorecard": "#2a78d6",
    "campaign-uplift-targeting": "#e0612e",
    "saas-cross-sell-playbook": "#14946a",
    "business-review-agent": "#6250d6",
    "marketplace-supply-simulation": "#2f8a2f",
    "market-entry-investment-case": "#c94f86",
    "funnel-attribution-audit": "#b35900",
    "gtm-launch-playbook": "#d1495b",
    "crm-data-hygiene-audit": "#00819e",
}

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": HAIRLINE,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def figure(width=8.0, height=5.0):
    """Default 8 x 5 (a 5:8 height to width ratio)."""
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    return fig, ax


def clean(ax, keep="x"):
    """Remove chart junk. keep='x' keeps a bottom baseline (vertical bars, lines);
    keep='y' keeps a left baseline (horizontal bars); keep=None removes both."""
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)
    if keep == "x":
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(HAIRLINE)
    if keep == "y":
        ax.spines["left"].set_visible(True)
        ax.spines["left"].set_color(HAIRLINE)
    ax.grid(False)
    ax.tick_params(length=0, labelsize=10.5, colors=MUTED)
    return ax


def headline(fig, title, deck=None):
    """Takeaway headline in sentence case, regular weight, with an optional deck."""
    fig.text(0.03, 0.965, title, fontsize=15, color=INK, ha="left", va="top")
    if deck:
        fig.text(0.03, 0.905, deck, fontsize=10.5, color=MUTED, ha="left", va="top")


def source(fig, text):
    fig.text(0.03, 0.02, f"Source: {text}", fontsize=8.5, color=MUTED, ha="left", va="bottom")


def finish(fig, path, top=0.84, bottom=0.12, left=0.08, right=0.97):
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


STREAMLIT_THEME = """[theme]
base = "light"
primaryColor = "{accent}"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f7f6f2"
textColor = "#14213d"
font = "sans serif"
"""

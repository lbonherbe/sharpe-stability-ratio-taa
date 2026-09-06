"""Shared chart styling: dark ground, rotating accent palettes, a sequential ramp."""

BG, INK, MUTED, GRID = "#08111f", "#f8fafc", "#94a3b8", "#1b2940"

PALETTES = {
    # name:        (primary,   secondary,  tertiary)
    "cyan_gold":   ("#0891b2", "#a16207", "#64748b"),   # the original house pair
    "violet_amber":("#7c5cd6", "#d99a2b", "#6b7280"),
    "emerald_rose":("#0f9d78", "#c2557a", "#6b7280"),
    "sky_orange":  ("#3b82c4", "#d97316", "#64748b"),
    "teal_magenta":("#14957f", "#b4519c", "#6b7280"),
}

# Sequential ramp for encoding a magnitude (e.g. drawdown depth) as colour,
# shallow -> deep. Using colour to carry a real number beats using it to decorate.
RAMP = ["#14957f", "#4f9e74", "#9ba63f", "#d99a2b", "#c2557a"]


def apply(plt, palette="cyan_gold"):
    """Set rcParams for the house dark style and return the accent triple."""
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": MUTED, "xtick.color": MUTED,
        "ytick.color": MUTED, "axes.edgecolor": GRID, "grid.color": GRID,
        "font.size": 10, "axes.titlesize": 13,
    })
    return PALETTES[palette]


def ramp_color(value, lo, hi):
    """Map value in [lo, hi] onto RAMP. Used for drawdown depth."""
    if hi == lo:
        return RAMP[0]
    t = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    return RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))]


def style(ax, grid_axis="both"):
    ax.grid(True, axis=grid_axis, alpha=.3, lw=.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

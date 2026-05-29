"""
DUNE plot styling utilities.

Usage in any notebook:
    import sys; sys.path.insert(0, "<repo_root>/utils")
    from dune_plot import apply_dune_style, dune_label

    apply_dune_style()          # call once at the top
    # ... make your figure ...
    dune_label(ax)              # add the DUNE WIP label to an axes
"""

import os
import matplotlib.pyplot as plt

_STYLE_FILE = os.path.join(os.path.dirname(__file__), "dune.mplstyle")
_LABEL_TEXT = "DUNE ND-LAr 2x2 Demonstrator, Work in Progress"


def apply_dune_style():
    """Apply the DUNE matplotlib style globally."""
    plt.style.use(_STYLE_FILE)


def dune_label(ax=None, loc="upper left", fontsize=12, fontstyle="italic"):
    """Add the standard DUNE WIP label to an axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        Axes to label. Defaults to current axes.
    loc : str
        "upper left", "upper right", "lower left", or "lower right".
    fontsize : int
        Font size for the label.
    fontstyle : str
        Font style (e.g. "italic", "normal").
    """
    if ax is None:
        ax = plt.gca()

    coords = {
        "upper left":  (0.03, 0.97, "left",  "top"),
        "upper right": (0.97, 0.97, "right", "top"),
        "lower left":  (0.03, 0.03, "left",  "bottom"),
        "lower right": (0.97, 0.03, "right", "bottom"),
    }
    x, y, ha, va = coords.get(loc, coords["upper left"])
    ax.text(x, y, _LABEL_TEXT, transform=ax.transAxes,
            fontsize=fontsize, fontstyle=fontstyle,
            ha=ha, va=va, color="black")

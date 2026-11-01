from io import BytesIO

from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from numpy import ndarray

CLASS_NAMES = {1: "Вода", 2: "Застройка / Открытый грунт", 3: "Растительность", 4: "Прочее"}
CLASS_COLORS = {0: "black",
                1: "RoyalBlue",
                2: "DarkRed",
                3: "LimeGreen",
                4: "Gold"}

def make_class_preview(array: ndarray, title: str="Классификация") -> BytesIO:
    h, w = array.shape
    scale = 1200 / max(h, w)
    fig = Figure(figsize=(w * scale / 100, h * scale / 100), dpi=100)

    cmap = ListedColormap([CLASS_COLORS[i] for i in range(len(CLASS_COLORS))])
    cmap.set_bad("black")

    ax = fig.add_subplot()
    ax.axis('off')
    ax.set_title(title)

    ax.imshow(array, cmap=cmap, vmin=-0.5, vmax=4.5, aspect="equal", interpolation="nearest")
    ax.legend(
        handles=[Patch(color=CLASS_COLORS[i], label=CLASS_NAMES[i]) for i in CLASS_NAMES],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=4,
        frameon=False
    )

    buf = BytesIO()
    fig.savefig(buf, format="JPEG", bbox_inches="tight", pad_inches=0.2)
    buf.seek(0)

    return buf

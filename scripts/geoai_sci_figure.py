
"""
geoai_sci_figure.py - SCI Paper Figure Factory
Generates publication-ready SCI figures: study area, land cover,
accuracy assessment, change detection, spatial pattern, driver analysis,
uncertainty, framework, graphical abstract, TOC figure.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.patheffects import withStroke
from matplotlib.colors import ListedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings
warnings.filterwarnings("ignore")

LC_COLORS = {
    "Cropland": "#FFFF64", "Forest": "#006400", "Grassland": "#00A000",
    "Shrubland": "#A6CE39", "Wetland": "#966400", "Water": "#0064FF",
    "Built-up": "#FF0000", "Bareland": "#E6E6A0", "Ice_Snow": "#E6FFFF",
}

NATURE_COLORS = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
                 "#0072B2", "#D55E00", "#CC79A7", "#999999"]
ELSEVIER_COLORS = ["#4477AA", "#CC6677", "#DDCC77", "#117733",
                   "#AA4499", "#88CCEE", "#332288", "#44AA99"]
MDPI_COLORS = ["#006633", "#FF6600", "#0066CC", "#CC0033",
               "#660066", "#FFCC00", "#339933", "#993300"]

JOURNAL_CONFIGS = {
    "Nature": {"full_width": 18.3, "dpi": 300, "font": "Arial", "font_size": 7, "legend_size": 6, "colors": NATURE_COLORS},
    "Science": {"full_width": 17.8, "dpi": 300, "font": "Arial", "font_size": 7, "legend_size": 6, "colors": NATURE_COLORS},
    "Remote_Sensing": {"full_width": 17.2, "dpi": 300, "font": "Arial", "font_size": 8, "legend_size": 7, "colors": MDPI_COLORS},
    "ISPRS_JPRS": {"full_width": 19.0, "dpi": 300, "font": "Arial", "font_size": 8, "legend_size": 7, "colors": ELSEVIER_COLORS},
    "IJAEOG": {"full_width": 18.0, "dpi": 300, "font": "Arial", "font_size": 8, "legend_size": 7, "colors": ELSEVIER_COLORS},
    "Ecological_Indicators": {"full_width": 21.0, "dpi": 300, "font": "Arial", "font_size": 8, "legend_size": 7, "colors": ELSEVIER_COLORS},
    "RSE": {"full_width": 21.0, "dpi": 300, "font": "Arial", "font_size": 8, "legend_size": 7, "colors": ELSEVIER_COLORS},
}

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica"]

class SCIFigures:
    def __init__(self, journal="Remote_Sensing", output_dir="figures"):
        self.journal = journal
        self.config = JOURNAL_CONFIGS.get(journal, JOURNAL_CONFIGS["Remote_Sensing"])
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        plt.rcParams.update({"font.size": self.config["font_size"], "axes.labelsize": self.config["font_size"],
                             "axes.titlesize": self.config["font_size"]+1, "legend.fontsize": self.config["legend_size"],
                             "figure.dpi": self.config["dpi"], "savefig.dpi": self.config["dpi"]})

    def _save(self, fig, name):
        path = os.path.join(self.output_dir, name)
        fig.savefig(path, dpi=self.config["dpi"], bbox_inches="tight", pad_inches=0.3, facecolor="white")
        plt.close(fig)
        return path

    def figure1_study_area(self, satellite_img, boundary_gdf, inset_map=None, title=None):
        fig = plt.figure(figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.7))
        gs = GridSpec(3, 3, figure=fig, width_ratios=[1,200,1], height_ratios=[1,3,1], wspace=0.05, hspace=0.05)
        ax = fig.add_subplot(gs[1,1])
        if satellite_img is not None: ax.imshow(satellite_img, cmap="gray")
        if boundary_gdf is not None: boundary_gdf.boundary.plot(ax=ax, color="red", linewidth=0.8)
        ax.set_title(title or "Study Area", fontweight="bold")
        ax.axis("off")
        ax.annotate("N", xy=(0.92,0.85), xytext=(0.92,0.79), ha="center", va="center",
                    fontsize=self.config["font_size"]+2, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color="black", lw=1.5), transform=ax.transAxes)
        if inset_map is not None:
            ax_inset = fig.add_subplot(gs[0,0]); ax_inset.imshow(inset_map)
            ax_inset.set_title("(a)", fontsize=6); ax_inset.axis("off")
        fig.text(0.5, 0.02, "Data source: [Specify] | CRS: EPSG:4326", ha="center", fontsize=5, style="italic")
        return self._save(fig, "Figure1_Study_Area.png")

    def figure2_land_cover(self, lc_maps, time_labels, class_names=None):
        n = len(lc_maps)
        fig = plt.figure(figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.5))
        gs = GridSpec(1, n, figure=fig, wspace=0.02)
        colors = list(LC_COLORS.values())[:len(np.unique(lc_maps[0][lc_maps[0]>=0]))]
        cmap = ListedColormap(colors)
        for i, (m, lbl) in enumerate(zip(lc_maps, time_labels)):
            ax = fig.add_subplot(gs[0,i]); ax.imshow(m, cmap=cmap, interpolation="nearest")
            ax.set_title(lbl, fontweight="bold", fontsize=8); ax.axis("off")
        if class_names:
            lax = fig.add_axes([0.1,0.02,0.8,0.03]); lax.axis("off")
            patches = [mpatches.Patch(facecolor=colors[i], label=class_names[i]) for i in range(len(class_names))]
            lax.legend(handles=patches, loc="center", ncol=min(len(class_names),6), fontsize=5, frameon=False)
        return self._save(fig, "Figure2_Land_Cover.png")

    def figure3_accuracy(self, confusion_matrix, class_names, metrics=None):
        fig = plt.figure(figsize=(self.config["full_width"]*0.03937*0.8, self.config["full_width"]*0.03937*0.6))
        gs = GridSpec(1, 2, figure=fig, width_ratios=[1.2,1], wspace=0.3)
        ax1 = fig.add_subplot(gs[0])
        cm = np.array(confusion_matrix); n = len(class_names)
        im = ax1.imshow(cm, cmap="YlOrRd", interpolation="nearest")
        for i in range(n):
            for j in range(n):
                ax1.text(j, i, cm[i,j], ha="center", va="center",
                        color="white" if cm[i,j] > cm.max()/2 else "black", fontsize=6)
        ax1.set_xticks(range(n)); ax1.set_yticks(range(n))
        ax1.set_xticklabels(class_names, rotation=45, ha="right", fontsize=5)
        ax1.set_yticklabels(class_names, fontsize=5)
        ax1.set_xlabel("Predicted", fontsize=7); ax1.set_ylabel("Actual", fontsize=7)
        ax1.set_title("Confusion Matrix", fontweight="bold", fontsize=8)
        plt.colorbar(im, ax=ax1, fraction=0.05, pad=0.05)
        if metrics:
            ax2 = fig.add_subplot(gs[1])
            ax2.barh(list(metrics.keys()), list(metrics.values()), color=NATURE_COLORS[:len(metrics)])
            ax2.set_xlim(0,1); ax2.set_xlabel("Score")
            ax2.set_title("Accuracy Metrics", fontweight="bold", fontsize=8)
        return self._save(fig, "Figure3_Accuracy_Assessment.png")

    def figure4_change_detection(self, change_map, transition_matrix, class_names=None, period="2010-2020"):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.45),
                                        gridspec_kw={"width_ratios":[1.2,1]})
        ax1.imshow(change_map, cmap=ListedColormap(["#CCCCCC","#FF6B6B","#4ECDC4"]), interpolation="nearest")
        ax1.set_title(f"Change Map ({period})", fontweight="bold"); ax1.axis("off")
        tm = np.array(transition_matrix)
        im2 = ax2.imshow(tm, cmap="Blues", interpolation="nearest")
        for i in range(tm.shape[0]):
            for j in range(tm.shape[1]):
                ax2.text(j, i, tm[i,j], ha="center", va="center",
                        color="white" if tm[i,j] > tm.max()/2 else "black", fontsize=5)
        if class_names:
            ax2.set_xticks(range(len(class_names))); ax2.set_yticks(range(len(class_names)))
            ax2.set_xticklabels(class_names, rotation=45, ha="right", fontsize=5)
            ax2.set_yticklabels(class_names, fontsize=5)
        ax2.set_xlabel("To", fontsize=7); ax2.set_ylabel("From", fontsize=7)
        ax2.set_title("Transition Matrix", fontweight="bold", fontsize=8)
        return self._save(fig, "Figure4_Change_Detection.png")

    def figure5_spatial_pattern(self, hotspot_map, lisa_map, moran_scatter=None):
        fig = plt.figure(figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.4))
        gs = GridSpec(1, 3, figure=fig, wspace=0.3)
        ax1 = fig.add_subplot(gs[0])
        ax1.imshow(hotspot_map, cmap=ListedColormap(["#053061","#2166AC","#92C5DE","#F7F7F7","#F4A582","#D6604D","#B2182B"]),
                  interpolation="nearest", vmin=-3, vmax=3)
        ax1.set_title("Hotspot (Gi*)", fontweight="bold"); ax1.axis("off")
        ax2 = fig.add_subplot(gs[1])
        ax2.imshow(lisa_map, cmap=ListedColormap(["#F7F7F7","#FF0000","#0000FF","#FF69B4","#87CEEB"]), interpolation="nearest")
        ax2.set_title("LISA Cluster", fontweight="bold"); ax2.axis("off")
        if moran_scatter:
            ax3 = fig.add_subplot(gs[2])
            ax3.scatter(moran_scatter["values"], moran_scatter["spatial_lag"], alpha=0.5, s=10, c="#4477AA")
            ax3.set_xlabel("Value"); ax3.set_ylabel("Spatial Lag"); ax3.set_title("Moran Scatter", fontweight="bold")
        return self._save(fig, "Figure5_Spatial_Pattern.png")

    def figure6_driver_analysis(self, feature_importance, feature_names=None):
        fig, ax = plt.subplots(figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.4))
        imp = np.array(feature_importance); names = feature_names or [f"F{i+1}" for i in range(len(imp))]
        idx = np.argsort(imp)
        ax.barh(range(len(idx)), imp[idx], color=NATURE_COLORS[:len(idx)])
        ax.set_yticks(range(len(idx))); ax.set_yticklabels([names[i] for i in idx], fontsize=6)
        ax.set_xlabel("Importance"); ax.set_title("Variable Importance", fontweight="bold")
        return self._save(fig, "Figure6_Driver_Analysis.png")

    def figure7_uncertainty(self, uncertainty_map):
        fig, ax = plt.subplots(figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.35))
        im = ax.imshow(uncertainty_map, cmap="RdYlGn_r", interpolation="bilinear")
        ax.set_title("Uncertainty", fontweight="bold"); ax.axis("off")
        plt.colorbar(im, ax=ax, fraction=0.05, pad=0.02, label="Std Dev")
        return self._save(fig, "Figure7_Uncertainty_Analysis.png")

    def figure8_framework(self, steps):
        from matplotlib.patches import FancyBboxPatch
        fig, ax = plt.subplots(figsize=(self.config["full_width"]*0.03937, self.config["full_width"]*0.03937*0.45))
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
        n = len(steps); pos = [i/max(n-1,1) for i in range(n)]
        for i, (p, s) in enumerate(zip(pos, steps)):
            box = FancyBboxPatch((p-0.08, 0.35), 0.16, 0.3, boxstyle="round,pad=0.02",
                                facecolor=NATURE_COLORS[i%len(NATURE_COLORS)], edgecolor="black", alpha=0.9)
            ax.add_patch(box); ax.text(p, 0.5, s, ha="center", va="center", fontsize=6, fontweight="bold")
            if i < n-1:
                ax.annotate("", xy=(pos[i+1]-0.08, 0.5), xytext=(p+0.08, 0.5),
                           arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))
        ax.set_title("Framework", fontweight="bold", fontsize=10, pad=20)
        return self._save(fig, "Figure8_Framework.png")

    def graphical_abstract(self, workflow_icons, result_img, width=1296, height=765):
        dpi = 200
        fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
        gs = GridSpec(1, 3, figure=fig, width_ratios=[1,0.1,1.2], wspace=0.05)
        ax1 = fig.add_subplot(gs[0]); ax1.axis("off")
        for i, icon in enumerate(workflow_icons):
            y = 0.8 - i*0.2
            ax1.text(0.5, y, icon, ha="center", va="center", fontsize=14, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.5", facecolor=NATURE_COLORS[i%len(NATURE_COLORS)], alpha=0.7))
            if i < len(workflow_icons)-1:
                ax1.annotate("", xy=(0.5,y-0.15), xytext=(0.5,y+0.02),
                           arrowprops=dict(arrowstyle="->", color="gray", lw=2), transform=ax1.transAxes)
        ax1.set_title("Workflow", fontsize=9, fontweight="bold")
        ax2 = fig.add_subplot(gs[2]); ax2.imshow(result_img); ax2.axis("off")
        ax2.set_title("Key Results", fontsize=9, fontweight="bold")
        return self._save(fig, "Graphical_Abstract.png")


    def compose_figure_grid(self, image_paths, layout="2x2", labels=None, output="Composed.png"):
        """Compose multiple images into a grid."""
        import matplotlib.image as mpimg
        layouts = {"2x2": (2,2), "1x2": (1,2), "2x1": (2,1), "3x1": (3,1),
                   "1x3": (1,3), "3x2": (3,2), "2x3": (2,3)}
        rows, cols = layouts.get(layout, (2,2))
        fig, axes = plt.subplots(rows, cols, figsize=(self.config["full_width"]*0.03937,
                                                       self.config["full_width"]*0.03937*0.6))
        axes = axes.flatten() if rows*cols > 1 else [axes]
        for i, (img, ax) in enumerate(zip(image_paths, axes)):
            ax.imshow(mpimg.imread(img))
            ax.axis("off")
            if labels and i < len(labels):
                ax.text(0.02, 0.98, labels[i], transform=ax.transAxes,
                       fontsize=10, fontweight="bold", va="top",
                       path_effects=[withStroke(linewidth=3, foreground="white")])
        for ax in axes[len(image_paths):]: ax.axis("off")
        return self._save(fig, output)

if __name__ == "__main__":
    sf = SCIFigures(journal="Remote_Sensing")
    print(f"SCI Figure Factory Ready: {sf.journal}, Output: {sf.output_dir}")

"""GeoPilot - Main QGIS Plugin Class."""

import os
import sys

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PLUGIN_DIR, "scripts")


class GeoPilotPlugin:
    """Main plugin class for GeoPilot."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = PLUGIN_DIR
        self.actions = []
        self.menu = "GeoPilot"
        self.toolbar = None
        self.dialog = None

        # Add scripts to sys.path (idempotent)
        if SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, SCRIPTS_DIR)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = QgsApplication.iconPath("mIconRaster.svg")

        # Use an existing toolbar or create one, but own the reference so we
        # can remove it cleanly on unload.
        self.toolbar = self.iface.addToolBar("GeoPilot")
        self.toolbar.setObjectName("GeoPilotToolbar")

        action = QAction(QIcon(icon_path), "GeoPilot Chat", self.iface.mainWindow())
        action.triggered.connect(self.show_dialog)
        self.iface.addPluginToMenu(self.menu, action)
        self.toolbar.addAction(action)
        self.actions.append(action)

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if self.dialog:
            try:
                self.dialog.close()
            except Exception:
                pass
            self.dialog = None
        if self.toolbar:
            try:
                self.toolbar.deleteLater()
            except Exception:
                pass
            self.toolbar = None
        # Best-effort: remove our SCRIPTS_DIR from sys.path
        try:
            while SCRIPTS_DIR in sys.path:
                sys.path.remove(SCRIPTS_DIR)
        except Exception:
            pass

    def show_dialog(self):
        """Open the GeoPilot chat dialog."""
        if self.dialog is None:
            from .geopilot_dialog import GeoPilotDialog

            self.dialog = GeoPilotDialog(self.iface, self.plugin_dir)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

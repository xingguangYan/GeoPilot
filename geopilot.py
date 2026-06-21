"""GeoPilot - Main QGIS Plugin Class"""

import os
import sys

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PLUGIN_DIR, "scripts")


class GeoPilotPlugin:
    """Main plugin class for GeoPilot."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = PLUGIN_DIR
        self.actions = []
        self.menu = "GeoPilot"
        self.toolbar = self.iface.addToolBar("GeoPilot")
        self.toolbar.setObjectName("GeoPilotToolbar")
        self.dialog = None
        self.translator = None

        # Add scripts to path
        if SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, SCRIPTS_DIR)

    def initGui(self):
        """Initialize the plugin GUI."""
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = QgsApplication.iconPath("mIconRaster.svg")

        action = QAction(QIcon(icon_path), "GeoPilot Chat", self.iface.mainWindow())
        action.triggered.connect(self.show_dialog)
        self.iface.addPluginToMenu(self.menu, action)
        self.toolbar.addAction(action)
        self.actions.append(action)

    def unload(self):
        """Unload the plugin."""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if self.dialog:
            self.dialog.close()

    def show_dialog(self):
        """Open the GeoPilot chat dialog."""
        if not self.dialog:
            from .geopilot_dialog import GeoPilotDialog

            self.dialog = GeoPilotDialog(self.iface, self.plugin_dir)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

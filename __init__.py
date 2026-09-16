"""GeoPilot - AI-powered Geospatial Analysis Assistant for QGIS."""

__version__ = "1.3.8"


def classFactory(iface):
    from .geopilot import GeoPilotPlugin

    return GeoPilotPlugin(iface)

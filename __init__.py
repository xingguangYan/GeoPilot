"""
GeoPilot - AI-powered Geospatial Analysis Assistant for QGIS
"""


def classFactory(iface):
    from .geopilot import GeoPilotPlugin

    return GeoPilotPlugin(iface)

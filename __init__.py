"""
GeoPilot - AI-powered Geospatial Analysis Assistant for QGIS
"""
import os, sys

def classFactory(iface):
    from .geopilot import GeoPilotPlugin
    return GeoPilotPlugin(iface)

"""geoai_gee_bridge.py - Google Earth Engine Integration"""
"""Lazy-loads ee/geemap to avoid import errors."""

def init_ee(project=None):
    import ee
    try:
        ee.Initialize(project=project)
        print("Earth Engine initialized")
        return True
    except Exception as e:
        print("EE init failed: " + str(e))
        print("Run: earthengine authenticate")
        return False

def get_s2_collection(roi, start_date, end_date, cloud_pct=20):
    """Get Sentinel-2 SR collection."""
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct)))

def get_l8_collection(roi, start_date, end_date, cloud_pct=20):
    """Get Landsat 8 SR collection."""
    return (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_pct)))

def gee_to_geopandas(ee_feature_collection):
    import geemap
    """Convert EE FeatureCollection to GeoDataFrame."""
    import geemap
    return geemap.ee_to_geopandas(ee_feature_collection)

def export_to_drive(image, description, folder, region, scale=30):
    """Export Earth Engine image to Google Drive."""
    task = ee.batch.Export.image.toDrive(
        image=image, description=description,
        folder=folder, region=region, scale=scale,
        maxPixels=1e13, fileFormat="GeoTIFF"
    )
    task.start()
    return task

if __name__ == "__main__":
    init_ee()

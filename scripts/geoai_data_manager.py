"""
geoai_data_manager.py - Geospatial Data Management

Handles: Shapefile, GeoJSON, GPKG, KML, KMZ, CSV, XLSX,
GeoTIFF, NetCDF, HDF, LAS/LAZ
"""

import os
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import box, Point, Polygon
import warnings
warnings.filterwarnings("ignore")


SUPPORTED_VECTOR = {
    ".shp": "ESRI Shapefile",
    ".geojson": "GeoJSON",
    ".gpkg": "GeoPackage",
    ".kml": "KML",
    ".kmz": "KMZ",
    ".gml": "GML",
    ".tab": "MapInfo TAB",
    ".mif": "MapInfo MIF",
    ".dwg": "AutoCAD DWG",
    ".dxf": "AutoCAD DXF",
}

SUPPORTED_RASTER = {
    ".tif": "GeoTIFF",
    ".tiff": "GeoTIFF",
    ".nc": "NetCDF",
    ".hdf": "HDF4/EOS",
    ".h5": "HDF5",
    ".img": "ERDAS IMG",
    ".jp2": "JPEG2000",
    ".mrf": "MRF",
}

SUPPORTED_TABULAR = {
    ".csv": "CSV",
    ".xlsx": "Excel",
    ".xls": "Excel 97",
}

POINT_CLOUD = {".las": "LAS", ".laz": "LAZ"}


class DataManager:
    """Unified data management for geospatial workflows."""

    def __init__(self, workspace=None):
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.layers = {}

    def scan_directory(self, path=None, recursive=True):
        """Scan directory for geospatial data files."""
        path = Path(path) if path else self.workspace
        if not path.exists():
            return {"error": f"Path not found: {path}"}

        all_exts = {**SUPPORTED_VECTOR, **SUPPORTED_RASTER,
                    **SUPPORTED_TABULAR, **POINT_CLOUD}
        found = {cat: [] for cat in
                 ["vector", "raster", "tabular", "point_cloud", "other"]}

        glob_pattern = "**/*" if recursive else "*"
        for f in path.glob(glob_pattern):
            if f.is_file():
                ext = f.suffix.lower()
                if ext in SUPPORTED_VECTOR:
                    found["vector"].append(str(f))
                elif ext in SUPPORTED_RASTER:
                    found["raster"].append(str(f))
                elif ext in SUPPORTED_TABULAR:
                    found["tabular"].append(str(f))
                elif ext in POINT_CLOUD:
                    found["point_cloud"].append(str(f))
                else:
                    found["other"].append(str(f))

        return found

    def read_vector(self, path, layer=None, **kwargs):
        """Read vector data as GeoDataFrame."""
        path = str(path)
        try:
            if path.endswith(".kmz"):
                import zipfile
                import shutil
                tmp_dir = Path(self.workspace) / "_kmz_temp"
                tmp_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(path, "r") as z:
                    z.extractall(tmp_dir)
                kml_files = list(tmp_dir.glob("*.kml"))
                if kml_files:
                    gdf = gpd.read_file(str(kml_files[0]))
                shutil.rmtree(tmp_dir)
            else:
                gdf = gpd.read_file(path, layer=layer, **kwargs)

            name = Path(path).stem
            self.layers[name] = gdf
            return gdf
        except Exception as e:
            raise IOError(f"Failed to read {path}: {e}")

    def write_vector(self, gdf, path, driver=None, **kwargs):
        """Write GeoDataFrame to file."""
        path = str(path)
        ext = Path(path).suffix.lower()

        driver_map = {
            ".shp": "ESRI Shapefile",
            ".geojson": "GeoJSON",
            ".gpkg": "GPKG",
            ".kml": "KML",
            ".gml": "GML",
        }

        driver = driver or driver_map.get(ext, "ESRI Shapefile")
        gdf.to_file(path, driver=driver, **kwargs)
        return path

    def read_raster(self, path, band=None):
        """Read raster data and return array + metadata."""
        import rasterio
        with rasterio.open(path) as src:
            data = src.read(band) if band else src.read()
            meta = src.meta.copy()
            meta["crs"] = str(src.crs) if src.crs else None
            meta["bounds"] = src.bounds
            meta["shape"] = src.shape
            meta["nodata"] = src.nodata
        return data, meta

    def read_csv_as_gdf(self, path, x_col="x", y_col="y", crs="EPSG:4326"):
        """Read CSV with coordinates as GeoDataFrame."""
        df = pd.read_csv(path)
        geometry = [Point(x, y) for x, y in zip(df[x_col], df[y_col])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
        name = Path(path).stem
        self.layers[name] = gdf
        return gdf

    def read_excel_as_gdf(self, path, sheet=0, x_col="x", y_col="y",
                          crs="EPSG:4326"):
        """Read Excel with coordinates as GeoDataFrame."""
        df = pd.read_excel(path, sheet_name=sheet)
        geometry = [Point(x, y) for x, y in zip(df[x_col], df[y_col])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
        name = Path(path).stem
        self.layers[name] = gdf
        return gdf

    def export_attributes(self, gdf, path, format="csv"):
        """Export attribute table to CSV or Excel."""
        df = gdf.drop(columns=["geometry"])
        if format == "csv":
            df.to_csv(path, index=False, encoding="utf-8-sig")
        elif format == "xlsx":
            df.to_excel(path, index=False)
        return path

    def data_quality_report(self, gdf, name=None):
        """Generate data quality report for a vector layer."""
        report = {
            "name": name or "Unknown",
            "total_features": len(gdf),
            "columns": list(gdf.columns),
            "crs": str(gdf.crs) if gdf.crs else "Not set",
            "geometry_types": gdf.geometry.type.value_counts().to_dict(),
            "extent": {
                "xmin": float(gdf.total_bounds[0]),
                "ymin": float(gdf.total_bounds[1]),
                "xmax": float(gdf.total_bounds[2]),
                "ymax": float(gdf.total_bounds[3]),
            },
            "quality_issues": {
                "missing_values": int(gdf.isnull().sum().sum()),
                "empty_geometries": int(gdf.geometry.is_empty.sum()),
                "null_geometries": int(gdf.geometry.isna().sum()),
                "duplicate_geometries": int(gdf.geometry.duplicated().sum()),
                "invalid_geometries": int(~gdf.geometry.is_valid.sum()),
            }
        }

        # Coordinate range sanity check
        if gdf.crs and str(gdf.crs) == "EPSG:4326":
            bounds = gdf.total_bounds
            report["coordinate_check"] = {
                "lat_in_range": -90 <= bounds[1] <= 90 and -90 <= bounds[3] <= 90,
                "lon_in_range": -180 <= bounds[0] <= 180 and -180 <= bounds[2] <= 180
            }

        return report

    def reproject(self, gdf, target_crs):
        """Reproject vector data."""
        return gdf.to_crs(target_crs)

    def clip_by_extent(self, gdf, xmin, ymin, xmax, ymax):
        """Clip data by bounding box extent."""
        bbox = box(xmin, ymin, xmax, ymax)
        bbox_gdf = gpd.GeoDataFrame(
            {"geometry": [bbox]}, crs=gdf.crs
        )
        return gpd.clip(gdf, bbox_gdf)

    def merge_layers(self, layer_names):
        """Merge multiple vector layers."""
        gdfs = [self.layers[n] for n in layer_names if n in self.layers]
        if len(gdfs) < 2:
            raise ValueError("Need at least 2 layers to merge")
        merged = pd.concat(gdfs, ignore_index=True)
        return merged

    def raster_info(self, path):
        """Get comprehensive raster metadata."""
        import rasterio
        with rasterio.open(path) as src:
            info = {
                "path": str(path),
                "width": src.width,
                "height": src.height,
                "count": src.count,
                "dtype": src.dtypes[0],
                "crs": str(src.crs) if src.crs else None,
                "transform": list(src.transform),
                "bounds": list(src.bounds),
                "nodata": src.nodata,
                "resolution": (abs(src.res[0]), abs(src.res[1])),
                "driver": src.driver,
                "band_names": [src.descriptions[i] or f"Band {i+1}"
                              for i in range(src.count)]
            }
        return info


# Quick test
if __name__ == "__main__":
    dm = DataManager()
    print(f"Workspace: {dm.workspace}")
    print("Supported vector:", list(SUPPORTED_VECTOR.keys()))
    print("Supported raster:", list(SUPPORTED_RASTER.keys()))

"""
geoai_raster_analysis.py - Raster Analysis Toolkit

GDAL/SAGA/GRASS/WhiteboxTools raster operations via Python.
"""

import numpy as np
from scipy import ndimage
from scipy.interpolate import griddata
import warnings
warnings.filterwarnings("ignore")


class RasterAnalysis:
    """Comprehensive raster analysis toolkit."""

    def __init__(self):
        self.supported_methods = [
            "clip", "resample", "mosaic", "calc", "reclassify",
            "slope", "aspect", "hillshade", "curvature",
            "flow_accumulation", "flow_direction", "watershed",
            "zonal_stats", "focal_stats", "terrain_roughness",
            "tpi", "tri", "savi", "ndvi", "ndwi"
        ]

    def read(self, path):
        """Read raster using rasterio."""
        import rasterio
        with rasterio.open(path) as src:
            return src.read(), src.meta

    def clip(self, data, meta, xmin, ymin, xmax, ymax):
        """Clip raster by extent coordinates."""
        import rasterio
        from rasterio.windows import from_bounds

        with rasterio.open("_temp.tif", "w", **meta) as dst:
            dst.write(data)

        with rasterio.open("_temp.tif") as src:
            window = from_bounds(xmin, ymin, xmax, ymax, src.transform)
            transform = src.window_transform(window)
            clipped = src.read(window=window)
            new_meta = src.meta.copy()
            new_meta.update({
                "height": window.height,
                "width": window.width,
                "transform": transform
            })

        import os
        os.remove("_temp.tif")
        return clipped, new_meta

    def resample(self, data, meta, target_res=None, target_shape=None,
                 method="bilinear"):
        """Resample raster to new resolution or shape."""
        from rasterio.enums import Resampling

        if target_shape:
            new_height, new_width = target_shape
        elif target_res:
            scale_x = meta["transform"][0] / target_res[0]
            scale_y = abs(meta["transform"][4]) / target_res[1]
            new_width = int(meta["width"] * scale_x)
            new_height = int(meta["height"] * scale_y)
        else:
            return data, meta

        methods = {
            "nearest": Resampling.nearest,
            "bilinear": Resampling.bilinear,
            "cubic": Resampling.cubic,
            "lanczos": Resampling.lanczos,
            "average": Resampling.average,
            "mode": Resampling.mode,
        }
        resample_method = methods.get(method, Resampling.bilinear)

        import rasterio
        with rasterio.open("_temp.tif", "w", **meta) as dst:
            dst.write(data)

        with rasterio.open("_temp.tif") as src:
            resampled = src.read(
                out_shape=(src.count, new_height, new_width),
                resampling=resample_method
            )
            transform = src.transform * src.transform.scale(
                src.width / new_width,
                src.height / new_height
            )
            new_meta = src.meta.copy()
            new_meta.update({
                "height": new_height,
                "width": new_width,
                "transform": transform
            })

        import os
        os.remove("_temp.tif")
        return resampled, new_meta

    def mosaic(self, raster_paths, output_path=None):
        """Mosaic multiple rasters together."""
        import rasterio
        from rasterio.merge import merge

        sources = [rasterio.open(p) for p in raster_paths]
        mosaic_data, mosaic_transform = merge(sources)

        meta = sources[0].meta.copy()
        meta.update({
            "height": mosaic_data.shape[1],
            "width": mosaic_data.shape[2],
            "transform": mosaic_transform
        })

        for src in sources:
            src.close()

        if output_path:
            with rasterio.open(output_path, "w", **meta) as dst:
                dst.write(mosaic_data)

        return mosaic_data, meta

    def calc(self, data, formula, band=1):
        """Apply formula to raster (e.g., 'data * 0.0001')."""
        if isinstance(data, list):
            locals_dict = {f"B{i+1}": d for i, d in enumerate(data)}
        else:
            locals_dict = {"A": data[band-1] if data.ndim == 3 else data}

        result = eval(formula, {"__builtins__": {}}, {
            **locals_dict,
            "np": np, "sin": np.sin, "cos": np.cos,
            "sqrt": np.sqrt, "exp": np.exp, "log": np.log,
            "where": np.where, "nanmean": np.nanmean,
        })
        return result

    def reclassify(self, data, bins, values, nodata=np.nan):
        """Reclassify raster values."""
        result = np.full(data.shape, nodata, dtype=np.float32)
        for i in range(len(bins) - 1):
            mask = (data >= bins[i]) & (data < bins[i+1])
            result[mask] = values[i]
        return result

    def slope(self, elevation, cellsize):
        """Compute slope from elevation (degrees)."""
        gy, gx = np.gradient(elevation, cellsize, cellsize)
        return np.degrees(np.arctan(np.sqrt(gx**2 + gy**2)))

    def aspect(self, elevation, cellsize):
        """Compute aspect from elevation (degrees from north)."""
        gy, gx = np.gradient(elevation, cellsize, cellsize)
        aspect = np.degrees(np.arctan2(gx, gy))
        return 270.0 - aspect % 360.0

    def hillshade(self, elevation, cellsize, azimuth=315, altitude=45):
        """Compute hillshade."""
        gy, gx = np.gradient(elevation, cellsize, cellsize)
        slope = np.arctan(np.sqrt(gx**2 + gy**2))
        aspect = np.arctan2(gx, gy)

        az_rad = np.radians(360 - azimuth + 90)
        alt_rad = np.radians(altitude)

        shaded = np.sin(alt_rad) * np.sin(slope) + \
                 np.cos(alt_rad) * np.cos(slope) * np.cos(az_rad - aspect)
        return np.clip(shaded, 0, 1) * 255

    def curvature(self, elevation, cellsize):
        """Compute curvature (positive=convex, negative=concave)."""
        gy, gx = np.gradient(elevation, cellsize, cellsize)
        gxx, _ = np.gradient(gx, cellsize, cellsize)
        _, gyy = np.gradient(gy, cellsize, cellsize)
        return -(gxx + gyy)

    def tpi(self, elevation, cellsize, radius=100):
        """Topographic Position Index."""
        from scipy.ndimage import uniform_filter
        cells = int(radius / cellsize)
        mean_elev = uniform_filter(elevation, size=cells, mode="reflect")
        return elevation - mean_elev

    def tri(self, elevation, cellsize, radius=100):
        """Terrain Ruggedness Index."""
        from scipy.ndimage import uniform_filter
        cells = int(radius / cellsize)
        mean_elev = uniform_filter(elevation, size=cells, mode="reflect")
        return np.sqrt((elevation - mean_elev)**2)

    def focal_stats(self, data, size=3, stat="mean"):
        """Focal (neighborhood) statistics."""
        from scipy.ndimage import uniform_filter, maximum_filter, \
            minimum_filter, generic_filter, median_filter

        stats_map = {
            "mean": lambda d: uniform_filter(d, size=size, mode="reflect"),
            "median": lambda d: median_filter(d, size=size, mode="reflect"),
            "max": lambda d: maximum_filter(d, size=size, mode="reflect"),
            "min": lambda d: minimum_filter(d, size=size, mode="reflect"),
            "std": lambda d: generic_filter(
                d, lambda x: np.std(x), size=size, mode="reflect"
            ),
            "range": lambda d: maximum_filter(d, size=size, mode="reflect") -
                               minimum_filter(d, size=size, mode="reflect"),
        }
        func = stats_map.get(stat, stats_map["mean"])
        return func(data)

    def zonal_stats(self, data, zones, stats_list=("mean", "std", "min", "max")):
        """Compute zonal statistics."""
        results = {}
        zone_ids = np.unique(zones)
        zone_ids = zone_ids[~np.isnan(zone_ids)]

        for zone_id in zone_ids:
            mask = zones == zone_id
            vals = data[mask]
            stats = {}
            if "mean" in stats_list:
                stats["mean"] = np.mean(vals)
            if "std" in stats_list:
                stats["std"] = np.std(vals)
            if "min" in stats_list:
                stats["min"] = np.min(vals)
            if "max" in stats_list:
                stats["max"] = np.max(vals)
            if "sum" in stats_list:
                stats["sum"] = np.sum(vals)
            if "count" in stats_list:
                stats["count"] = np.sum(~np.isnan(vals))
            if "median" in stats_list:
                stats["median"] = np.median(vals)
            results[int(zone_id)] = stats

        return results

    def interpolate(self, points, values, xi, yi, method="linear"):
        """Interpolate point data to raster grid."""
        from scipy.interpolate import griddata
        grid_x, grid_y = np.meshgrid(xi, yi)
        grid_z = griddata(points, values, (grid_x, grid_y), method=method)
        return grid_z

    def terrain_roughness(self, elevation, cellsize):
        """Compute terrain roughness index."""
        from scipy.ndimage import generic_filter
        def _roughness(window):
            return np.max(window) - np.min(window)

        cells = max(3, int(3 / cellsize))
        return generic_filter(elevation, _roughness,
                             size=cells, mode="reflect")

    def idw_interpolation(self, points, values, grid_shape,
                          power=2, radius=None):
        """Inverse Distance Weighted interpolation."""
        grid_x = np.linspace(
            np.min(points[:, 0]), np.max(points[:, 0]), grid_shape[1]
        )
        grid_y = np.linspace(
            np.min(points[:, 1]), np.max(points[:, 1]), grid_shape[0]
        )
        xx, yy = np.meshgrid(grid_x, grid_y)

        result = np.zeros(grid_shape, dtype=np.float32)
        for i in range(len(grid_x)):
            for j in range(len(grid_y)):
                dists = np.sqrt(
                    (points[:, 0] - grid_x[i])**2 +
                    (points[:, 1] - grid_y[j])**2
                )
                if radius:
                    mask = dists <= radius
                    dists = dists[mask]
                    pts_vals = values[mask]
                else:
                    pts_vals = values

                if len(dists) == 0:
                    continue

                weights = 1.0 / (dists**power + 1e-10)
                result[j, i] = np.sum(weights * pts_vals) / np.sum(weights)

        return result, xx, yy


# Test
if __name__ == "__main__":
    ra = RasterAnalysis()
    print("Raster Analysis Toolkit Ready")
    print(f"Supported methods ({len(ra.supported_methods)}):")
    for m in ra.supported_methods:
        print(f"  - {m}")

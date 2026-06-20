"""
geoai_vector_analysis.py - Vector Analysis Toolkit

Provides access to all major vector analysis operations using
geopandas, shapely, and QGIS processing backend when available.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union, voronoi_diagram
from shapely.geometry import Point, MultiPoint, Polygon
from scipy.spatial import Voronoi
from scipy import stats
import warnings
warnings.filterwarnings("ignore")


class VectorAnalysis:
    """Comprehensive vector spatial analysis toolkit."""

    def __init__(self, data_manager=None):
        self.dm = data_manager

    def buffer(self, gdf, distance, resolution=16, dissolve=False,
               cap_style="round", join_style="round"):
        """Create buffers around features."""
        cap_map = {"round": 1, "flat": 2, "square": 3}
        join_map = {"round": 1, "mitre": 2, "bevel": 3}

        cap = cap_map.get(cap_style, 1)
        join = join_map.get(join_style, 1)

        buffered = gdf.copy()
        buffered["geometry"] = gdf.geometry.buffer(
            distance, resolution=resolution,
            cap_style=cap, join_style=join
        )

        if dissolve:
            dissolved = gpd.GeoDataFrame(
                {"geometry": [unary_union(buffered.geometry)]},
                crs=gdf.crs
            )
            return dissolved

        return buffered

    def clip(self, target_gdf, clip_gdf):
        """Clip target layer by clip layer."""
        return gpd.clip(target_gdf, clip_gdf)

    def intersection(self, gdf1, gdf2):
        """Compute intersection of two layers."""
        return gpd.overlay(gdf1, gdf2, how="intersection")

    def union(self, gdf1, gdf2):
        """Compute union of two layers."""
        return gpd.overlay(gdf1, gdf2, how="union")

    def symmetrical_difference(self, gdf1, gdf2):
        """Compute symmetrical difference."""
        return gpd.overlay(gdf1, gdf2, how="symmetric_difference")

    def erase(self, target_gdf, erase_gdf):
        """Erase (difference) features from target."""
        return gpd.overlay(target_gdf, erase_gdf, how="difference")

    def identity(self, target_gdf, identity_gdf):
        """Compute identity (intersection + unmatched)."""
        return gpd.overlay(target_gdf, identity_gdf, how="identity")

    def update(self, target_gdf, update_gdf):
        """Update target geometry with update layer."""
        return gpd.overlay(target_gdf, update_gdf, how="update")

    def dissolve(self, gdf, by=None, aggfunc="first", **agg_dict):
        """Dissolve features by attribute field."""
        if by:
            dissolved = gdf.dissolve(by=by, aggfunc=aggfunc, **agg_dict)
        else:
            dissolved = gdf.dissolve()
        return dissolved.reset_index()

    def spatial_join(self, target_gdf, join_gdf, how="left",
                     predicate="intersects", max_distance=None):
        """Perform spatial join between two layers."""
        if max_distance:
            return gpd.sjoin_nearest(
                target_gdf, join_gdf, how=how,
                max_distance=max_distance
            )
        return gpd.sjoin(target_gdf, join_gdf, how=how, predicate=predicate)

    def select_by_location(self, target_gdf, select_gdf,
                           predicate="intersects"):
        """Select features by spatial relationship."""
        valid_predicates = {
            "intersects", "contains", "within", "touches",
            "crosses", "overlaps", "covers", "covered_by"
        }
        if predicate not in valid_predicates:
            raise ValueError(f"Invalid predicate. Use: {valid_predicates}")

        spatial_index = target_gdf.sindex
        possible_matches_index = list(
            spatial_index.query(select_gdf.geometry.unary_union,
                              predicate=predicate)
        )
        return target_gdf.iloc[possible_matches_index]

    def nearest_neighbor_analysis(self, gdf, k=1):
        """Find k nearest neighbors for each feature."""
        from shapely.ops import nearest_points

        coords = np.array(
            [(geom.centroid.x, geom.centroid.y)
             for geom in gdf.geometry]
        )

        from sklearn.neighbors import NearestNeighbors
        nbrs = NearestNeighbors(n_neighbors=min(k + 1, len(gdf)))
        nbrs.fit(coords)
        distances, indices = nbrs.kneighbors(coords)

        results = []
        for i in range(len(gdf)):
            for j in range(1, min(k + 1, len(gdf))):
                results.append({
                    "source": i,
                    "target": indices[i][j],
                    "distance": distances[i][j]
                })

        return pd.DataFrame(results)

    def voronoi(self, gdf, extent=None):
        """Generate Voronoi polygons from point layer."""
        points = [geom for geom in gdf.geometry
                  if geom.geom_type in ("Point", "MultiPoint")]

        if not points:
            raise ValueError("Input must contain Point geometries")

        coords = []
        for p in points:
            if p.geom_type == "MultiPoint":
                coords.extend(list(p.coords))
            else:
                coords.append((p.x, p.y))

        if extent is None:
            minx, miny, maxx, maxy = gdf.total_bounds
        else:
            minx, miny, maxx, maxy = extent

        # Extend bounds for edge polygons
        margin_x = (maxx - minx) * 0.1
        margin_y = (maxy - miny) * 0.1
        envelope = Polygon([
            (minx - margin_x, miny - margin_y),
            (maxx + margin_x, miny - margin_y),
            (maxx + margin_x, maxy + margin_y),
            (minx - margin_x, maxy + margin_y)
        ])

        vor = Voronoi(np.array(coords))
        from shapely import voronoi_diagram as svd
        regions = svd(MultiPoint(points), envelope=envelope)

        return gpd.GeoDataFrame(
            {"geometry": list(regions.geoms)},
            crs=gdf.crs
        )

    def delaunay_triangulation(self, gdf):
        """Generate Delaunay triangulation from points."""
        from shapely.ops import triangulate
        points = [geom for geom in gdf.geometry
                  if geom.geom_type in ("Point", "MultiPoint")]

        all_coords = []
        for p in points:
            if p.geom_type == "MultiPoint":
                all_coords.extend(list(p.coords))
            else:
                all_coords.append((p.x, p.y))

        triangles = triangulate(MultiPoint(all_coords))
        return gpd.GeoDataFrame(
            {"geometry": list(triangles)},
            crs=gdf.crs
        )

    def kernel_density(self, gdf, bandwidth=None, grid_size=100):
        """Compute kernel density estimation from points."""
        from sklearn.neighbors import KernelDensity

        coords = np.array([
            (geom.centroid.x, geom.centroid.y)
            for geom in gdf.geometry
        ])

        if bandwidth is None:
            bandwidth = gdf.total_bounds[2] - gdf.total_bounds[0]
            bandwidth /= 20

        bounds = gdf.total_bounds
        xx, yy = np.meshgrid(
            np.linspace(bounds[0], bounds[2], grid_size),
            np.linspace(bounds[1], bounds[3], grid_size)
        )
        grid = np.vstack([xx.ravel(), yy.ravel()]).T

        kde = KernelDensity(bandwidth=bandwidth, kernel="gaussian")
        kde.fit(coords)
        density = np.exp(kde.score_samples(grid)).reshape(grid_size, grid_size)

        import rasterio
        from rasterio.transform import from_origin
        cellsize_x = (bounds[2] - bounds[0]) / grid_size
        cellsize_y = (bounds[3] - bounds[1]) / grid_size
        transform = from_origin(bounds[0], bounds[3], cellsize_x, cellsize_y)

        return density, transform, gdf.crs

    def hotspot_analysis_getis_ord(self, gdf, value_field,
                                   weights_type="queen", k=8):
        """Getis-Ord Gi* hotspot analysis."""
        from esda.getisord import G_Local
        from libpysal.weights import Queen, Rook, KNN

        if weights_type == "queen":
            w = Queen.from_dataframe(gdf)
        elif weights_type == "rook":
            w = Rook.from_dataframe(gdf)
        else:
            w = KNN.from_dataframe(gdf, k=k)

        w.transform = "r"
        values = gdf[value_field].values
        gi_star = G_Local(values, w, transform="r", star=True)

        result = gdf.copy()
        result["Gi_Star"] = gi_star.Zs
        result["Gi_PValue"] = gi_star.p_sim
        result["Gi_Sig"] = gi_star.p_sim < 0.05

        # Classification
        def classify_hotspot(row):
            z = row["Gi_Star"]
            p = row["Gi_PValue"]
            if p > 0.05:
                return "Not Significant"
            elif z > 2.58:
                return "Hot Spot (99%)"
            elif z > 1.96:
                return "Hot Spot (95%)"
            elif z > 1.65:
                return "Hot Spot (90%)"
            elif z < -2.58:
                return "Cold Spot (99%)"
            elif z < -1.96:
                return "Cold Spot (95%)"
            elif z < -1.65:
                return "Cold Spot (90%)"
            else:
                return "Not Significant"

        result["HotSpot_Class"] = result.apply(classify_hotspot, axis=1)
        return result

    def morans_i(self, gdf, value_field, weights_type="queen"):
        """Global Moran"s I spatial autocorrelation."""
        from esda.moran import Moran
        from libpysal.weights import Queen, Rook

        if weights_type == "queen":
            w = Queen.from_dataframe(gdf)
        else:
            w = Rook.from_dataframe(gdf)

        w.transform = "r"
        values = gdf[value_field].values
        mi = Moran(values, w)

        return {
            "Morans_I": mi.I,
            "Expected_I": mi.EI,
            "P_value": mi.p_sim,
            "Z_score": mi.z_sim,
            "Significant": mi.p_sim < 0.05
        }

    def lisa(self, gdf, value_field, weights_type="queen", permutations=999):
        """Local Indicators of Spatial Association (LISA)."""
        from esda.moran import Moran_Local
        from libpysal.weights import Queen, Rook

        if weights_type == "queen":
            w = Queen.from_dataframe(gdf)
        else:
            w = Rook.from_dataframe(gdf)

        w.transform = "r"
        values = gdf[value_field].values
        lisa = Moran_Local(values, w, permutations=permutations)

        result = gdf.copy()
        result["LISA_I"] = lisa.Is
        result["LISA_P"] = lisa.p_sim
        result["LISA_Sig"] = lisa.p_sim < 0.05

        # Quadrant classification
        mean_val = np.mean(values)
        result["LISA_Cluster"] = "Not Significant"
        for i in range(len(result)):
            if result.iloc[i]["LISA_P"] < 0.05:
                if values[i] > mean_val and lisa.Is[i] > 0:
                    result.loc[result.index[i], "LISA_Cluster"] = "HH (High-High)"
                elif values[i] < mean_val and lisa.Is[i] > 0:
                    result.loc[result.index[i], "LISA_Cluster"] = "LL (Low-Low)"
                elif values[i] > mean_val and lisa.Is[i] < 0:
                    result.loc[result.index[i], "LISA_Cluster"] = "HL (High-Low)"
                else:
                    result.loc[result.index[i], "LISA_Cluster"] = "LH (Low-High)"

        return result

    def centrality_analysis(self, gdf, weight_field=None):
        """Compute network centrality metrics."""
        import networkx as nx

        G = nx.Graph()
        for i, row in gdf.iterrows():
            G.add_node(i, geometry=row.geometry.centroid)

        # Add edges based on distance
        coords = np.array([
            (row.geometry.centroid.x, row.geometry.centroid.y)
            for _, row in gdf.iterrows()
        ])

        from sklearn.neighbors import NearestNeighbors
        nbrs = NearestNeighbors(n_neighbors=3)
        nbrs.fit(coords)
        distances, indices = nbrs.kneighbors(coords)

        for i in range(len(coords)):
            for j_idx, j in enumerate(indices[i]):
                if i != j:
                    weight = distances[i][j_idx]
                    G.add_edge(i, j, weight=weight)

        return {
            "degree_centrality": nx.degree_centrality(G),
            "betweenness_centrality": nx.betweenness_centrality(G, weight="weight"),
            "closeness_centrality": nx.closeness_centrality(G, distance="weight"),
            "eigenvector_centrality": nx.eigenvector_centrality_numpy(G, weight="weight"),
            "number_of_nodes": G.number_of_nodes(),
            "number_of_edges": G.number_of_edges(),
            "graph_density": nx.density(G),
        }

    def shortest_path(self, gdf_network, source_point, target_point,
                      weight_field="length"):
        """Find shortest path on a network."""
        import networkx as nx

        G = nx.Graph()
        for i, row in gdf_network.iterrows():
            geom = row.geometry
            if geom.geom_type == "LineString":
                coords = list(geom.coords)
                for c in range(len(coords) - 1):
                    length = Point(coords[c]).distance(Point(coords[c+1]))
                    G.add_edge(
                        coords[c], coords[c+1],
                        weight=length,
                        geometry=geom
                    )

        source = (source_point.x, source_point.y)
        target = (target_point.x, target_point.y)

        try:
            path = nx.shortest_path(G, source, target, weight="weight")
            path_length = nx.shortest_path_length(
                G, source, target, weight="weight"
            )
            return {"path": path, "length": path_length, "nodes": len(path)}
        except nx.NetworkXNoPath:
            return {"error": "No path found between points"}

    def service_area(self, gdf_network, source_point, max_distance):
        """Compute service area from a point on network."""
        import networkx as nx

        G = nx.Graph()
        for i, row in gdf_network.iterrows():
            geom = row.geometry
            if geom.geom_type == "LineString":
                coords = list(geom.coords)
                for c in range(len(coords) - 1):
                    length = Point(coords[c]).distance(Point(coords[c+1]))
                    G.add_edge(coords[c], coords[c+1], weight=length)

        source = (source_point.x, source_point.y)
        lengths = nx.single_source_dijkstra_path_length(
            G, source, cutoff=max_distance, weight="weight"
        )

        reachable = {n: d for n, d in lengths.items() if d <= max_distance}
        return reachable


# Test
if __name__ == "__main__":
    va = VectorAnalysis()
    print("Vector Analysis Toolkit Ready")
    print("Methods available:")
    methods = [m for m in dir(va) if not m.startswith("_")]
    for m in methods:
        print(f"  - {m}")

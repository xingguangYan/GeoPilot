"""
geoai_remote_sensing.py - Remote Sensing Analysis Toolkit

Covers: indices computation, supervised/unsupervised classification,
time series analysis, change detection
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import (accuracy_score, cohen_kappa_score,
                             confusion_matrix, classification_report)
import warnings
warnings.filterwarnings("ignore")


class RemoteSensing:
    """Remote sensing analysis toolkit."""

    # Spectral index formulas
    INDICES = {
        # Vegetation
        "NDVI":  lambda B: (B["N"] - B["R"]) / (B["N"] + B["R"] + 1e-10),
        "EVI":   lambda B: 2.5 * (B["N"] - B["R"]) / (B["N"] + 6*B["R"] - 7.5*B.get("B", 0) + 1 + 1e-10),
        "EVI2":  lambda B: 2.5 * (B["N"] - B["R"]) / (B["N"] + 2.4*B["R"] + 1 + 1e-10),
        "SAVI":  lambda B: (B["N"] - B["R"]) * 1.5 / (B["N"] + B["R"] + 0.5 + 1e-10),
        "OSAVI": lambda B: (B["N"] - B["R"]) / (B["N"] + B["R"] + 0.16 + 1e-10),
        "MSAVI2": lambda B: (2*B["N"]+1 - np.sqrt((2*B["N"]+1)**2 - 8*(B["N"]-B["R"]))) / 2,
        "ARVI":  lambda B: (B["N"] - (2*B["R"] - B.get("B",0))) / (B["N"] + (2*B["R"] - B.get("B",0)) + 1e-10),
        "GCVI":  lambda B: (B["N"] / B.get("G", 1)) - 1,
        "NDRE":  lambda B: (B["N"] - B.get("RE1", 0)) / (B["N"] + B.get("RE1", 0) + 1e-10),
        "CVI":   lambda B: B["N"] * B["R"] / (B.get("G", 1)**2 + 1e-10),
        "RVI":   lambda B: B["N"] / (B["R"] + 1e-10),
        "DVI":   lambda B: B["N"] - B["R"],
        # Water
        "NDWI":  lambda B: (B.get("G", 0) - B["N"]) / (B.get("G", 0) + B["N"] + 1e-10),
        "MNDWI": lambda B: (B.get("G", 0) - B.get("S1", 0)) / (B.get("G", 0) + B.get("S1", 0) + 1e-10),
        "AWEI_sh": lambda B: B.get("B", 0) + 2.5*B.get("G", 0) - 1.5*(B["N"]+B.get("S1",0)) - 0.25*B.get("S2", 0),
        "AWEI_nsh": lambda B: 4*(B.get("G",0)-B.get("S1",0)) - (0.25*B["N"]+2.75*B.get("S2",0)),
        "WRI":   lambda B: (B.get("G",0)+B["R"]) / (B["N"]+B.get("S1",0)+1e-10),
        # Built-up
        "NDBI":  lambda B: (B.get("S1", 0) - B["N"]) / (B.get("S1", 0) + B["N"] + 1e-10),
        "BUI":   lambda B: ((B.get("S1",0)-B["N"])/(B.get("S1",0)+B["N"]+1e-10)) - ((B["N"]-B["R"])/(B["N"]+B["R"]+1e-10)),
        "IBI":   lambda B: ((2*B.get("S1",0)/(B.get("S1",0)+B["N"]+1e-10) -
                            (B["N"]/(B["N"]+B["R"]+1e-10) + B.get("G",0)/(B.get("G",0)+B.get("S1",0)+1e-10))) /
                           (2*B.get("S1",0)/(B.get("S1",0)+B["N"]+1e-10) +
                            (B["N"]/(B["N"]+B["R"]+1e-10) + B.get("G",0)/(B.get("G",0)+B.get("S1",0)+1e-10)))),
        # Burn
        "NBR":   lambda B: (B["N"] - B.get("S2", 0)) / (B["N"] + B.get("S2", 0) + 1e-10),
        "dNBR":  lambda B_pre, B_post: B_post - B_pre,
        "BAI":   lambda B: 1 / ((0.1 - B["R"])**2 + (0.06 - B["N"])**2 + 1e-10),
        # Moisture
        "NDMI":  lambda B: (B["N"] - B.get("S1", 0)) / (B["N"] + B.get("S1", 0) + 1e-10),
        "MSI":   lambda B: B.get("S1", 0) / (B["N"] + 1e-10),
        # Snow
        "NDSI":  lambda B: (B.get("G",0) - B.get("S1",0)) / (B.get("G",0) + B.get("S1",0) + 1e-10),
        # Soil
        "BI":    lambda B: np.sqrt((B["R"]**2 + B.get("G",0)**2 + B["N"]**2) / 3),
        "CI":    lambda B: (B["R"] - B.get("G",0)) / (B["R"] + B.get("G",0) + 1e-10),
    }

    def __init__(self):
        self.classifiers = {}
        self.trained = {}

    def compute_index(self, bands, index_name):
        """Compute a spectral index from band dict.
        bands = {"B": blue, "G": green, "R": red, "N": nir,
                 "S1": swir1, "S2": swir2, "RE1": rededge1}
        """
        if index_name not in self.INDICES:
            raise ValueError(f"Unknown index: {index_name}. "
                           f"Available: {list(self.INDICES.keys())}")
        return self.INDICES[index_name](bands)

    def compute_multiple_indices(self, bands, index_names):
        """Compute multiple indices at once."""
        results = {}
        for name in index_names:
            results[name] = self.compute_index(bands, name)
        return results

    def compute_all_indices(self, bands):
        """Compute all available indices."""
        results = {}
        for name in self.INDICES:
            try:
                results[name] = self.compute_index(bands, name)
            except Exception:
                continue
        return results

    def extract_training_data(self, raster_stack, roi_gdf, field_name=None):
        """Extract training data from raster stack using ROI polygons."""
        import rasterio
        from rasterio.mask import mask as rio_mask
        from geopandas import GeoDataFrame

        samples = []
        if field_name:
            for _, row in roi_gdf.iterrows():
                geom = [row.geometry]
                label = row[field_name]
                out_img, _ = rio_mask(raster_stack, geom, crop=True)
                pixels = out_img.reshape(out_img.shape[0], -1).T
                for pixel in pixels:
                    if not np.any(np.isnan(pixel)) and not np.any(np.isinf(pixel)):
                        samples.append((*pixel, label))
        else:
            for _, row in roi_gdf.iterrows():
                geom = [row.geometry]
                out_img, _ = rio_mask(raster_stack, geom, crop=True)
                pixels = out_img.reshape(out_img.shape[0], -1).T
                for pixel in pixels:
                    if not np.any(np.isnan(pixel)) and not np.any(np.isinf(pixel)):
                        samples.append((*pixel, 1))

        df = pd.DataFrame(samples)
        n_bands = raster_stack.count
        band_cols = [f"Band_{i+1}" for i in range(n_bands)]
        df.columns = band_cols + ["Label"]
        return df

    def sample_raster(self, raster_path, n_samples=1000, seed=42):
        """Random sampling of raster values."""
        import rasterio
        rs = np.random.RandomState(seed)

        with rasterio.open(raster_path) as src:
            data = src.read()
            n_bands, h, w = data.shape
            valid_mask = ~np.any(np.isnan(data), axis=0)

            valid_indices = np.argwhere(valid_mask)
            if len(valid_indices) < n_samples:
                n_samples = len(valid_indices)

            chosen = valid_indices[rs.choice(len(valid_indices), n_samples, replace=False)]
            samples = data[:, chosen[:, 0], chosen[:, 1]].T
            coords = chosen

        return samples, coords

    # ==================== Classification ====================

    def _get_classifier(self, algorithm, **params):
        """Initialize classifier by algorithm name."""
        algos = {
            "rf": RandomForestClassifier,
            "svm": SVC,
            "cart": DecisionTreeClassifier,
            "xgb": lambda: __import__("xgboost", fromlist=["XGBClassifier"]).XGBClassifier,
            "lgbm": lambda: __import__("lightgbm", fromlist=["LGBMClassifier"]).LGBMClassifier,
            "gbdt": GradientBoostingClassifier,
            "knn": KNeighborsClassifier,
            "catboost": lambda: __import__("catboost", fromlist=["CatBoostClassifier"]).CatBoostClassifier,
        }

        if algorithm not in algos:
            raise ValueError(f"Unknown algorithm: {algorithm}. "
                           f"Available: {list(algos.keys())}")

        algo_class = algos[algorithm]
        if callable(algo_class) and algorithm in ("xgb", "lgbm", "catboost"):
            try:
                clf = algo_class()(**params)
            except Exception:
                clf = algo_class()(**params)
        else:
            clf = algo_class(**params)

        return clf

    def train(self, X, y, algorithm="rf", test_size=0.3, **params):
        """Train a classifier and return performance metrics."""
        clf = self._get_classifier(algorithm, **params)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        metrics = {
            "algorithm": algorithm,
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "kappa": float(cohen_kappa_score(y_test, y_pred)),
            "classification_report": classification_report(y_test, y_pred,
                                                          output_dict=True),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "n_classes": len(np.unique(y)),
            "n_features": X.shape[1],
            "n_samples": len(X),
        }

        self.classifiers[algorithm] = clf
        self.trained[algorithm] = metrics
        return metrics

    def classify_raster(self, raster_data, algorithm="rf"):
        """Apply trained classifier to raster data."""
        if algorithm not in self.classifiers:
            raise ValueError(f"Classifier {algorithm} not trained yet.")

        clf = self.classifiers[algorithm]
        original_shape = raster_data.shape[1:] if raster_data.ndim == 3 else raster_data.shape
        flat = raster_data.reshape(raster_data.shape[0], -1).T
        valid = ~np.any(np.isnan(flat), axis=1)

        result = np.full(flat.shape[0], -9999, dtype=np.int32)
        result[valid] = clf.predict(flat[valid])
        return result.reshape(original_shape)

    def cross_validate(self, X, y, algorithm="rf", cv=5, **params):
        """Cross-validate classification performance."""
        clf = self._get_classifier(algorithm, **params)
        scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
        return {
            "scores": scores.tolist(),
            "mean": float(scores.mean()),
            "std": float(scores.std()),
            "cv_folds": cv
        }

    def feature_importance(self, algorithm="rf"):
        """Get feature importance from trained model."""
        if algorithm not in self.classifiers:
            raise ValueError(f"Classifier {algorithm} not trained.")
        clf = self.classifiers[algorithm]
        if hasattr(clf, "feature_importances_"):
            return clf.feature_importances_.tolist()
        elif hasattr(clf, "coef_"):
            return np.abs(clf.coef_).mean(axis=0).tolist()
        else:
            return None

    # ==================== Change Detection ====================

    def image_difference(self, image1, image2):
        """Simple image difference."""
        return image2 - image1

    def image_ratio(self, image1, image2):
        """Image ratio change detection."""
        return image2 / (image1 + 1e-10)

    def ndvi_change(self, ndvi1, ndvi2):
        """NDVI change detection (dNDVI)."""
        return ndvi2 - ndvi1

    def change_vector_analysis(self, bands1, bands2):
        """Change Vector Analysis."""
        diff = bands2 - bands1
        magnitude = np.sqrt(np.sum(diff**2, axis=0))
        angle = np.arctan2(diff[1] if diff.shape[0] > 1 else diff[0],
                          diff[0])
        return magnitude, angle

    def post_classification_comparison(self, class1, class2,
                                       class_names=None):
        """Post-classification change detection."""
        change_matrix = np.zeros((class1.max()+1, class2.max()+1),
                                dtype=np.int64)
        for i in range(class1.shape[0]):
            for j in range(class1.shape[1]):
                c1 = int(class1[i, j])
                c2 = int(class2[i, j])
                if c1 >= 0 and c2 >= 0:
                    change_matrix[c1, c2] += 1

        # Change map
        change_map = np.zeros(class1.shape, dtype=np.int32)
        mask = class1 != class2
        change_map[mask] = 1

        # Statistics
        total = class1.size
        unchanged = np.sum(class1 == class2)
        changed = total - unchanged

        stats = {
            "total_pixels": int(total),
            "unchanged": int(unchanged),
            "changed": int(changed),
            "change_percentage": float(changed / total * 100),
            "change_matrix": change_matrix.tolist()
        }

        return change_map, stats

    # ==================== Time Series ====================

    def mann_kendall_test(self, series):
        """Mann-Kendall trend test for time series."""
        from scipy.stats import kendalltau, norm
        import math

        n = len(series)
        if n < 3:
            return {"error": "Need at least 3 time points"}

        tau, p_value = kendalltau(np.arange(n), series)
        S = 0
        for i in range(n-1):
            for j in range(i+1, n):
                S += np.sign(series[j] - series[i])

        # Variance
        ties = pd.Series(series).value_counts()
        variance = n * (n-1) * (2*n+5) / 18
        variance -= np.sum(ties * (ties-1) * (2*ties+5)) / 18

        if variance > 0:
            Z = (S - 1) / math.sqrt(variance) if S > 0 else \
                (S + 1) / math.sqrt(variance) if S < 0 else 0
            p_value_norm = 2 * (1 - norm.cdf(abs(Z)))
        else:
            Z = 0
            p_value_norm = 1.0

        return {
            "S": int(S),
            "Kendall_tau": float(tau),
            "p_value": float(p_value),
            "p_value_normal": float(p_value_norm),
            "Z_score": float(Z),
            "trend": "increasing" if S > 0 and p_value < 0.05 else
                     "decreasing" if S < 0 and p_value < 0.05 else
                     "no significant trend"
        }

    def sen_slope(self, series):
        """Sen"s slope estimator."""
        n = len(series)
        slopes = []
        for i in range(n-1):
            for j in range(i+1, n):
                slopes.append((series[j] - series[i]) / (j - i))
        return float(np.median(slopes))

    def theil_sen_regression(self, x, y):
        """Theil-Sen robust regression."""
        from sklearn.linear_model import TheilSenRegressor
        model = TheilSenRegressor(random_state=42)
        model.fit(x.reshape(-1, 1), y)
        return {
            "slope": float(model.coef_[0]),
            "intercept": float(model.intercept_),
            "predict": model.predict(x.reshape(-1, 1))
        }

    def breakpoint_detection(self, series, min_segment=3):
        """Simple breakpoint detection using piecewise linear fit."""
        n = len(series)
        best_rss = float("inf")
        best_bk = None

        for bk in range(min_segment, n - min_segment):
            x1 = np.arange(bk)
            x2 = np.arange(bk, n) - bk
            y1 = series[:bk]
            y2 = series[bk:]

            if len(x1) < 2 or len(x2) < 2:
                continue

            z1 = np.polyfit(x1, y1, 1)
            z2 = np.polyfit(x2, y2, 1)
            rss = np.sum((y1 - np.polyval(z1, x1))**2) + \
                  np.sum((y2 - np.polyval(z2, x2))**2)

            if rss < best_rss:
                best_rss = rss
                best_bk = bk

        if best_bk:
            return {
                "breakpoint": int(best_bk),
                "segments": 2,
                "rss": float(best_rss)
            }
        return {"breakpoint": None, "segments": 1}


# Test
if __name__ == "__main__":
    rs = RemoteSensing()
    print("Remote Sensing Toolkit Ready")
    print(f"Available indices ({len(rs.INDICES)}):")
    for name in sorted(rs.INDICES.keys()):
        print(f"  - {name}")
    print(f"\nAvailable classifiers: rf, svm, cart, xgb, lgbm, gbdt, knn, catboost")

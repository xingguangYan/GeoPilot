import os, sys, platform, subprocess, json
from pathlib import Path

def detect_qgis():
    """Detect QGIS installation on the system."""
    candidates = [
        r"D:\QGIS",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expanduser(r"~\AppData\Local\Programs"),
        r"C:\OSGeo4W",
        r"C:\OSGeo4W64",
    ]
    qgis_versions = []
    for base in candidates:
        if not os.path.exists(base):
            continue
        try:
            for item in os.listdir(base):
                if "QGIS" in item.upper():
                    qgis_path = os.path.join(base, item)
                    if os.path.isdir(qgis_path):
                        qgis_versions.append({
                            "path": qgis_path,
                            "version": item,
                            "bin": os.path.join(qgis_path, "bin") if os.path.isdir(os.path.join(qgis_path, "bin")) else None,
                            "apps": os.path.join(qgis_path, "apps", "qgis") if os.path.isdir(os.path.join(qgis_path, "apps", "qgis")) else None
                        })
        except PermissionError:
            continue

    # Check D:\QGIS\ layout (OSGeo4W)
    if os.path.exists(r"D:\QGIS\bin\qgis-bin.exe") and os.path.exists(r"D:\QGIS\apps\qgis"):
        qgis_versions.append({
            "path": r"D:\QGIS",
            "version": "OSGeo4W",
            "bin": r"D:\QGIS\bin",
            "apps": r"D:\QGIS\apps\qgis"
        })

    return qgis_versions


def detect_conda_envs():
    try:
        result = subprocess.run(["conda", "env", "list", "--json"],
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            envs = []
            for env in data.get("envs", []):
                env_path = Path(env)
                if (env_path / "python.exe").exists() or (env_path / "bin" / "python").exists():
                    envs.append({"name": env_path.name, "path": str(env_path)})
            return envs
    except Exception:
        return []
    return []


def check_python_gis_packages():
    packages = [
        "geopandas", "shapely", "rasterio", "fiona", "pyproj",
        "gdal", "numpy", "pandas", "scipy", "scikit-learn",
        "matplotlib", "seaborn", "earthengine-api", "geemap",
        "xarray", "rioxarray", "netCDF4", "h5py",
        "tensorflow", "torch", "pyqgis"
    ]
    results = {}
    for pkg in packages:
        try:
            mod = __import__(pkg.replace("-", "_"))
            version = getattr(mod, "__version__", "installed")
            results[pkg] = version
        except ImportError:
            results[pkg] = None
    return results


def generate_env_report():
    report = {
        "system": {"platform": platform.platform(), "python": sys.version},
        "qgis": detect_qgis(),
        "conda_envs": detect_conda_envs(),
        "python_packages": check_python_gis_packages()
    }
    return report


def setup_pyqgis_standalone(qgis_path=None):
    if qgis_path is None:
        qgis_versions = detect_qgis()
        if not qgis_versions:
            print("WARNING: QGIS not found.")
            return False
        qgis_path = qgis_versions[0]["path"]

    qgis_apps = os.path.join(qgis_path, "apps", "qgis")
    qgis_bin = os.path.join(qgis_path, "bin")

    os.environ["PATH"] = qgis_bin + ";" + os.environ.get("PATH", "")
    os.environ["PATH"] = os.path.join(qgis_apps, "bin") + ";" + os.environ.get("PATH", "")
    os.environ["PYTHONPATH"] = os.path.join(qgis_apps, "python")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qgis_path, "apps", "Qt5", "plugins")

    sys.path.insert(0, os.path.join(qgis_apps, "python"))
    sys.path.insert(0, os.path.join(qgis_apps, "python", "plugins"))

    if platform.system() == "Windows":
        os.environ["PATH"] = os.path.join(qgis_path, "apps", "Qt5", "plugins") + ";" + os.environ["PATH"]

    return True


if __name__ == "__main__":
    report = generate_env_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

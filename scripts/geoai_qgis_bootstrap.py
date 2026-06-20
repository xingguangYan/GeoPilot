"""QGIS Python Bootstrap - init QGIS for headless processing"""
import sys, os
QGIS_PATH = r"D:\QGIS"

def init_qgis(qgis_path=None):
    if qgis_path is None:
        qgis_path = QGIS_PATH
    apps_dir = os.path.join(qgis_path, "apps", "qgis")
    bin_dir = os.path.join(qgis_path, "bin")
    os.environ.setdefault("PATH", "")
    os.environ["PATH"] = bin_dir + ";" + os.environ["PATH"]
    os.environ["PATH"] = os.path.join(apps_dir, "bin") + ";" + os.environ["PATH"]
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qgis_path, "apps", "Qt5", "plugins")
    sys.path.insert(0, os.path.join(apps_dir, "python"))
    sys.path.insert(0, os.path.join(apps_dir, "python", "plugins"))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from qgis.core import QgsApplication
    QgsApplication.setPrefixPath(apps_dir, True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    from processing.core.Processing import Processing
    Processing.initialize()
    return qgs

def demo():
    qgs = init_qgis()
    from qgis.core import QgsApplication
    algs = QgsApplication.processingRegistry().algorithms()
    print("QGIS: " + QgsApplication.applicationVersion())
    print("Algorithms: %d" % len(algs))
    qgs.exitQgis()

if __name__ == "__main__":
    demo()

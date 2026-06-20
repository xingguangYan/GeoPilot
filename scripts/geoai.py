"""geoai.py - Unified Command-Line Interface for QGIS GeoAI Studio"""
import sys, os, argparse

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(description="QGIS GeoAI Studio CLI")
    subparsers = parser.add_subparsers(dest="command")

    # env
    p_env = subparsers.add_parser("env", help="Check environment")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan directory for data")
    p_scan.add_argument("path", nargs="?", default=".", help="Directory to scan")

    # index
    p_idx = subparsers.add_parser("index", help="Compute spectral index")
    p_idx.add_argument("index", help="Index name (NDVI, EVI, NDWI, etc.)")

    # classify
    p_cls = subparsers.add_parser("classify", help="Run classification")
    p_cls.add_argument("algorithm", default="rf", help="rf, svm, xgb, etc.")

    # figure
    p_fig = subparsers.add_parser("figure", help="Generate SCI figure")
    p_fig.add_argument("type", help="study_area, land_cover, accuracy, etc.")

    # recommend
    p_rec = subparsers.add_parser("recommend", help="Recommend journals")
    p_rec.add_argument("--if", type=float, dest="target_if", help="Target IF")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run analysis pipeline")
    p_pipe.add_argument("name", help="urban, forest, carbon, water, eco, lulc")

    # report
    p_rep = subparsers.add_parser("report", help="Generate research report")

    args = parser.parse_args()

    if args.command == "env":
        from geoai_env_setup import generate_env_report
        import json; print(json.dumps(generate_env_report(), indent=2))
    elif args.command == "scan":
        from geoai_data_manager import DataManager
        dm = DataManager(); found = dm.scan_directory(args.path)
        for cat, files in found.items():
            if files: print(f"\n{cat.upper()}: {len(files)} files")
            for f in files[:10]: print(f"  {f}")
    elif args.command == "index":
        from geoai_remote_sensing import RemoteSensing
        rs = RemoteSensing()
        print(f"Available: {list(rs.INDICES.keys())}")
    elif args.command == "recommend":
        from geoai_paper_agent import PaperSubmissionAgent
        agent = PaperSubmissionAgent()
        recs = agent.recommend(target_if=getattr(args, "target_if", None))
        for tier, js in recs.items():
            if js: print(f"\n{tier.upper()}:")
            for j in js: print(f"  {j[\"name\"]} (IF={j[\"if\"]}, AR={j[\"accept_rate\"]}%)")
    elif args.command == "pipeline":
        from geoai_pipeline import GeoAIPipeline
        p = GeoAIPipeline()
        wf = getattr(p, f"{args.name}_expansion_workflow", None)
        if wf: result = wf("Region", [2010, 2020])
        else: print(f"Pipeline {args.name} not found")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

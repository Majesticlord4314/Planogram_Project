#!/usr/bin/env python3
"""
Cohort Planogram Generation - Main Entry Point

This script provides a clean, dedicated entry point for generating
cohort-based planograms without interfering with the main system.

Usage:
    python cohort_planogram.py --lob iPhone --store flagship
    python cohort_planogram.py --all --store flagship
    python cohort_planogram.py --status
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Setup logging for cohort planogram generation"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_dir / "cohort_planogram.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point"""
    setup_logging()
    
    try:
        from cohort_planogram.runner import CohortPlanogramRunner
        import argparse
        
        parser = argparse.ArgumentParser(
            description='Generate Cohort-Based Planograms',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python cohort_planogram.py --lob iPhone --store flagship
  python cohort_planogram.py --lob iPad --store standard
  python cohort_planogram.py --all --store flagship
  python cohort_planogram.py --status
            """
        )
        
        parser.add_argument('--lob', choices=['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods'],
                           help='Line of Business to generate planogram for')
        parser.add_argument('--store', choices=['flagship', 'standard', 'express'],
                           default='flagship', help='Store type (default: flagship)')
        parser.add_argument('--all', action='store_true',
                           help='Generate planograms for all available LOBs')
        parser.add_argument('--status', action='store_true',
                           help='Show system status report')
        
        args = parser.parse_args()
        
        runner = CohortPlanogramRunner()
        
        if args.status:
            runner.print_status_report()
        elif args.all:
            runner.generate_all_cohort_planograms(args.store)
        elif args.lob:
            runner.generate_cohort_planogram(args.lob, args.store)
        else:
            print("Cohort Planogram Generation System")
            print("Please specify one of the following options:")
            print("  --lob [iPhone|iPad|Mac|Watch|AirPods]  Generate for specific LOB")
            print("  --all                                   Generate for all LOBs")
            print("  --status                               Show system status")
            print("\nFor detailed help: python cohort_planogram.py --help")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error in cohort planogram generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

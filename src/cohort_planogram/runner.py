"""
Cohort Planogram Runner - Main Entry Point

This module provides the main entry point for generating cohort-based planograms
for all supported LOBs (iPhone, iPad, Mac, Watch, AirPods).
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from .iphone_cohort import iPhoneCohortPlanogram
from .ipad_cohort import iPadCohortPlanogram
from .watch_cohort import WatchCohortPlanogram
from .mac_cohort import MacCohortPlanogram
from .data_loader import CohortDataLoader

class CohortPlanogramRunner:
    """Main runner for cohort-based planogram generation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_loader = CohortDataLoader()
        
        # Map LOBs to their planogram generators
        self.generators = {
            'iPhone': iPhoneCohortPlanogram,
            'iPad': iPadCohortPlanogram,
            'Watch': WatchCohortPlanogram,
            'Mac': MacCohortPlanogram,
            # 'AirPods': AirPodsCohortPlanogram # To be implemented
        }
        
        # Supported store types
        self.supported_store_types = ['flagship', 'standard', 'express']
        
        # Supported LOBs
        self.supported_lobs = ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods']
    
    def generate_cohort_planogram(self, lob: str, store_type: str = 'flagship') -> Optional[Path]:
        """Generate cohort planogram for specified LOB and store type"""
        self.logger.info(f"Starting cohort planogram generation for {lob} - {store_type}")
        
        # Validate inputs
        if not self._validate_inputs(lob, store_type):
            return None
        
        # Check if data exists for this LOB
        if not self._check_data_availability(lob):
            return None
        
        # Get the appropriate generator
        generator_class = self.generators.get(lob)
        if not generator_class:
            self.logger.error(f"No generator implemented for LOB: {lob}")
            print(f"ERROR: Cohort planogram not yet implemented for {lob}")
            print(f"Available: {list(self.generators.keys())}")
            return None
        
        try:
            # Create generator and generate planogram
            generator = generator_class()
            output_path = generator.generate_cohort_planogram(store_type)
            
            self.logger.info(f"Successfully generated cohort planogram: {output_path}")
            print(f"SUCCESS: Cohort planogram generated: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating cohort planogram: {e}", exc_info=True)
            print(f"ERROR: Error generating cohort planogram: {e}")
            return None
    
    def generate_all_cohort_planograms(self, store_type: str = 'flagship') -> Dict[str, Optional[Path]]:
        """Generate cohort planograms for all available LOBs"""
        self.logger.info(f"Generating cohort planograms for all LOBs - {store_type}")
        
        results = {}
        
        for lob in self.generators.keys():
            print(f"\nGenerating {lob} cohort planogram...")
            result = self.generate_cohort_planogram(lob, store_type)
            results[lob] = result
        
        # Summary
        successful = sum(1 for path in results.values() if path is not None)
        total = len(results)
        
        print(f"\nGeneration Summary:")
        print(f"  Successful: {successful}/{total}")
        print(f"  Output directory: output/cohort_planograms/")
        
        return results
    
    def _validate_inputs(self, lob: str, store_type: str) -> bool:
        """Validate input parameters"""
        if lob not in self.supported_lobs:
            self.logger.error(f"ERROR: Unsupported LOB: {lob}")
            print(f"ERROR: Unsupported LOB: {lob}")
            print(f"Supported LOBs: {self.supported_lobs}")
            return False
        
        if store_type not in self.supported_store_types:
            self.logger.error(f"ERROR: Unsupported store type: {store_type}")
            print(f"ERROR: Unsupported store type: {store_type}")
            print(f"Supported store types: {self.supported_store_types}")
            return False
        
        return True
    
    def _check_data_availability(self, lob: str) -> bool:
        """Check if cohort data is available for the specified LOB"""
        try:
            lob_data = self.data_loader.get_lob_data(lob)
            
            if len(lob_data) == 0:
                self.logger.error(f"ERROR: No cohort data found for LOB: {lob}")
                print(f"ERROR: No cohort data found for LOB: {lob}")
                return False
            
            # Check for minimum required data
            min_records = 10
            if len(lob_data) < min_records:
                self.logger.warning(f"WARNING: Limited cohort data for {lob}: {len(lob_data)} records")
                print(f"WARNING: Limited cohort data for {lob}: {len(lob_data)} records")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error checking data availability for {lob}: {e}")
            print(f"ERROR: Error checking data availability for {lob}: {e}")
            return False
    
    def get_available_lobs(self) -> Dict[str, Dict]:
        """Get information about available LOBs and their data"""
        available_lobs = {}
        
        for lob in self.supported_lobs:
            try:
                lob_data = self.data_loader.get_lob_data(lob)
                summary_stats = self.data_loader.get_lob_summary_stats(lob)
                
                available_lobs[lob] = {
                    'implemented': lob in self.generators,
                    'data_available': len(lob_data) > 0,
                    'record_count': len(lob_data),
                    'unique_products': summary_stats['unique_core_products'],
                    'unique_categories': summary_stats['unique_categories'],
                    'avg_attach_rate': summary_stats['avg_attach_rate']
                }
                
            except Exception as e:
                available_lobs[lob] = {
                    'implemented': lob in self.generators,
                    'data_available': False,
                    'error': str(e)
                }
        
        return available_lobs
    
    def print_status_report(self) -> None:
        """Print status report of cohort planogram system"""
        print("\n" + "="*60)
        print("COHORT PLANOGRAM SYSTEM STATUS")
        print("="*60)
        
        available_lobs = self.get_available_lobs()
        
        for lob, info in available_lobs.items():
            status = "OK" if info['implemented'] else "PENDING"
            data_status = "DATA" if info.get('data_available', False) else "NO DATA"
            
            print(f"\n{status} {lob}:")
            print(f"  Implementation: {'Ready' if info['implemented'] else 'In Progress'}")
            print(f"  Data: {data_status} {'Available' if info.get('data_available', False) else 'Not Available'}")
            
            if info.get('data_available', False):
                print(f"  Records: {info['record_count']:,}")
                print(f"  Products: {info['unique_products']}")
                print(f"  Categories: {info['unique_categories']}")
                print(f"  Avg Attach Rate: {info['avg_attach_rate']:.1%}")
        
        print(f"\nOutput Directory: output/cohort_planograms/")
        print("="*60)

def main():
    """Main entry point for cohort planogram generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Cohort-Based Planograms')
    parser.add_argument('--lob', choices=['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods'],
                       help='Line of Business to generate planogram for')
    parser.add_argument('--store', choices=['flagship', 'standard', 'express'],
                       default='flagship', help='Store type')
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
        print("Please specify --lob, --all, or --status")
        parser.print_help()

if __name__ == "__main__":
    main()

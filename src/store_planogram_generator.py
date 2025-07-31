"""
Store Planogram Generator - Integrates store selection with planogram generation
"""

import os
import sys
import json
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))

from store_wall_analyzer import StoreWallAnalyzer
from lob_distribution_engine import LOBDistributionEngine

# Import existing planogram generators
from visualization.cohort_planogram import CohortPlanogramGenerator

class StorePlanogramGenerator:
    def __init__(self):
        self.analyzer = StoreWallAnalyzer('data/raw/store_templates/Plannogram compiled_16052025.csv')
        self.distribution_engine = LOBDistributionEngine()
        self.planogram_generator = CohortPlanogramGenerator()
        
        # Product size variations
        self.product_sizes = {
            'iphone_cases': {
                'small': {'width': 60, 'height': 120},
                'medium': {'width': 70, 'height': 140}, 
                'large': {'width': 80, 'height': 160}
            },
            'ipad_cases': {
                'small': {'width': 180, 'height': 240},
                'medium': {'width': 200, 'height': 280},
                'large': {'width': 220, 'height': 300}
            },
            'mac_accessories': {
                'small': {'width': 100, 'height': 50},
                'medium': {'width': 150, 'height': 80},
                'large': {'width': 200, 'height': 100}
            },
            'bags_sleeves': {
                'small': {'width': 250, 'height': 180},
                'medium': {'width': 300, 'height': 220},
                'large': {'width': 350, 'height': 260}
            },
            'watch_bands': {
                'small': {'width': 40, 'height': 80},
                'medium': {'width': 50, 'height': 100},
                'large': {'width': 60, 'height': 120}
            }
        }
        
        # Generation modes
        self.generation_modes = {
            'LOB_WISE': 'Generate cohorts for all corresponding walls',
            'PRODUCT_WISE': 'Generate specific product categories', 
            'FULL_STORE': 'Generate complete store optimization'
        }
        
    def get_store_lob_data(self, store_name):
        """Get LOB data for a specific store"""
        try:
            with open('output/store_wall_analysis.json', 'r') as f:
                analysis_data = json.load(f)
            
            store_data = analysis_data['store_analysis'].get(store_name)
            if not store_data:
                return None
                
            return store_data
        except FileNotFoundError:
            # Generate analysis if file doesn't exist
            analysis_data = self.analyzer.save_analysis('output/store_wall_analysis.json')
            return analysis_data['store_analysis'].get(store_name)
    
    def generate_lob_planogram(self, store_name, lob_category, wall_count):
        """Generate planogram for specific LOB category"""
        
        output_dir = f"output/store_planograms/{store_name.replace(' ', '_')}/{lob_category}"
        os.makedirs(output_dir, exist_ok=True)
        
        planograms_generated = []
        
        for wall_num in range(1, wall_count + 1):
            wall_id = f"W{wall_num}"
            
            if lob_category == 'iphone_cases':
                # Generate iPhone cohort planogram
                output_file = f"{output_dir}/{wall_id}_iphone_cases.png"
                try:
                    # Use existing iPhone cohort generation with size variations
                    self._generate_iphone_cohort_with_sizes(output_file, wall_id)
                    planograms_generated.append(output_file)
                except Exception as e:
                    print(f"Error generating iPhone cases planogram for {wall_id}: {e}")
                    
            elif lob_category == 'ipad_cases':
                # Generate iPad cohort planogram
                output_file = f"{output_dir}/{wall_id}_ipad_cases.png"
                try:
                    self._generate_ipad_cohort_with_sizes(output_file, wall_id)
                    planograms_generated.append(output_file)
                except Exception as e:
                    print(f"Error generating iPad cases planogram for {wall_id}: {e}")
                    
            elif lob_category == 'mac_accessories':
                # Generate Mac accessories planogram
                output_file = f"{output_dir}/{wall_id}_mac_accessories.png"
                try:
                    self._generate_mac_cohort_with_sizes(output_file, wall_id)
                    planograms_generated.append(output_file)
                except Exception as e:
                    print(f"Error generating Mac accessories planogram for {wall_id}: {e}")
                    
            elif lob_category == 'bags_sleeves':
                # Generate bags & sleeves planogram
                output_file = f"{output_dir}/{wall_id}_bags_sleeves.png"
                try:
                    self._generate_bags_sleeves_with_sizes(output_file, wall_id)
                    planograms_generated.append(output_file)
                except Exception as e:
                    print(f"Error generating bags & sleeves planogram for {wall_id}: {e}")
                    
            elif lob_category == 'watch_bands':
                # Generate watch bands planogram
                output_file = f"{output_dir}/{wall_id}_watch_bands.png"
                try:
                    self._generate_watch_cohort_with_sizes(output_file, wall_id)
                    planograms_generated.append(output_file)
                except Exception as e:
                    print(f"Error generating watch bands planogram for {wall_id}: {e}")
        
        return planograms_generated
    
    def _generate_iphone_cohort_with_sizes(self, output_file, wall_id):
        """Generate iPhone cohort with variable sizes"""
        try:
            from src.cohort_planogram.iphone_cohort import iPhoneCohortPlanogram
            
            # Create iPhone cohort planogram with size variations
            iphone_plano = iPhoneCohortPlanogram()
            iphone_plano.create_planogram(
                store_type='flagship',
                output_path=output_file,
                wall_id=wall_id,
                product_sizes=self.product_sizes['iphone_cases']
            )
        except ImportError:
            # Fallback to basic planogram generation
            self._generate_basic_planogram(output_file, wall_id, 'iPhone Cases')
    
    def _generate_ipad_cohort_with_sizes(self, output_file, wall_id):
        """Generate iPad cohort with variable sizes"""
        try:
            from src.cohort_planogram.ipad_cohort import iPadCohortPlanogram
            
            ipad_plano = iPadCohortPlanogram()
            ipad_plano.create_planogram(
                store_type='flagship',
                output_path=output_file,
                wall_id=wall_id,
                product_sizes=self.product_sizes['ipad_cases']
            )
        except ImportError:
            self._generate_basic_planogram(output_file, wall_id, 'iPad Cases')
    
    def _generate_mac_cohort_with_sizes(self, output_file, wall_id):
        """Generate Mac accessories cohort with variable sizes"""
        self._generate_basic_planogram(output_file, wall_id, 'Mac Accessories')
        
    def _generate_bags_sleeves_with_sizes(self, output_file, wall_id):
        """Generate bags & sleeves cohort with variable sizes"""
        self._generate_basic_planogram(output_file, wall_id, 'Bags & Sleeves')
        
    def _generate_watch_cohort_with_sizes(self, output_file, wall_id):
        """Generate watch bands cohort with variable sizes"""
        try:
            from src.cohort_planogram.watch_cohort import WatchCohortPlanogram
            
            watch_plano = WatchCohortPlanogram()
            watch_plano.create_planogram(
                store_type='flagship',
                output_path=output_file,
                wall_id=wall_id,
                product_sizes=self.product_sizes['watch_bands']
            )
        except ImportError:
            self._generate_basic_planogram(output_file, wall_id, 'Watch Bands')
    
    def _generate_basic_planogram(self, output_file, wall_id, category_name):
        """Generate a basic planogram as fallback"""
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        # Title
        ax.text(50, 95, f"{category_name} Planogram - {wall_id}", 
                ha='center', va='center', fontsize=16, fontweight='bold')
        
        # Create basic grid layout with size variations
        sizes = ['small', 'medium', 'large']
        colors = ['lightblue', 'lightgreen', 'lightcoral']
        
        y_pos = 80
        for i, (size, color) in enumerate(zip(sizes, colors)):
            # Product rectangles with different sizes
            for j in range(5):  # 5 products per row
                width = 8 + i * 2  # Variable width
                height = 10 + i * 3  # Variable height
                x_pos = 10 + j * 18
                
                rect = patches.Rectangle((x_pos, y_pos - i * 20), width, height,
                                       linewidth=1, edgecolor='black', facecolor=color)
                ax.add_patch(rect)
                
                # Product label
                ax.text(x_pos + width/2, y_pos - i * 20 + height/2, 
                       f"{size.title()}\nProduct", ha='center', va='center', 
                       fontsize=8, fontweight='bold')
        
        # Legend
        ax.text(10, 25, "Size Variations:", fontsize=12, fontweight='bold')
        for i, (size, color) in enumerate(zip(sizes, colors)):
            rect = patches.Rectangle((10, 20 - i * 5), 3, 3,
                                   linewidth=1, edgecolor='black', facecolor=color)
            ax.add_patch(rect)
            ax.text(15, 21.5 - i * 5, f"{size.title()} Size", fontsize=10)
        
        ax.set_aspect('equal')
        ax.axis('off')
        plt.tight_layout()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_store_planograms(self, store_name, mode='LOB_WISE', selected_lobs=None):
        """Generate planograms for entire store based on mode"""
        store_data = self.get_store_lob_data(store_name)
        if not store_data:
            return {'error': f'Store {store_name} not found'}
        
        wall_details = store_data['wall_details']
        generated_planograms = {}
        
        if mode == 'LOB_WISE':
            # Generate all LOB categories (skip audio for now)
            for lob_category, lob_data in wall_details.items():
                if lob_category == 'audio':  # Skip audio as requested
                    continue
                    
                wall_count = lob_data.get('wall_count', 0)
                if wall_count > 0:
                    planograms = self.generate_lob_planogram(store_name, lob_category, wall_count)
                    generated_planograms[lob_category] = planograms
                    
        elif mode == 'PRODUCT_WISE' and selected_lobs:
            # Generate only selected LOB categories
            for lob_category in selected_lobs:
                if lob_category in wall_details:
                    wall_count = wall_details[lob_category].get('wall_count', 0)
                    if wall_count > 0:
                        planograms = self.generate_lob_planogram(store_name, lob_category, wall_count)
                        generated_planograms[lob_category] = planograms
                        
        elif mode == 'FULL_STORE':
            # Generate optimized layout for entire store
            recommendations = self.distribution_engine.generate_store_recommendations(
                'data/raw/store_templates/Plannogram compiled_16052025.csv'
            )
            
            store_rec = recommendations.get(store_name, {})
            optimization = store_rec.get('optimization', {})
            optimal_distribution = optimization.get('optimal_distribution', {})
            
            # Generate planograms based on optimal distribution
            for lob_category, optimal_walls in optimal_distribution.items():
                if lob_category == 'audio':  # Skip audio
                    continue
                if optimal_walls > 0:
                    planograms = self.generate_lob_planogram(store_name, lob_category, optimal_walls)
                    generated_planograms[lob_category] = planograms
        
        # Create summary report
        summary = {
            'store_name': store_name,
            'generation_mode': mode,
            'total_planograms': sum(len(planograms) for planograms in generated_planograms.values()),
            'lob_categories': list(generated_planograms.keys()),
            'planograms': generated_planograms,
            'store_data': store_data
        }
        
        # Save summary
        summary_file = f"output/store_planograms/{store_name.replace(' ', '_')}/generation_summary.json"
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return summary

def main():
    """Test the store planogram generator"""
    generator = StorePlanogramGenerator()
    
    # Test with VEGA CITY MALL
    store_name = "IMAGINE- VEGA CITY MALL BENGALURU"
    
    print(f"Generating planograms for {store_name}...")
    
    # Test LOB-wise generation
    result = generator.generate_store_planograms(
        store_name, 
        mode='LOB_WISE'
    )
    
    print(f"Generated {result['total_planograms']} planograms")
    print(f"LOB categories: {result['lob_categories']}")
    
    return result

if __name__ == "__main__":
    main()

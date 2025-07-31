#!/usr/bin/env python3
"""
Planogram Manager - Handles wall count storage and planogram generation
Manages the final wall counts after user edits and generates planograms accordingly
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from .cases_covers_generator import CasesCoversGenerator
    from .ipad_accessories_generator import IPadAccessoriesGenerator
except ImportError:
    # Handle direct execution
    from cases_covers_generator import CasesCoversGenerator
    from ipad_accessories_generator import IPadAccessoriesGenerator

logger = logging.getLogger(__name__)

class PlanogramManager:
    """Manages wall count storage and planogram generation"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.storage_path = project_root / 'data' / 'processed' / 'final_wall_configs.json'
        self.output_path = project_root / 'output'
        self.planogram_generators = self._init_generators()
        
        # Ensure directories exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def _init_generators(self) -> Dict:
        """Initialize planogram generators for different categories"""
        return {
            'Cases & Covers': CasesCoversGenerator,  # Enhanced generator
            'Mac Accessories': None,  # TODO: Add Mac generator
            'iPad Accessories': IPadAccessoriesGenerator,  # iPad generator with multi-wall support
            'Watch Accessories': None,  # TODO: Add Watch generator
            'Audio Accessories': None,  # TODO: Add Audio generator
            'Adapters & Cables': None,  # TODO: Add Adapters generator
            'Miscellaneous': None,  # TODO: Add Misc generator
        }
    
    def store_final_wall_config(self, store_name: str, wall_config: Dict[str, int]) -> bool:
        """
        Store the final wall configuration after user edits/fixes
        This becomes the authoritative source for planogram generation
        
        Args:
            store_name: Normalized store name
            wall_config: Final wall counts per LOB after all edits
            
        Returns:
            bool: Success status
        """
        try:
            # Load existing configurations
            configs = self._load_wall_configs()
            
            # Store the final configuration with timestamp
            configs[store_name] = {
                'wall_counts': wall_config,
                'total_walls': sum(wall_config.values()),
                'last_updated': datetime.now().isoformat(),
                'status': 'finalized'
            }
            
            # Save to disk
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Stored final wall config for {store_name}: {wall_config}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing wall config: {e}")
            return False
    
    def get_final_wall_config(self, store_name: str) -> Optional[Dict]:
        """
        Get the final wall configuration for a store
        
        Args:
            store_name: Normalized store name
            
        Returns:
            Dict with wall_counts, total_walls, last_updated, status
        """
        try:
            configs = self._load_wall_configs()
            return configs.get(store_name)
        except Exception as e:
            logger.error(f"Error loading wall config: {e}")
            return None
    
    def generate_planograms(self, store_name: str, store_data: Dict) -> Dict[str, Any]:
        """
        Generate planograms for all walls based on final wall configuration
        
        Args:
            store_name: Normalized store name
            store_data: Store data from store reference
            
        Returns:
            Dict with generation results
        """
        try:
            # Get final wall configuration
            final_config = self.get_final_wall_config(store_name)
            if not final_config:
                logger.warning(f"No final wall config found for {store_name}")
                return {'success': False, 'error': 'No final wall configuration found'}
            
            wall_counts = final_config['wall_counts']
            results = {
                'success': True,
                'store_name': store_name,
                'total_walls': final_config['total_walls'],
                'generated_planograms': {},
                'errors': []
            }
            
            # Generate planograms for each category
            wall_counter = 1
            for lob, count in wall_counts.items():
                if count == 0:
                    continue
                    
                try:
                    # Get store data for this LOB
                    lob_data = store_data.get('wall_details', {}).get(lob, {})
                    if not lob_data:
                        logger.warning(f"No data found for LOB: {lob}")
                        continue
                    
                    # Generate planograms for each wall in this LOB
                    lob_results = []
                    for wall_num in range(wall_counter, wall_counter + count):
                        planogram_result = self._generate_single_planogram(
                            store_name, lob, wall_num, lob_data
                        )
                        lob_results.append(planogram_result)
                    
                    results['generated_planograms'][lob] = {
                        'wall_count': count,
                        'wall_range': f"{wall_counter}-{wall_counter + count - 1}",
                        'planograms': lob_results
                    }
                    
                    wall_counter += count
                    
                except Exception as e:
                    error_msg = f"Error generating planogram for {lob}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating planograms: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_single_planogram(self, store_name: str, lob: str, wall_num: int, lob_data: Dict) -> Dict:
        """Generate a single planogram for a specific wall"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"wall{wall_num}_{lob.lower().replace(' ', '_').replace('&', 'and')}"
            
            # Check if we have a generator for this LOB
            generator_class = self.planogram_generators.get(lob)
            if not generator_class:
                logger.info(f"No specialized generator for {lob}, using generic layout")
                return self._generate_generic_planogram(store_name, lob, wall_num, lob_data, base_filename, timestamp)
            
            # Use specialized generator
            logger.info(f"Using specialized generator for {lob}")
            generator = generator_class(str(self.project_root))
            
            # Generate planogram
            planogram_path = self.output_path / f"{base_filename}_planogram_{timestamp}.png"
            details_path = self.output_path / f"{base_filename}_details_{timestamp}.txt"
            
            # Get products for this LOB - use real data for Cases & Covers and iPad Accessories
            if lob == 'Cases & Covers':
                products = self._load_real_cases_data()
                capacity = sum(p.get('total_sales', 0) for p in products)
                logger.info(f"Loaded {len(products)} real Cases & Covers products with total sales: {capacity}")
            elif lob == 'iPad Accessories':
                # Use iPad-specific multi-wall generation
                return self._generate_ipad_planograms(store_name, wall_num, lob_data, base_filename, timestamp)
            else:
                # Extract products from lob_data for other categories
                products = lob_data.get('products', [])
                capacity = lob_data.get('total_capacity', 0)
            
            # Generate the visualization
            if hasattr(generator, 'generate_planogram'):
                success = generator.generate_planogram(
                    products=products,
                    capacity=capacity,
                    output_path=str(planogram_path),
                    details_path=str(details_path),
                    wall_number=wall_num,
                    store_name=store_name
                )
            else:
                # Fallback method
                success = self._generate_generic_planogram(store_name, lob, wall_num, lob_data, base_filename, timestamp)
            
            return {
                'wall_number': wall_num,
                'lob': lob,
                'success': success,
                'planogram_path': str(planogram_path) if success else None,
                'details_path': str(details_path) if success else None,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error generating single planogram: {e}")
            return {
                'wall_number': wall_num,
                'lob': lob,
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _load_real_cases_data(self) -> List[Dict]:
        """Load real Cases & Covers data from CSV file"""
        try:
            import pandas as pd
            
            # Load Cases & Covers CSV data
            csv_path = self.project_root / 'data' / 'raw' / 'accessories' / 'cases_sales.csv'
            if not csv_path.exists():
                logger.warning(f"Cases CSV not found at {csv_path}")
                return []
            
            df = pd.read_csv(csv_path)
            df.columns = df.columns.str.strip()  # Clean column names
            
            # Filter for products with sales data and sort by sales
            df_with_sales = df[df['pureqty'].notna() & (df['pureqty'] > 0)]
            df_sorted = df_with_sales.sort_values('pureqty', ascending=False)
            
            # Convert to expected format (take top 30 products)
            products = []
            for _, row in df_sorted.head(30).iterrows():
                products.append({
                    'product': row['product_name'],
                    'brand': row['brand'].strip() if pd.notna(row['brand']) else 'Other',
                    'series': row['series'].strip() if pd.notna(row['series']) else 'General',
                    'total_sales': int(row['pureqty']),
                    'accessory_type': row['subcategory'].strip() if pd.notna(row['subcategory']) else row['category'].strip(),
                    'capacity': min(int(row['pureqty']), 200)  # Cap for display
                })
            
            logger.info(f"Loaded {len(products)} Cases & Covers products from CSV")
            return products
            
        except Exception as e:
            logger.error(f"Error loading real Cases data: {e}")
            return []
    
    def _generate_ipad_planograms(self, store_name: str, wall_num: int, lob_data: Dict, base_filename: str, timestamp: str) -> Dict:
        """Generate iPad planograms using the NEW 5-row system with no blank facings"""
        try:
            # Get iPad wall count from configuration
            final_config = self.get_final_wall_config(store_name)
            if final_config:
                ipad_wall_count = final_config['wall_counts'].get('iPad Accessories', 1)
            else:
                ipad_wall_count = 1
            
            logger.info(f"Generating {ipad_wall_count} iPad planogram(s) for {store_name} using NEW 5-row system")
            
            # Initialize iPad generator with new system
            ipad_generator = IPadAccessoriesGenerator(str(self.project_root))
            
            # Generate planograms using the new Apple/TPA strategy
            results = ipad_generator.generate_store_planograms(store_name, ipad_wall_count)
            
            # Process results for this specific wall
            wall_key = f'wall_{wall_num}'
            success = results.get(wall_key, False)
            
            # Determine actual file paths (iPad generator creates its own naming)
            store_slug = store_name.lower().replace(' ', '_')
            actual_planogram_path = f"ipad_wall_{wall_num}_{store_slug}.png"
            actual_details_path = f"ipad_wall_{wall_num}_{store_slug}_report.txt"
            
            # Check if files were actually created
            planogram_file = self.project_root / actual_planogram_path
            details_file = self.project_root / actual_details_path
            
            files_exist = planogram_file.exists() and details_file.exists()
            
            return {
                'wall_number': wall_num,
                'lob': 'iPad Accessories',
                'success': success and files_exist,
                'planogram_path': actual_planogram_path if files_exist else None,
                'details_path': actual_details_path if files_exist else None,
                'timestamp': timestamp,
                'total_ipad_walls': ipad_wall_count,
                'all_walls_generated': len([k for k, v in results.items() if v]) == ipad_wall_count,
                'grid_specs': {
                    'size': '5x4 (20 products per wall)',
                    'structure': '3 Apple rows + 2 TPA rows',
                    'no_blank_facings': True,
                    'color_diversity': 'Data-backed actual case colors'
                },
                'generation_strategy': self._get_ipad_strategy_description(ipad_wall_count)
            }
            
        except Exception as e:
            logger.error(f"Error generating iPad planograms: {e}")
            import traceback
            traceback.print_exc()
            return {
                'wall_number': wall_num,
                'lob': 'iPad Accessories',
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _get_ipad_strategy_description(self, wall_count: int) -> str:
        """Get description of iPad generation strategy based on wall count"""
        strategies = {
            1: "Single Mixed Wall: 3 Apple rows + 2 TPA rows (Gripp + others)",
            2: "Apple/TPA Split: Wall 1 Apple/TPA split, Wall 2 TPA-focused",
            3: "Multi-Wall Strategy: 2 Apple/TPA walls + 1 TPA-only wall",
            4: "Flagship Strategy: 2 Apple/TPA walls + 2 TPA-only walls"
        }
        return strategies.get(wall_count, f"{wall_count}-wall custom strategy")

    def _generate_generic_planogram(self, store_name: str, lob: str, wall_num: int, lob_data: Dict, base_filename: str, timestamp: str) -> bool:
        """Generate a generic planogram layout"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            
            # Create figure
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 8)
            ax.set_aspect('equal')
            
            # Title
            ax.text(5, 7.5, f"Wall {wall_num} - {lob}", ha='center', va='center', 
                   fontsize=16, fontweight='bold')
            ax.text(5, 7, f"Store: {store_name}", ha='center', va='center', fontsize=12)
            
            # Products
            products = lob_data.get('products', [])
            capacity = lob_data.get('total_capacity', 0)
            
            # Simple grid layout
            y_pos = 6
            ax.text(1, y_pos, f"Products ({len(products)}):", fontweight='bold')
            y_pos -= 0.3
            
            for i, product in enumerate(products[:10]):  # Show first 10 products
                product_name = product.get('product', 'Unknown Product')[:50]
                brand = product.get('brand', 'Unknown Brand')
                ax.text(1, y_pos, f"• {product_name} ({brand})", fontsize=10)
                y_pos -= 0.3
            
            if len(products) > 10:
                ax.text(1, y_pos, f"... and {len(products) - 10} more products", 
                       fontsize=10, style='italic')
            
            # Capacity info
            ax.text(1, 2, f"Total Capacity: {capacity}", fontweight='bold', fontsize=12)
            
            # Remove axes
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            # Save
            output_path = self.output_path / f"{base_filename}_planogram_{timestamp}.png"
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Generate details file
            details_path = self.output_path / f"{base_filename}_details_{timestamp}.txt"
            with open(details_path, 'w', encoding='utf-8') as f:
                f.write(f"PLANOGRAM DETAILS - Wall {wall_num}\n")
                f.write(f"Store: {store_name}\n")
                f.write(f"Category: {lob}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Products: {len(products)}\n")
                f.write(f"Total Capacity: {capacity}\n\n")
                f.write("PRODUCTS:\n")
                for product in products:
                    f.write(f"  • {product.get('product', 'Unknown')} ({product.get('brand', 'Unknown')})\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating generic planogram: {e}")
            return False
    
    def _load_wall_configs(self) -> Dict:
        """Load wall configurations from storage"""
        try:
            if not self.storage_path.exists():
                return {}
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading wall configs: {e}")
            return {}

# Global instance
planogram_manager = None

def get_planogram_manager(project_root: Path) -> PlanogramManager:
    """Get or create planogram manager instance"""
    global planogram_manager
    if planogram_manager is None:
        planogram_manager = PlanogramManager(project_root)
    return planogram_manager

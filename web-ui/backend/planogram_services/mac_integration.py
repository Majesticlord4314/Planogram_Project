"""
Mac Accessories Integration Layer
Integration layer for Mac accessories planogram generation in the web-ui system.
Provides unified interface for Mac accessories, bags & sleeves planogram generation.
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import json

from .mac_accessories_generator import MacAccessoriesGenerator
from .bags_sleeves_generator import BagsSleevesGenerator

class MacIntegration:
    """Integration layer for Mac accessories planogram generation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mac_generator = MacAccessoriesGenerator()
        self.bags_sleeves_generator = BagsSleevesGenerator()
        
        # Mac LOB configuration
        self.mac_categories = {
            'mac_accessories': 'Mac Accessories (Hubs, Chargers, Cases)',
            'bags_sleeves': 'Mac Bags & Sleeves'
        }

    def generate_mac_planograms(self, store_name: str, wall_config: Dict[str, int], 
                               selected_categories: List[str] = None) -> Dict[str, str]:
        """
        Generate Mac planograms based on store configuration
        
        Args:
            store_name: Name of the store
            wall_config: Wall configuration for Mac LOB
            selected_categories: List of selected Mac categories
            
        Returns:
            Dictionary mapping wall identifiers to output file paths
        """
        self.logger.info(f"Generating Mac planograms for {store_name}")
        
        try:
            results = {}
            
            # Get Mac wall count from configuration
            mac_walls = wall_config.get('Mac Accessories', 0)
            
            if mac_walls == 0:
                self.logger.warning(f"No Mac walls configured for {store_name}")
                return results
            
            # Determine what to generate based on selected categories
            if not selected_categories:
                selected_categories = list(self.mac_categories.keys())
            
            # Generate Mac accessories planograms
            if 'mac_accessories' in selected_categories and mac_walls >= 1:
                mac_results = self.mac_generator.generate_store_planograms(
                    store_name, mac_walls
                )
                results.update(mac_results)
                
                self.logger.info(f"Generated {len(mac_results)} Mac accessories planograms")
            
            # Generate bags & sleeves planogram (if requested and space available)
            if 'bags_sleeves' in selected_categories:
                # Bags & sleeves gets its own dedicated planogram
                bags_sleeves_path = self.bags_sleeves_generator.generate_enhanced_bags_sleeves_planogram(
                    store_name
                )
                results['bags_sleeves'] = bags_sleeves_path
                
                self.logger.info("Generated Mac bags & sleeves planogram")
            
            # Generate summary report
            self._generate_mac_summary_report(store_name, results, wall_config)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating Mac planograms: {e}")
            raise

    def get_mac_wall_recommendations(self, store_type: str = 'standard') -> Dict[str, int]:
        """Get recommended wall allocation for Mac accessories"""
        recommendations = {
            'flagship': {
                'Mac Accessories': 4,  # 4 walls for comprehensive Mac display
                'total_walls': 4
            },
            'standard': {
                'Mac Accessories': 2,  # 2 walls for standard Mac display
                'total_walls': 2
            },
            'express': {
                'Mac Accessories': 1,  # 1 wall for compact Mac display
                'total_walls': 1
            }
        }
        
        return recommendations.get(store_type, recommendations['standard'])

    def get_mac_category_info(self) -> Dict[str, Dict]:
        """Get information about Mac categories"""
        return {
            'mac_accessories': {
                'name': 'Mac Accessories',
                'description': 'Hubs, chargers, cases, cables, and peripherals',
                'wall_requirement': 'Requires 1-4 walls based on store type',
                'products': 'Hardshell cases, privacy filters, hubs, chargers, cables, stands'
            },
            'bags_sleeves': {
                'name': 'Mac Bags & Sleeves',
                'description': 'Laptop bags, sleeves, and carrying solutions',
                'wall_requirement': 'Dedicated planogram (not wall-based)',
                'products': 'Laptop sleeves, messenger bags, backpacks, cases'
            }
        }

    def validate_mac_configuration(self, wall_config: Dict[str, int]) -> Dict[str, str]:
        """Validate Mac wall configuration"""
        issues = {}
        
        mac_walls = wall_config.get('Mac Accessories', 0)
        
        if mac_walls < 1:
            issues['mac_walls'] = "At least 1 wall recommended for Mac accessories"
        elif mac_walls > 4:
            issues['mac_walls'] = "More than 4 walls may lead to sparse product distribution"
        
        return issues

    def get_mac_product_stats(self) -> Dict[str, int]:
        """Get Mac product statistics"""
        try:
            # Load Mac data from sales data
            products = self.mac_generator.get_products_from_sales_data()
            
            # Load bags & sleeves data if available
            try:
                bags_sleeves = self.bags_sleeves_generator.load_bags_sleeves_data()
                approved_bags_sleeves = self.bags_sleeves_generator.filter_approved_brands(bags_sleeves)
                bags_count = len(approved_bags_sleeves)
            except:
                bags_count = 0
            
            # Calculate statistics
            categories = set(p.category for p in products)
            brands = set(p.brand for p in products)
            
            stats = {
                'total_mac_products': len(products),
                'total_bags_sleeves': bags_count,
                'total_products': len(products) + bags_count,
                'categories': len(categories),
                'brands': len(brands),
                'avg_units_sold': int(np.mean([p.units_sold for p in products])) if products else 0
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting Mac product stats: {e}")
            return {
                'total_mac_products': 0,
                'total_bags_sleeves': 0,
                'total_products': 0,
                'categories': 0,
                'brands': 0,
                'avg_units_sold': 0
            }

    def _generate_mac_summary_report(self, store_name: str, results: Dict[str, str], 
                                   wall_config: Dict[str, int]):
        """Generate summary report for Mac planograms"""
        try:
            report_data = {
                'store_name': store_name,
                'generation_timestamp': pd.Timestamp.now().isoformat(),
                'wall_configuration': wall_config,
                'generated_planograms': list(results.keys()),
                'planogram_files': results,
                'mac_categories_generated': len(results),
                'total_walls_used': wall_config.get('Mac Accessories', 0)
            }
            
            # Add product statistics
            stats = self.get_mac_product_stats()
            report_data['product_statistics'] = stats
            
            # Save report
            report_filename = f"mac_planogram_report_{store_name.lower().replace(' ', '_')}.json"
            report_path = Path("output") / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"Generated Mac summary report: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating Mac summary report: {e}")

    def get_dimensional_analysis(self) -> Dict[str, Dict]:
        """Get dimensional analysis of Mac products for shelf planning"""
        try:
            products = self.mac_generator.get_products_from_sales_data()
            
            # Analyze dimensions by category
            analysis = {}
            
            categories = set(p.category for p in products)
            for category in categories:
                cat_products = [p for p in products if p.category == category]
                
                if cat_products:
                    analysis[category] = {
                        'count': len(cat_products),
                        'avg_width': np.mean([p.width for p in cat_products]),
                        'avg_height': np.mean([p.height for p in cat_products]),
                        'max_height': max(p.height for p in cat_products),
                        'min_height': min(p.height for p in cat_products),
                        'sales_performance': {
                            'total_units': sum(p.units_sold for p in cat_products),
                            'total_revenue': sum(p.revenue for p in cat_products),
                            'avg_market_share': np.mean([p.market_share for p in cat_products])
                        }
                    }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in dimensional analysis: {e}")
            return {}

    def get_brand_distribution(self) -> Dict[str, Dict]:
        """Get brand distribution analysis"""
        try:
            products = self.mac_generator.get_products_from_sales_data()
            
            # Analyze brand distribution
            brand_stats = {}
            
            for brand in set(p.brand for p in products):
                brand_products = [p for p in products if p.brand == brand]
                
                brand_stats[brand] = {
                    'product_count': len(brand_products),
                    'total_units_sold': sum(p.units_sold for p in brand_products),
                    'total_revenue': sum(p.revenue for p in brand_products),
                    'avg_market_share': np.mean([p.market_share for p in brand_products]),
                    'categories': list(set(p.category for p in brand_products)),
                    'priority_score': np.mean([p.priority for p in brand_products])
                }
            
            return brand_stats
            
        except Exception as e:
            self.logger.error(f"Error in brand distribution analysis: {e}")
            return {}

# Import numpy for calculations
import numpy as np
import pandas as pd

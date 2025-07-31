#!/usr/bin/env python3
"""
iPad Accessories Frontend Integration
Provides the interface between frontend wall count selection and iPad planogram generation
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from .ipad_accessories_generator import IPadAccessoriesGenerator
except ImportError:
    # Handle direct execution
    from ipad_accessories_generator import IPadAccessoriesGenerator

logger = logging.getLogger(__name__)

class OptimizedIPadIntegration:
    """
    Frontend integration class for iPad Accessories planogram generation
    Handles multi-wall generation based on frontend wall count selection
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.generator = IPadAccessoriesGenerator(project_root)
        self.output_path = self.project_root / 'output'
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_optimized_planograms(self, store_name: str, wall_count: int, 
                                    store_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate optimized iPad planograms based on wall count from frontend
        
        Args:
            store_name: Name of the store
            wall_count: Number of walls allocated to iPad Accessories (from frontend)
            store_data: Optional store-specific data
            
        Returns:
            Dict with generation results and file paths
        """
        try:
            logger.info(f"Generating {wall_count} iPad planogram(s) for {store_name}")
            
            # Generate planograms using the iPad generator
            generation_results = self.generator.generate_store_planograms(store_name, wall_count)
            
            # Process results for frontend response
            results = {
                'success': True,
                'store_name': store_name,
                'wall_count': wall_count,
                'generated_walls': [],
                'total_products': 0,
                'total_sales': 0,
                'generation_timestamp': datetime.now().isoformat()
            }
            
            # Process each generated wall
            for wall_key, success in generation_results.items():
                if success:
                    wall_number = int(wall_key.split('_')[1])
                    
                    # Determine file paths
                    planogram_file = f"ipad_wall_{wall_number}_{store_name.lower().replace(' ', '_')}.png"
                    report_file = f"ipad_wall_{wall_number}_{store_name.lower().replace(' ', '_')}_report.txt"
                    
                    wall_info = {
                        'wall_number': wall_number,
                        'success': True,
                        'planogram_path': planogram_file,
                        'report_path': report_file,
                        'wall_type': self._get_wall_type(wall_number, wall_count)
                    }
                    
                    # Try to get additional metrics from report
                    try:
                        wall_metrics = self._extract_wall_metrics(report_file)
                        wall_info.update(wall_metrics)
                        results['total_products'] += wall_metrics.get('products_count', 0)
                        results['total_sales'] += wall_metrics.get('sales_volume', 0)
                    except Exception as e:
                        logger.warning(f"Could not extract metrics for wall {wall_number}: {e}")
                    
                    results['generated_walls'].append(wall_info)
                else:
                    # Failed wall
                    wall_number = int(wall_key.split('_')[1])
                    results['generated_walls'].append({
                        'wall_number': wall_number,
                        'success': False,
                        'error': f"Failed to generate wall {wall_number}"
                    })
            
            # Sort walls by number
            results['generated_walls'].sort(key=lambda x: x['wall_number'])
            
            # Calculate success rate
            successful_walls = len([w for w in results['generated_walls'] if w['success']])
            results['success_rate'] = (successful_walls / wall_count) * 100 if wall_count > 0 else 0
            results['all_walls_successful'] = successful_walls == wall_count
            
            logger.info(f"Generated {successful_walls}/{wall_count} iPad planograms successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in iPad planogram generation: {e}")
            return {
                'success': False,
                'error': str(e),
                'store_name': store_name,
                'wall_count': wall_count,
                'generation_timestamp': datetime.now().isoformat()
            }
    
    def _get_wall_type(self, wall_number: int, total_walls: int) -> str:
        """Determine the type/purpose of each wall"""
        if total_walls == 1:
            return "Premium & Volume"
        elif total_walls == 2:
            return "Premium" if wall_number == 1 else "Volume"
        else:
            if wall_number == 1:
                return "Premium"
            elif wall_number == total_walls:
                return "Specialty"
            else:
                return "Volume"
    
    def _extract_wall_metrics(self, report_file: str) -> Dict[str, Any]:
        """Extract metrics from wall report file"""
        try:
            report_path = self.output_path / report_file
            if not report_path.exists():
                return {}
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            metrics = {}
            
            # Extract basic metrics using simple parsing
            lines = content.split('\n')
            for line in lines:
                if 'Filled Positions:' in line:
                    try:
                        metrics['products_count'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Total Sales Volume:' in line:
                    try:
                        metrics['sales_volume'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Utilization:' in line:
                    try:
                        util_str = line.split(':')[1].strip().replace('%', '')
                        metrics['utilization'] = float(util_str)
                    except:
                        pass
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error extracting metrics from {report_file}: {e}")
            return {}
    
    def get_wall_configuration_options(self) -> Dict[str, Any]:
        """
        Get available wall configuration options for iPad Accessories
        Used by frontend to show wall count options
        """
        return {
            'category': 'iPad Accessories',
            'min_walls': 1,
            'max_walls': 4,
            'recommended_walls': 2,
            'wall_configurations': {
                1: {
                    'description': 'Single Mixed Wall',
                    'capacity': '20 products',
                    'focus': '3 Apple rows + 2 TPA rows (Gripp + others)',
                    'suitable_for': 'Express stores, limited space'
                },
                2: {
                    'description': 'Apple/TPA Split Strategy',
                    'capacity': '40 products',
                    'focus': 'Wall 1: Apple/TPA split, Wall 2: TPA-focused',
                    'suitable_for': 'Standard stores, balanced selection'
                },
                3: {
                    'description': 'Multi-Wall Apple/TPA Strategy',
                    'capacity': '60 products',
                    'focus': '2 Apple/TPA walls + 1 TPA-only wall',
                    'suitable_for': 'Large stores, full product range'
                },
                4: {
                    'description': 'Flagship Apple/TPA Configuration',
                    'capacity': '80 products',
                    'focus': '2 Apple/TPA walls + 2 TPA-only walls',
                    'suitable_for': 'Flagship stores, maximum TPA selection'
                }
            },
            'grid_specifications': {
                'grid_size': '5×4 (20 products per wall)',
                'dedicated_columns': 'Mini, Base, Air, Pro',
                'row_structure': '3 Apple + 2 TPA per wall',
                'color_diversity': 'Data-backed actual case colors',
                'no_blank_facings': 'Guaranteed 100% fill rate'
            }
        }
    
    def validate_wall_count(self, wall_count: int) -> Dict[str, Any]:
        """Validate the requested wall count"""
        config_options = self.get_wall_configuration_options()
        min_walls = config_options['min_walls']
        max_walls = config_options['max_walls']
        
        if wall_count < min_walls:
            return {
                'valid': False,
                'error': f'Minimum {min_walls} wall required for iPad Accessories',
                'suggested': min_walls
            }
        elif wall_count > max_walls:
            return {
                'valid': False,
                'error': f'Maximum {max_walls} walls supported for iPad Accessories',
                'suggested': max_walls
            }
        else:
            return {
                'valid': True,
                'configuration': config_options['wall_configurations'][wall_count]
            }
    
    def get_generation_status(self, store_name: str) -> Dict[str, Any]:
        """Get the current generation status for a store"""
        try:
            # Check for existing planogram files
            store_slug = store_name.lower().replace(' ', '_')
            existing_files = list(self.output_path.glob(f"ipad_wall_*_{store_slug}.png"))
            
            if not existing_files:
                return {
                    'status': 'not_generated',
                    'message': 'No iPad planograms found for this store'
                }
            
            # Parse wall numbers from filenames
            wall_numbers = []
            for file_path in existing_files:
                try:
                    filename = file_path.name
                    wall_num = int(filename.split('_')[2])
                    wall_numbers.append(wall_num)
                except:
                    continue
            
            wall_numbers.sort()
            
            return {
                'status': 'generated',
                'wall_count': len(wall_numbers),
                'walls': wall_numbers,
                'last_generated': max(f.stat().st_mtime for f in existing_files),
                'files': [f.name for f in existing_files]
            }
            
        except Exception as e:
            logger.error(f"Error checking generation status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Compatibility alias for existing integrations
IPadAccessoriesIntegration = OptimizedIPadIntegration
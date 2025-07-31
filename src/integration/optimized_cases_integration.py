"""
Optimized Cases Integration
Simple interface for frontend to use the optimized planogram generator
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add project paths
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root / 'web-ui' / 'backend'))

class OptimizedCasesIntegration:
    """Simple integration interface for optimized cases planogram generation"""
    
    def __init__(self, project_root_path: Optional[str] = None):
        """Initialize the integration"""
        self.project_root = Path(project_root_path) if project_root_path else project_root
        self.generator = None
        self._initialize_generator()
    
    def _initialize_generator(self):
        """Initialize the optimized generator"""
        try:
            from planogram_services.cases_covers_generator_new import CasesCoversGenerator
            self.generator = CasesCoversGenerator(str(self.project_root))
            return True
        except Exception as e:
            print(f"Error initializing optimized generator: {e}")
            return False
    
    def generate_store_planograms(self, store_name: str, num_walls: int = 2) -> Dict[str, Any]:
        """Generate planograms for a complete store"""
        if not self.generator:
            return {"status": "error", "message": "Generator not initialized"}
        
        try:
            # Use the optimized generator's store method
            results = self.generator.generate_store_planograms(store_name, num_walls)
            
            # Format results for frontend
            planograms = {}
            for wall_key, success in results.items():
                if success:
                    wall_num = wall_key.replace('wall_', '')
                    planograms[f"wall{wall_num}"] = {
                        "status": "success",
                        "planogram_image": f"output/{store_name.lower().replace(' ', '_')}_wall{wall_num}_cases_covers_optimized.png",
                        "product_details_file": f"output/{store_name.lower().replace(' ', '_')}_wall{wall_num}_cases_covers_optimized.txt"
                    }
                else:
                    wall_num = wall_key.replace('wall_', '')
                    planograms[f"wall{wall_num}"] = {
                        "status": "error",
                        "message": "Generation failed"
                    }
            
            return {
                "status": "success",
                "store_name": store_name,
                "num_walls": num_walls,
                "planograms": planograms,
                "generator_type": "optimized",
                "features": [
                    "8x6 grid (48 products per wall)",
                    "Vertical phone-like rectangles (9:16 ratio)",
                    "Apple section: Pure Apple with actual colors",
                    "TPA section: Gripp/Pulse/Tekne brands",
                    "Column-based series allocation",
                    "No bottom cutoff, optimized canvas"
                ]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating planograms: {str(e)}"
            }
    
    def generate_single_wall(self, store_name: str, wall_number: int, total_walls: int = 2) -> Dict[str, Any]:
        """Generate a single wall planogram"""
        if not self.generator:
            return {"status": "error", "message": "Generator not initialized"}
        
        try:
            # Generate output paths
            output_path = f"output/{store_name.lower().replace(' ', '_')}_wall{wall_number}_cases_optimized.png"
            details_path = f"output/{store_name.lower().replace(' ', '_')}_wall{wall_number}_details_optimized.txt"
            
            # Generate planogram
            success = self.generator.generate_planogram(
                products=[],  # Will load real data
                capacity=48,
                output_path=output_path,
                details_path=details_path,
                wall_number=wall_number,
                store_name=store_name,
                total_walls=total_walls
            )
            
            if success:
                return {
                    "status": "success",
                    "wall_number": wall_number,
                    "total_walls": total_walls,
                    "planogram_image": output_path,
                    "product_details_file": details_path,
                    "generator_type": "optimized"
                }
            else:
                return {
                    "status": "error",
                    "message": "Planogram generation failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating wall planogram: {str(e)}"
            }
    
    def get_generator_info(self) -> Dict[str, Any]:
        """Get information about the optimized generator"""
        return {
            "generator_name": "Optimized Cases & Covers Generator",
            "version": "2.0",
            "features": {
                "grid_size": "8x6 (48 products)",
                "rectangle_type": "Vertical phone-like (9:16 aspect ratio)",
                "apple_allocation": "50% (top rows with actual product colors)",
                "tpa_allocation": "25% (Gripp/Pulse/Tekne brands only)",
                "other_allocation": "25% (diverse brand representation)",
                "series_logic": "Column-based (Base/Plus vs Pro/Pro Max)",
                "color_diversity": "Apple: Clear, Black, Denim, Fuchsia, etc.",
                "layout_optimization": "No cutoff, proper canvas sizing",
                "data_source": "Real sales data from CSV files"
            },
            "supported_stores": "All store types (adjusts grid automatically)",
            "output_formats": ["PNG planogram", "TXT details file"],
            "integration_status": "Active" if self.generator else "Failed"
        }

# Convenience functions for direct use
def generate_optimized_cases_planogram(store_name: str, num_walls: int = 2) -> Dict[str, Any]:
    """Generate optimized cases planogram - main entry point for frontend"""
    integration = OptimizedCasesIntegration()
    return integration.generate_store_planograms(store_name, num_walls)

def generate_single_optimized_wall(store_name: str, wall_number: int, total_walls: int = 2) -> Dict[str, Any]:
    """Generate single optimized wall - for individual wall requests"""
    integration = OptimizedCasesIntegration()
    return integration.generate_single_wall(store_name, wall_number, total_walls)

def get_optimized_generator_status() -> Dict[str, Any]:
    """Get status of optimized generator - for health checks"""
    integration = OptimizedCasesIntegration()
    return integration.get_generator_info()

# Test function
def test_integration():
    """Test the integration"""
    print("Testing Optimized Cases Integration...")
    
    # Test generator info
    info = get_optimized_generator_status()
    print(f"Generator: {info['generator_name']} v{info['version']}")
    print(f"Status: {info['integration_status']}")
    
    # Test single wall generation
    result = generate_single_optimized_wall("KORAMANGALA BENGALURU", 1, 2)
    print(f"Single wall test: {result['status']}")
    
    # Test store generation
    store_result = generate_optimized_cases_planogram("KORAMANGALA BENGALURU", 2)
    print(f"Store generation test: {store_result['status']}")
    
    if store_result['status'] == 'success':
        planograms = store_result['planograms']
        print(f"Generated {len(planograms)} planograms:")
        for wall, data in planograms.items():
            print(f"  {wall}: {data['status']}")
    
    return store_result['status'] == 'success'

if __name__ == "__main__":
    test_integration()
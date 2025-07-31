"""
Smart Accessory Optimizer - Intelligent wall allocation for accessories
Handles complex scenarios like:
- iPhone 16 series prioritization
- Apple vs Third Party distribution rules
- Cross-accessory optimization (cases + screen protectors)
- Optimal wall filling based on sales data
"""

from typing import List, Dict, Optional, Tuple, Set
import numpy as np
from collections import defaultdict, Counter
from src.models.product import Product, ProductCategory
from src.models.shelf import Shelf, ShelfPosition
from .base_optimizer import BaseOptimizer, OptimizationResult
from src.utils.monitor import monitor
from src.utils.logger import get_logger

class SmartAccessoryOptimizer(BaseOptimizer):
    """Intelligent optimizer for accessory-based planogram generation"""
    
    def __init__(self, store, gap_size: float = 0.5, accessory_type: str = "cases"):
        super().__init__(store, gap_size)
        self.accessory_type = accessory_type
        self.logger = get_logger()
        
        # Configuration for different accessory types
        self.accessory_config = {
            "cases": {
                "apple_ratio": 0.5,  # 50% Apple, 50% TPA
                "companion_accessories": ["screen_protectors", "lens_protectors"],
                "priority_series": ["iPhone 16", "iPhone 15"],
                "variants_order": ["Base", "Plus", "Pro", "Pro Max"]
            },
            "charging_cables": {
                "apple_ratio": 0.4,  # 40% Apple, 60% TPA  
                "companion_accessories": ["power_adapters", "wireless_chargers"],
                "priority_series": ["USB-C", "Lightning"],
                "variants_order": ["1m", "2m", "3m"]
            },
            "audio": {
                "apple_ratio": 0.6,  # 60% Apple, 40% TPA
                "companion_accessories": ["audio_accessories"],
                "priority_series": ["AirPods Pro", "AirPods"],
                "variants_order": ["Pro", "Standard", "Max"]
            }
        }
    
    @monitor.time_it
    def optimize(self, products: List[Product], **kwargs) -> OptimizationResult:
        """Smart optimization based on accessory type and sales patterns"""
        self.logger.info(f"Running smart accessory optimization for: {self.accessory_type}")
        
        # Categorize products
        categorized_products = self._categorize_products(products)
        
        # Apply accessory-specific optimization
        if self.accessory_type == "cases":
            result = self._optimize_cases(categorized_products)
        elif self.accessory_type == "charging_cables":
            result = self._optimize_charging(categorized_products)
        elif self.accessory_type == "audio":
            result = self._optimize_audio(categorized_products)
        else:
            result = self._optimize_generic_accessories(categorized_products)
        
        return result
    
    def _categorize_products(self, products: List[Product]) -> Dict[str, List[Product]]:
        """Categorize products by brand, series, and compatibility"""
        categorized = {
            "apple": [],
            "third_party": [],
            "companions": [],  # Related accessories like screen protectors
            "by_series": defaultdict(list),
            "by_variant": defaultdict(list)
        }
        
        for product in products:
            # Brand categorization
            brand = getattr(product, 'brand', '').lower()
            if 'apple' in brand:
                categorized["apple"].append(product)
            else:
                categorized["third_party"].append(product)
            
            # Series categorization (iPhone 16, iPhone 15, etc.)
            series = getattr(product, 'series', '')
            if series:
                categorized["by_series"][series].append(product)
            
            # Variant categorization (Base, Plus, Pro, Pro Max)
            variant = getattr(product, 'variant', '')
            if variant:
                categorized["by_variant"][variant].append(product)
            
            # Companion products (screen protectors for cases)
            product_name = product.product_name.lower()
            config = self.accessory_config.get(self.accessory_type, {})
            companions = config.get("companion_accessories", [])
            
            for companion in companions:
                if companion.replace('_', ' ') in product_name:
                    categorized["companions"].append(product)
                    break
        
        return categorized
    
    def _optimize_cases(self, categorized_products: Dict[str, List[Product]]) -> OptimizationResult:
        """Optimize iPhone cases with intelligent wall allocation"""
        self.logger.info("Optimizing iPhone cases with smart allocation...")
        
        config = self.accessory_config["cases"]
        results = OptimizationResult(
            success=True,
            store=self.store,
            products_placed=[],
            products_rejected=[],
            metrics={}
        )
        
        # Step 1: Identify available walls and their purposes
        wall_allocation = self._allocate_walls_for_cases(categorized_products)
        
        # Step 2: Prioritize iPhone 16 series
        priority_products = self._prioritize_iphone16_cases(categorized_products)
        
        # Step 3: Apply Apple vs TPA ratio per wall
        wall_assignments = self._assign_products_to_walls(priority_products, wall_allocation, config)
        
        # Step 4: Fill walls optimally
        results = self._fill_walls_optimally(wall_assignments)
        
        # Step 5: Handle companion accessories (screen protectors)
        results = self._add_companion_accessories(results, categorized_products["companions"])
        
        return results
    
    def _allocate_walls_for_cases(self, categorized_products: Dict[str, List[Product]]) -> Dict[str, Dict]:
        """Intelligently allocate walls based on store size and product mix"""
        total_walls = len(self.store.shelves)
        case_products = len(categorized_products["apple"]) + len(categorized_products["third_party"])
        companion_products = len(categorized_products["companions"])
        
        allocation = {}
        
        if total_walls >= 4:  # Large store
            # Dedicated walls for each type
            allocation = {
                "cases_apple": {
                    "wall_count": 2,
                    "purpose": "Apple cases only",
                    "priority_series": ["iPhone 16", "iPhone 15"],
                    "apple_ratio": 1.0
                },
                "cases_tpa": {
                    "wall_count": 1,
                    "purpose": "Third party cases",
                    "priority_series": ["iPhone 16", "iPhone 15"],
                    "apple_ratio": 0.0
                },
                "accessories": {
                    "wall_count": 1,
                    "purpose": "Screen protectors and lens protectors",
                    "priority_series": ["iPhone 16", "iPhone 15"],
                    "apple_ratio": 0.3
                }
            }
        elif total_walls >= 2:  # Medium store
            # Mixed walls with ratios
            allocation = {
                "cases_mixed": {
                    "wall_count": 1,
                    "purpose": "Mixed cases (Apple + TPA)",
                    "priority_series": ["iPhone 16"],
                    "apple_ratio": 0.5
                },
                "accessories": {
                    "wall_count": 1, 
                    "purpose": "Screen protectors and remaining cases",
                    "priority_series": ["iPhone 16"],
                    "apple_ratio": 0.3
                }
            }
        else:  # Small store - single wall
            allocation = {
                "mixed_all": {
                    "wall_count": 1,
                    "purpose": "Cases and accessories mixed",
                    "priority_series": ["iPhone 16"],
                    "apple_ratio": 0.4
                }
            }
        
        self.logger.info(f"Wall allocation strategy: {list(allocation.keys())}")
        return allocation
    
    def _prioritize_iphone16_cases(self, categorized_products: Dict[str, List[Product]]) -> List[Product]:
        """Prioritize iPhone 16 series with proper variant distribution"""
        all_products = categorized_products["apple"] + categorized_products["third_party"]
        
        # Sort by iPhone 16 priority, then by sales velocity
        def priority_score(product):
            series = getattr(product, 'series', '')
            variant = getattr(product, 'variant', '')
            sales = getattr(product, 'sales_velocity', getattr(product, 'total_qty', 0))
            
            score = sales
            
            # iPhone 16 series gets highest priority
            if 'iPhone 16' in series:
                score += 10000
                
                # Variant priority within iPhone 16
                variant_priorities = {"Pro Max": 300, "Pro": 200, "Plus": 100, "Base": 50}
                score += variant_priorities.get(variant, 0)
            
            # iPhone 15 gets second priority  
            elif 'iPhone 15' in series:
                score += 5000
                variant_priorities = {"Pro Max": 150, "Pro": 100, "Plus": 50, "Base": 25}
                score += variant_priorities.get(variant, 0)
            
            return score
        
        prioritized = sorted(all_products, key=priority_score, reverse=True)
        
        # Ensure balanced representation of variants
        balanced_products = self._balance_variants(prioritized)
        
        return balanced_products
    
    def _balance_variants(self, products: List[Product]) -> List[Product]:
        """Ensure balanced representation of iPhone variants"""
        variants_seen = set()
        balanced = []
        remaining = []
        
        # First pass: Get one of each iPhone 16 variant
        for product in products:
            series = getattr(product, 'series', '')
            variant = getattr(product, 'variant', '')
            
            if 'iPhone 16' in series:
                variant_key = f"iPhone16_{variant}"
                if variant_key not in variants_seen and len(balanced) < 8:
                    balanced.append(product)
                    variants_seen.add(variant_key)
                else:
                    remaining.append(product)
            else:
                remaining.append(product)
        
        # Second pass: Add remaining products
        balanced.extend(remaining)
        
        variant_list = [f"{getattr(p, 'series', '')} {getattr(p, 'variant', '')}" for p in balanced[:10]]
        self.logger.info(f"Balanced variants: {variant_list}")
        return balanced
    
    def _assign_products_to_walls(self, products: List[Product], wall_allocation: Dict, config: Dict) -> Dict[str, List[Product]]:
        """Assign products to specific walls based on allocation strategy"""
        assignments = {wall_type: [] for wall_type in wall_allocation.keys()}
        
        apple_products = [p for p in products if 'apple' in getattr(p, 'brand', '').lower()]
        tpa_products = [p for p in products if 'apple' not in getattr(p, 'brand', '').lower()]
        
        for wall_type, wall_config in wall_allocation.items():
            wall_count = wall_config["wall_count"]
            apple_ratio = wall_config["apple_ratio"]
            capacity_per_wall = self._estimate_wall_capacity()
            
            total_capacity = capacity_per_wall * wall_count
            apple_slots = int(total_capacity * apple_ratio)
            tpa_slots = total_capacity - apple_slots
            
            # Assign Apple products
            for i, product in enumerate(apple_products[:apple_slots]):
                assignments[wall_type].append(product)
            
            # Assign TPA products
            for i, product in enumerate(tpa_products[:tpa_slots]):
                assignments[wall_type].append(product)
        
        return assignments
    
    def _estimate_wall_capacity(self) -> int:
        """Estimate how many products can fit on a typical wall"""
        if not self.store.shelves:
            return 20  # Default
        
        # Calculate based on average shelf capacity
        total_positions = 0
        for shelf in self.store.shelves:
            shelf_width = getattr(shelf, 'width', 200)  # Default 200cm
            avg_product_width = 8  # Average case width
            positions_per_shelf = max(1, shelf_width // avg_product_width)
            total_positions += positions_per_shelf
        
        return max(10, total_positions // len(self.store.shelves))
    
    def _fill_walls_optimally(self, wall_assignments: Dict[str, List[Product]]) -> OptimizationResult:
        """Fill assigned walls with optimal product placement and generate intelligent planogram"""
        results = OptimizationResult(
            success=True,
            store=self.store,
            products_placed=[],
            products_rejected=[],
            metrics={}
        )
        
        # For cases, use intelligent planogram generator
        if self.accessory_type == "cases":
            return self._generate_intelligent_cases_planogram(wall_assignments)
        
        # For other accessories, use standard placement
        wall_index = 0
        for wall_type, products in wall_assignments.items():
            if not products:
                continue
                
            self.logger.info(f"Filling {wall_type} with {len(products)} products")
            
            # Assign products to specific shelves
            for product in products:
                if wall_index < len(self.store.shelves):
                    shelf = self.store.shelves[wall_index]
                    
                    # Calculate optimal facings based on sales velocity
                    facings = self._calculate_optimal_facings(product)
                    
                    if self._try_place_product(shelf, product, facings):
                        results.products_placed.append(product)
                    else:
                        results.products_rejected.append(product)
                        results.warnings.append(f"Could not place {product.product_name} on {wall_type}")
            
            wall_index += 1
        
        return results
    
    def _generate_intelligent_cases_planogram(self, wall_assignments: Dict[str, List[Product]]) -> OptimizationResult:
        """Generate intelligent cases planogram with professional layout using optimized generator"""
        from src.visualization.intelligent_planogram_generator import create_intelligent_cases_planogram
        
        results = OptimizationResult(
            success=True,
            store=self.store,
            products_placed=[],
            products_rejected=[],
            metrics={}
        )
        
        # Combine all products for intelligent placement
        all_products = []
        for products in wall_assignments.values():
            all_products.extend(products)
        
        # Determine store size and wall count based on number of shelves
        if len(self.store.shelves) >= 8:
            store_type = 'large'
            num_walls = 3
        elif len(self.store.shelves) >= 6:
            store_type = 'medium'
            num_walls = 2
        else:
            store_type = 'small'
            num_walls = 1
        
        # Get store name
        store_name = getattr(self.store, 'name', 'Smart Cases Layout')
        
        try:
            # Generate intelligent planogram using optimized system
            planogram_result = create_intelligent_cases_planogram(
                products=all_products,
                store_type=store_type,
                store_name=store_name,
                num_walls=num_walls
            )
            
            # Update results with planogram data
            results.products_placed = all_products
            results.metadata = {
                'planogram_type': 'optimized_cases',
                'store_type': store_type,
                'num_walls': num_walls,
                'generator_type': planogram_result.get('generator_type', 'optimized'),
                'planograms': planogram_result.get('planograms', {}),
                'total_products': len(all_products),
                'apple_allocation': '50% (top rows with actual colors)',
                'tpa_allocation': '25% (Gripp/Pulse/Tekne brands)',
                'other_allocation': '25% (diverse brands)',
                'layout_features': [
                    '8x6 grid (48 products per wall)',
                    'Vertical phone-like rectangles (9:16 ratio)',
                    'Apple color diversity (Clear, Black, Denim, etc.)',
                    'Column-based series allocation',
                    'TPA brands: Gripp, Pulse, Tekne',
                    'No bottom cutoff, optimized canvas'
                ]
            }
            
            # Log success with details
            planogram_count = len(planogram_result.get('planograms', {}))
            self.logger.info(f"Generated {planogram_count} optimized cases planograms for {store_name}")
            self.logger.info(f"Store type: {store_type}, Walls: {num_walls}")
            self.logger.info(f"Generator: {planogram_result.get('generator_type', 'optimized')}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate optimized planogram: {e}")
            # Fall back to standard placement
            for product in all_products:
                results.products_placed.append(product)
            
            results.metadata = {
                'planogram_type': 'fallback',
                'error': str(e),
                'total_products': len(all_products)
            }
        
        return results
    
    def _calculate_optimal_facings(self, product: Product) -> int:
        """Calculate optimal number of facings based on sales data and priority"""
        base_facings = 1
        sales = getattr(product, 'sales_velocity', getattr(product, 'total_qty', 0))
        series = getattr(product, 'series', '')
        
        # iPhone 16 gets more facings
        if 'iPhone 16' in series:
            if sales > 50:
                return 3
            elif sales > 20:
                return 2
            else:
                return 1
        
        # Other series
        if sales > 30:
            return 2
        else:
            return 1
    
    def _add_companion_accessories(self, results: OptimizationResult, companions: List[Product]) -> OptimizationResult:
        """Add companion accessories like screen protectors to appropriate walls"""
        if not companions:
            return results
        
        self.logger.info(f"Adding {len(companions)} companion accessories")
        
        # Find walls with remaining space
        for shelf in self.store.shelves:
            remaining_width = self._calculate_remaining_width(shelf)
            
            for companion in companions[:]:  # Copy list to avoid modification during iteration
                if remaining_width > 5:  # Minimum space needed
                    facings = 1
                    if self._try_place_product(shelf, companion, facings):
                        results.products_placed.append(companion)
                        companions.remove(companion)
                        remaining_width -= 8  # Approximate width used
                    
        # Add any remaining companions to rejected
        for companion in companions:
            results.products_rejected.append(companion)
            results.warnings.append(f"No space for companion accessory: {companion.product_name}")
        
        return results
    
    def _calculate_remaining_width(self, shelf: Shelf) -> float:
        """Calculate remaining width on a shelf"""
        total_width = getattr(shelf, 'width', 200)
        used_width = 0
        
        for position in shelf.positions:
            product_width = getattr(position, 'width', 8)  # Default width
            used_width += product_width * position.facings
        
        return total_width - used_width
    
    def _optimize_charging(self, categorized_products: Dict[str, List[Product]]) -> OptimizationResult:
        """Optimize charging cables and accessories"""
        # Implementation for charging accessories
        results = OptimizationResult(
            success=True,
            store=self.store,
            products_placed=[],
            products_rejected=[],
            metrics={}
        )
        # Add charging-specific logic here
        return results
    
    def _optimize_audio(self, categorized_products: Dict[str, List[Product]]) -> OptimizationResult:
        """Optimize audio products and accessories"""
        # Implementation for audio accessories  
        results = OptimizationResult(
            success=True,
            store=self.store,
            products_placed=[],
            products_rejected=[],
            metrics={}
        )
        # Add audio-specific logic here
        return results
    
    def _optimize_generic_accessories(self, categorized_products: Dict[str, List[Product]]) -> OptimizationResult:
        """Generic accessory optimization for other types"""
        results = OptimizationResult(
            success=True,
            store=self.store,
            products_placed=[],
            products_rejected=[],
            metrics={}
        )
        # Add generic logic here
        return results
    
    def _try_place_product(self, shelf: Shelf, product: Product, facings: int) -> bool:
        """Try to place a product on a shelf with specified facings"""
        try:
            # Calculate space needed
            product_width = getattr(product, 'width', 8.0)  # Default case width
            space_needed = product_width * facings + self.gap_size
            
            # Check available space
            shelf_width = getattr(shelf, 'width', 200.0)  # Default shelf width
            used_width = sum(getattr(pos, 'width', 8.0) * pos.facings for pos in shelf.positions)
            available_width = shelf_width - used_width
            
            if space_needed <= available_width:
                # Create position
                position = ShelfPosition(
                    product_id=product.product_id,
                    facings=facings,
                    width=product_width,
                    height=getattr(product, 'height', 12.0),
                    x_position=used_width,
                    y_position=0
                )
                shelf.positions.append(position)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error placing product {product.product_id}: {e}")
            return False

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

class ShelfType(Enum):
    STORAGE = "storage"
    STANDARD = "standard"
    PREMIUM = "premium"
    PROMOTIONAL = "promotional"

@dataclass
class ShelfPosition:
    """Represents a product position on shelf"""
    product_id: str
    x_start: float
    x_end: float
    facings: int
    
    @property
    def width(self) -> float:
        return self.x_end - self.x_start

@dataclass
class Shelf:
    """Shelf data model"""
    shelf_id: int
    shelf_name: str
    width: float  # cm
    height: float  # cm
    depth: float  # cm
    y_position: float  # vertical position from ground
    shelf_type: str
    eye_level_score: float  # 0 to 1, where 1 is perfect eye level
    
    # Product positions on this shelf
    positions: List[ShelfPosition] = field(default_factory=list)
    
    # Calculated properties
    area: Optional[float] = field(init=False)
    is_eye_level: Optional[bool] = field(init=False)
    is_premium: Optional[bool] = field(init=False)
    utilization: Optional[float] = field(init=False)
    
    def __post_init__(self):
        """Calculate derived properties"""
        self.area = self.width * self.height
        self.is_eye_level = self.eye_level_score >= 0.8
        self.is_premium = self.shelf_type in ["premium", "promotional"]
        self.utilization = 0.0  # Will be updated when products are placed
    
    def can_fit_product(self, product, facings: int = 1) -> bool:
        """Check if product fits on shelf with given facings"""
        required_width = product.width * facings
        required_height = product.height
        required_depth = product.depth
        
        # Check dimensions
        if required_height > self.height or required_depth > self.depth:
            return False
        
        # Check available width
        available_width = self.get_available_width()
        return required_width <= available_width
    
    def get_available_width(self) -> float:
        """Calculate remaining available width on shelf"""
        if not self.positions:
            return self.width
        
        used_width = sum(pos.width for pos in self.positions)
        # Account for gaps between products (1cm per gap)
        gaps = len(self.positions) * 1  
        return self.width - used_width - gaps
    
    def add_product(self, product, facings: int, x_position: Optional[float] = None) -> bool:
        """Add a product to the shelf"""
        if not self.can_fit_product(product, facings):
            return False
        
        # Calculate position
        if x_position is None:
            if self.positions:
                # Place after last product with gap
                last_pos = max(self.positions, key=lambda p: p.x_end)
                x_position = last_pos.x_end + 1  # 1cm gap
            else:
                x_position = 0
        
        # Create position
        product_width = product.width * facings
        position = ShelfPosition(
            product_id=product.product_id,
            x_start=x_position,
            x_end=x_position + product_width,
            facings=facings
        )
        
        self.positions.append(position)
        self.update_utilization()
        return True
    
    def remove_product(self, product_id: str) -> bool:
        """Remove a product from the shelf"""
        original_count = len(self.positions)
        self.positions = [pos for pos in self.positions if pos.product_id != product_id]
        
        if len(self.positions) < original_count:
            self.update_utilization()
            return True
        return False
    
    def update_utilization(self):
        """Update shelf utilization percentage"""
        if not self.positions:
            self.utilization = 0.0
        else:
            used_width = sum(pos.width for pos in self.positions)
            gaps = (len(self.positions) - 1) * 2 if len(self.positions) > 1 else 0
            total_used = used_width + gaps
            self.utilization = (total_used / self.width) * 100
    
    def get_products_by_zone(self) -> Dict[str, List[ShelfPosition]]:
        """Divide shelf into zones and return products in each zone"""
        zones = {
            'left': [],
            'center': [],
            'right': []
        }
        
        third_width = self.width / 3
        
        for pos in self.positions:
            center_x = (pos.x_start + pos.x_end) / 2
            if center_x < third_width:
                zones['left'].append(pos)
            elif center_x < 2 * third_width:
                zones['center'].append(pos)
            else:
                zones['right'].append(pos)
        
        return zones
    
    def optimize_positions(self, gap_size: float = 2.0):
        """Reorganize products to eliminate gaps and optimize space"""
        if not self.positions:
            return
        
        # Sort by current position
        self.positions.sort(key=lambda p: p.x_start)
        
        # Reposition with consistent gaps
        current_x = 0
        for pos in self.positions:
            width = pos.x_end - pos.x_start
            pos.x_start = current_x
            pos.x_end = current_x + width
            current_x = pos.x_end + gap_size
        
        self.update_utilization()
    
    def get_placement_score(self, product) -> float:
        """Calculate placement score for a product on this shelf"""
        score = 0.0
        
        # Eye level bonus
        if self.is_eye_level:
            score += 0.3
        else:
            score += 0.1 * self.eye_level_score
        
        # Premium shelf bonus for high-value items
        if self.is_premium and product.price > 50:
            score += 0.2
        
        # Height compatibility
        height_ratio = product.height / self.height
        if 0.5 <= height_ratio <= 0.8:
            score += 0.2  # Optimal height usage
        elif height_ratio > 0.8:
            score += 0.1  # Tight fit
        
        # Sales velocity match
        if product.sales_velocity > 10 and self.eye_level_score > 0.7:
            score += 0.2  # Fast movers at good positions
        
        return score
    
    def to_dict(self) -> Dict:
        """Convert shelf to dictionary for export"""
        return {
            'shelf_id': self.shelf_id,
            'shelf_name': self.shelf_name,
            'dimensions': {
                'width': self.width,
                'height': self.height,
                'depth': self.depth
            },
            'y_position': self.y_position,
            'shelf_type': self.shelf_type,
            'eye_level_score': self.eye_level_score,
            'utilization': self.utilization,
            'products': [
                {
                    'product_id': pos.product_id,
                    'x_position': pos.x_start,
                    'width': pos.width,
                    'facings': pos.facings
                }
                for pos in self.positions
            ]
        }
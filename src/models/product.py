from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ProductCategory(Enum):
    CASE = "case"
    CABLE = "cable"
    ADAPTER = "adapter"
    SCREEN_PROTECTOR = "screen_protector"
    CHARGER = "charger"
    MOUNT = "mount"
    AUDIO = "audio"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    PENCIL = "pencil"
    WATCH_BAND = "watch_band"
    OTHER = "other"

class ProductStatus(Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    SEASONAL = "seasonal"
    NEW = "new"

@dataclass
class Product:
    """Product data model for accessories"""
    # Basic info
    product_name: str
    series: str  # iPhone 16, iPhone 15, etc.
    category: ProductCategory
    subcategory: str
    brand: str
    
    # Dimensions (in cm)
    width: float
    height: float
    depth: float
    
    # Sales data
    pureqty: float
    impureqty: float
    
    # Core product info
    core_product: str  # Which device it's for (iPhone, iPad, etc.)
    
    # Cohort data (will be populated from cohort files)
    attach_rate: Optional[float] = None
    bundle_frequency: Optional[int] = None
    
    # Computed fields
    product_id: Optional[str] = None
    min_facings: Optional[int] = None
    max_facings: Optional[int] = None
    status: Optional[ProductStatus] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        # Generate product_id if not provided
        if not self.product_id:
            self.product_id = f"{self.series}_{self.category.value}_{self.subcategory}_{self.brand}".replace(" ", "_")
        
        # Total quantity sold
        self.total_qty = self.pureqty + self.impureqty
        
        # Sales velocity (normalized to 0-100 scale based on total quantity)
        # This will be recalculated relative to other products in the optimizer
        self.sales_velocity = self.total_qty
        
        # Purity ratio (how much of sales is "pure")
        self.purity_ratio = self.pureqty / self.total_qty if self.total_qty > 0 else 0
        
        # Calculate facings based on sales performance
        self._calculate_facing_limits()
        
        # Default status
        if not self.status:
            self.status = ProductStatus.ACTIVE
    
    def _calculate_facing_limits(self):
        """Calculate min/max facings based on sales performance"""
        if self.total_qty >= 400:  # Top sellers
            self.min_facings = 3
            self.max_facings = 6
        elif self.total_qty >= 200:  # Good sellers
            self.min_facings = 2
            self.max_facings = 4
        elif self.total_qty >= 100:  # Moderate sellers
            self.min_facings = 2
            self.max_facings = 3
        elif self.total_qty >= 50:  # Low sellers
            self.min_facings = 1
            self.max_facings = 2
        else:  # Very low sellers
            self.min_facings = 1
            self.max_facings = 1
    
    def calculate_facings(self, strategy: str = "balanced") -> int:
        """Calculate optimal facings based on strategy"""
        if strategy == "sales_based":
            # Pure sales-based calculation - more conservative to fit more products
            if self.total_qty >= 1000:
                return self.max_facings
            elif self.total_qty >= 600:
                return min(3, self.max_facings - 1)
            elif self.total_qty >= 300:
                return min(2, self.max_facings - 2)
            elif self.total_qty >= 100:
                return 2
            else:
                return self.min_facings
                
        elif strategy == "purity_weighted":
            # Give bonus for high purity ratio
            base_facings = self.calculate_facings("sales_based")
            if self.purity_ratio >= 0.8:
                return min(self.max_facings, base_facings + 1)
            elif self.purity_ratio <= 0.3:
                return max(self.min_facings, base_facings - 1)
            return base_facings
            
        else:  # balanced
            # Consider both total sales and purity
            sales_facings = self.calculate_facings("sales_based")
            purity_facings = self.calculate_facings("purity_weighted")
            return max(self.min_facings, (sales_facings + purity_facings) // 2)
    
    @property
    def space_efficiency(self) -> float:
        """Calculate sales per unit of shelf space"""
        return self.total_qty / (self.width * self.height) if self.width > 0 and self.height > 0 else 0
    
    @property
    def profit_efficiency(self) -> float:
        """Calculate profit per unit of shelf space"""
        profit = getattr(self, 'profit', 0) or 0
        space = self.width * self.height if self.width > 0 and self.height > 0 else 1
        return profit / space
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
    product_id: str
    product_name: str
    series: str  # iPhone 16, iPhone 15, etc.
    category: ProductCategory
    subcategory: str
    brand: str
    
    # Dimensions (in cm)
    width: float
    height: float
    depth: float
    weight: float  # in grams
    
    # Sales data
    qty_sold_last_week: int
    qty_sold_last_month: int
    avg_weekly_sales: float
    current_stock: int
    min_stock: int
    
    # Display constraints
    min_facings: int
    max_facings: int
    
    # Additional attributes
    color: str
    price: float
    core_product: str  # Which device it's for
    launch_date: str
    status: ProductStatus
    
    # Cohort data (will be populated from cohort files)
    attach_rate: Optional[float] = None
    bundle_frequency: Optional[int] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.sales_velocity = self.avg_weekly_sales / 7  # Daily average
        self.stock_days = self.current_stock / self.sales_velocity if self.sales_velocity > 0 else 999
        self.needs_restock = self.current_stock <= self.min_stock
        
    def calculate_facings(self, strategy: str = "balanced") -> int:
        """Calculate optimal facings based on strategy"""
        if strategy == "sales_based":
            # Based purely on sales velocity
            base_facings = min(self.max_facings, max(self.min_facings, int(self.sales_velocity / 10) + 1))
        elif strategy == "stock_based":
            # Consider current stock levels
            if self.needs_restock:
                base_facings = self.min_facings
            else:
                stock_ratio = self.current_stock / (self.min_stock * 3)
                base_facings = min(self.max_facings, max(self.min_facings, int(stock_ratio * 3) + 1))
        else:  # balanced
            sales_facings = int(self.sales_velocity / 10) + 1
            stock_facings = int(self.current_stock / self.min_stock)
            base_facings = min(self.max_facings, max(self.min_facings, (sales_facings + stock_facings) // 2))
            
        return base_facings
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from typing import List, Dict, Optional, Tuple
import seaborn as sns
from src.models.product import Product, ProductCategory
from src.models.shelf import Shelf
from src.models.store import Store
from src.optimization.base_optimizer import OptimizationResult
from src.utils.logger import get_logger

class PlanogramVisualizer:
    """Create visual representations of planograms"""
    
    def __init__(self, figsize: Tuple[int, int] = (24, 16)):
        self.figsize = figsize
        self.dpi = 300  # High resolution output
        self.logger = get_logger()
        
        # Define color schemes
        self.category_colors = {
            ProductCategory.CASE: '#FF6B6B',
            ProductCategory.SCREEN_PROTECTOR: '#4ECDC4',
            ProductCategory.CABLE: '#45B7D1',
            ProductCategory.ADAPTER: '#96CEB4',
            ProductCategory.CHARGER: '#FECA57',
            ProductCategory.AUDIO: '#DDA0DD',
            ProductCategory.KEYBOARD: '#95E1D3',
            ProductCategory.MOUSE: '#F38181',
            ProductCategory.PENCIL: '#AA96DA',
            ProductCategory.WATCH_BAND: '#FCBAD3',
            ProductCategory.OTHER: '#B0B0B0'
        }
        
        # Brand-based colors for cases
        self.brand_colors = {
            'apple': '#007AFF',      # Apple Blue
            'pulse': '#FF3B30',      # Red
            'tekne': '#34C759',      # Green  
            'uag': '#FF9500',        # Orange
            'gripp': '#AF52DE',      # Purple
            'otterbox': '#000000',   # Black
            'spigen': '#5856D6',     # Indigo
            'default': '#8E8E93'     # Gray for unknown brands
        }
        
        # iPhone model colors for better distinction
        self.iphone_model_colors = {
            'iphone 16': '#1D1D1F',      # Space Black (latest)
            'iphone 16 plus': '#2F3034',  # Dark
            'iphone 16 pro': '#5F5F5F',   # Pro Gray
            'iphone 16 pro max': '#8A8A8D', # Light Gray
            'iphone 15': '#B0B0B0',       # Lighter (older)
            'iphone 14': '#C7C7CC',       # Lightest (oldest)
            'default': '#E5E5EA'          # Default light
        }
        
        # Store type colors
        self.shelf_colors = {
            'storage': '#E8E8E8',
            'standard': '#F0F0F0',
            'premium': '#FFF9E6',
            'promotional': '#E6F3FF'
        }
    
    def visualize_planogram(self, result: OptimizationResult, 
                          product_lookup: Dict[str, Product],
                          title: str = "Planogram Visualization",
                          save_path: Optional[str] = None,
                          show_metrics: bool = True) -> plt.Figure:
        """Create planogram visualization"""
        
        # Create figure
        if show_metrics:
            fig = plt.figure(figsize=self.figsize)
            # Create grid for planogram and metrics
            gs = fig.add_gridspec(3, 3, height_ratios=[2, 1, 0.5], width_ratios=[3, 1, 1])
            ax_main = fig.add_subplot(gs[0, :])
            ax_metrics1 = fig.add_subplot(gs[1, 0])
            ax_metrics2 = fig.add_subplot(gs[1, 1])
            ax_metrics3 = fig.add_subplot(gs[1, 2])
            ax_legend = fig.add_subplot(gs[2, :])
        else:
            fig, ax_main = plt.subplots(1, 1, figsize=self.figsize)
        
        # Draw planogram
        self._draw_planogram(ax_main, result.store, product_lookup, title)
        
        # Add metrics if requested
        if show_metrics:
            self._add_metrics(ax_metrics1, ax_metrics2, ax_metrics3, result)
            self._add_legend(ax_legend)
        
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            self.logger.info(f"Planogram saved to {save_path}")
        
        return fig
    
    def _draw_planogram(self, ax, store: Store, product_lookup: Dict[str, Product], title: str):
        """Draw the main planogram"""
        
        # Set up the plot
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Calculate plot dimensions
        max_width = max(shelf.width for shelf in store.shelves) * 1.1
        max_height = max(shelf.y_position + shelf.height for shelf in store.shelves) * 1.1
        
        ax.set_xlim(-20, max_width)
        ax.set_ylim(-10, max_height)
        ax.set_aspect('equal')
        
        # Draw shelves and products
        for shelf in store.shelves:
            # Draw shelf background
            shelf_rect = FancyBboxPatch(
                (0, shelf.y_position),
                shelf.width,
                shelf.height,
                boxstyle="round,pad=0.1",
                facecolor=self.shelf_colors.get(shelf.shelf_type, '#F0F0F0'),
                edgecolor='#333333',
                linewidth=2,
                alpha=0.3
            )
            ax.add_patch(shelf_rect)
            
            # Add shelf label
            label_text = shelf.shelf_name
            if shelf.eye_level_score >= 0.8:
                label_text += " 👁️"
            
            ax.text(-15, shelf.y_position + shelf.height/2, label_text,
                   fontsize=10, rotation=90, va='center', ha='center',
                   weight='bold', color='#333333')
            
            # Add utilization indicator
            util_color = self._get_utilization_color(shelf.utilization)
            util_rect = Rectangle(
                (-18, shelf.y_position),
                3,
                shelf.height * (shelf.utilization / 100),
                facecolor=util_color,
                alpha=0.8
            )
            ax.add_patch(util_rect)
            
            # Draw products
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    self._draw_product(ax, product, position, shelf.y_position)
        
        # Add grid
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_xlabel('Width (cm)', fontsize=12)
        ax.set_ylabel('Height (cm)', fontsize=12)
    
    def _draw_product(self, ax, product: Product, position, shelf_y: float):
        """Draw individual product"""
        
        # Product rectangle
        product_rect = FancyBboxPatch(
            (position.x_start, shelf_y + 2),
            position.width - 1,  # Small gap for visual clarity
            product.height - 4,
            boxstyle="round,pad=0.05",
            facecolor=self.category_colors.get(product.category, '#B0B0B0'),
            edgecolor='#333333',
            linewidth=1.5,
            alpha=0.8
        )
        ax.add_patch(product_rect)
        
        # Product label
        label_lines = self._format_product_label(product, position)
        
        # Determine font size based on product width
        if position.width > 20:
            fontsize = 8
        elif position.width > 15:
            fontsize = 7
        else:
            fontsize = 6
        
        # Add text
        ax.text(
            position.x_start + position.width/2,
            shelf_y + product.height/2,
            '\n'.join(label_lines),
            ha='center',
            va='center',
            fontsize=fontsize,
            color='white',
            weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#333333', alpha=0.7)
        )
        
        # Add sales indicator
        if hasattr(product, 'profit'):
            if product.profit > 20:  # High margin
                ax.text(position.x_end - 5, shelf_y + product.height - 5, '$$$',
                    fontsize=8, color='green')
            elif product.profit > 10:  # Medium margin
                ax.text(position.x_end - 5, shelf_y + product.height - 5, '$$',
                    fontsize=8, color='darkgreen')
    
    def _format_product_label(self, product: Product, position) -> List[str]:
        """Format product label for display"""
        lines = []
        
        # Shorten product name if needed
        name_parts = product.product_name.split()
        if len(name_parts) > 3:
            name = ' '.join(name_parts[:2]) + '...'
        else:
            name = product.product_name
        
        lines.append(name)
        lines.append(f"{position.facings} units")
        
        # Show profit if available, otherwise price
        if hasattr(product, 'profit') and product.profit > 0:
            lines.append(f"M: ${product.profit:.0f}")  # M for margin
        elif hasattr(product, 'price'):
            lines.append(f"P: ${product.price:.0f}")   # P for price
        
        return lines
    
    def _get_utilization_color(self, utilization: float) -> str:
        """Get color based on utilization percentage"""
        if utilization >= 90:
            return '#FF4444'  # Red - overcrowded
        elif utilization >= 70:
            return '#44BB44'  # Green - optimal
        elif utilization >= 40:
            return '#BBBB44'  # Yellow - good
        else:
            return '#4444FF'  # Blue - underutilized
    
    def _add_metrics(self, ax1, ax2, ax3, result: OptimizationResult):
        """Add metrics visualizations"""
        
        # Metrics 1: Category distribution
        ax1.set_title('Category Distribution', fontsize=10, weight='bold')
        if 'category_distribution' in result.metrics:
            categories = list(result.metrics['category_distribution'].keys())
            facings = list(result.metrics['category_distribution'].values())
            
            # Create pie chart
            colors = [self.category_colors.get(cat, '#B0B0B0') for cat in categories]
            ax1.pie(facings, labels=[cat.value for cat in categories], 
                   colors=colors, autopct='%1.1f%%', startangle=90)
        
        # Metrics 2: Shelf utilization
        ax2.set_title('Shelf Utilization', fontsize=10, weight='bold')
        if 'shelf_utilization' in result.metrics:
            shelf_names = [s['shelf_name'] for s in result.metrics['shelf_utilization']]
            utilizations = [s['utilization'] for s in result.metrics['shelf_utilization']]
            
            bars = ax2.barh(shelf_names, utilizations)
            
            # Color bars based on utilization
            for bar, util in zip(bars, utilizations):
                bar.set_color(self._get_utilization_color(util))
            
            ax2.set_xlabel('Utilization %')
            ax2.axvline(x=70, color='green', linestyle='--', alpha=0.5)
            ax2.axvline(x=90, color='red', linestyle='--', alpha=0.5)
        
        # Metrics 3: Key metrics
            ax3.set_title('Key Metrics', fontsize=10, weight='bold')
            ax3.axis('off')
            
            metrics_text = [
                f"Total Facings: {result.metrics.get('total_facings', 0)}",
                f"Avg Utilization: {result.metrics.get('average_utilization', 0):.1f}%",
                f"Space Efficiency: {(len(result.products_placed) / (len(result.products_placed) + len(result.products_rejected)) * 100):.1f}%"
            ]
            
            # Updated to show profit metrics
            if 'profit_density' in result.metrics:
                metrics_text.append(f"Profit Density: ${result.metrics['profit_density']:.2f}/cm")
            elif 'value_density' in result.metrics:
                metrics_text.append(f"Value Density: ${result.metrics['value_density']:.2f}/cm")
            
            if 'quantity_density' in result.metrics:
                metrics_text.append(f"Qty Density: {result.metrics['quantity_density']:.1f}/cm")
            
            # Display metrics
            for i, text in enumerate(metrics_text):
                ax3.text(0.1, 0.8 - i*0.15, text, fontsize=9, transform=ax3.transAxes)
    def create_profit_heatmap(self, result: OptimizationResult,
                         product_lookup: Dict[str, Product],
                         save_path: Optional[str] = None) -> plt.Figure:
    
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        # Heatmap 1: Profit per unit
        shelf_data_profit = []
        # Heatmap 2: Total profit potential
        shelf_data_potential = []
        
        for shelf in result.store.shelves:
            profit_row = []
            potential_row = []
            
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    profit = getattr(product, 'profit', 0)
                    potential = profit * product.total_qty * position.facings
                    
                    profit_row.append(profit)
                    potential_row.append(potential)
            
            shelf_data_profit.append(profit_row)
            shelf_data_potential.append(potential_row)
        
        # Pad rows and create heatmaps
        max_positions = max(len(row) for row in shelf_data_profit) if shelf_data_profit else 0
        
        for row in shelf_data_profit:
            row.extend([0] * (max_positions - len(row)))
        for row in shelf_data_potential:
            row.extend([0] * (max_positions - len(row)))
        
        # Create heatmaps
        if shelf_data_profit and max_positions > 0:
            sns.heatmap(shelf_data_profit, annot=True, fmt='.0f', cmap='Greens',
                    cbar_kws={'label': 'Profit Margin ($)'},
                    ax=ax1,
                    xticklabels=False,
                    yticklabels=[s.shelf_name for s in result.store.shelves])
            ax1.set_title('Profit Margin by Position', fontsize=14, weight='bold')
            
            sns.heatmap(shelf_data_potential, annot=True, fmt='.0f', cmap='YlOrRd',
                    cbar_kws={'label': 'Total Profit Potential ($)'},
                    ax=ax2,
                    xticklabels=False,
                    yticklabels=[s.shelf_name for s in result.store.shelves])
            ax2.set_title('Total Profit Potential by Position', fontsize=14, weight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
    def _add_legend(self, ax):
        """Add category color legend"""
        ax.axis('off')
        
        # Create legend elements
        legend_elements = []
        for category, color in self.category_colors.items():
            legend_elements.append(
                patches.Patch(facecolor=color, label=category.value.replace('_', ' ').title())
            )
        
        # Create legend
        ax.legend(handles=legend_elements, loc='center', ncol=6, 
                 frameon=False, fontsize=9)
    
    def create_comparison_view(self, results: Dict[str, OptimizationResult],
                             product_lookup: Dict[str, Product],
                             save_path: Optional[str] = None) -> plt.Figure:
        """Create comparison view of multiple optimization results"""
        
        n_results = len(results)
        fig, axes = plt.subplots(n_results, 1, figsize=(20, 8*n_results))
        
        if n_results == 1:
            axes = [axes]
        
        for ax, (name, result) in zip(axes, results.items()):
            self._draw_planogram(ax, result.store, product_lookup, f"Planogram - {name}")
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
    
    def create_heatmap_view(self, result: OptimizationResult,
                          product_lookup: Dict[str, Product],
                          metric: str = 'sales_velocity',
                          save_path: Optional[str] = None) -> plt.Figure:
        """Create heatmap view showing product metrics"""
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Prepare data for heatmap
        shelf_data = []
        max_positions = 0
        
        for shelf in result.store.shelves:
            row_data = []
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    if metric == 'sales_velocity':
                        value = product.sales_velocity
                    elif metric == 'price':
                        value = product.price
                    elif metric == 'attach_rate':
                        value = getattr(product, 'attach_rate', 0)
                    else:
                        value = 0
                    row_data.append(value)
            
            shelf_data.append(row_data)
            max_positions = max(max_positions, len(row_data))
        
        # Pad rows to same length
        for row in shelf_data:
            row.extend([0] * (max_positions - len(row)))
        
        # Create heatmap
        if shelf_data and max_positions > 0:
            sns.heatmap(shelf_data, annot=True, fmt='.1f', cmap='YlOrRd',
                       cbar_kws={'label': metric.replace('_', ' ').title()},
                       xticklabels=False,
                       yticklabels=[s.shelf_name for s in result.store.shelves])
        
        ax.set_title(f'Product Heatmap - {metric.replace("_", " ").title()}',
                    fontsize=16, weight='bold')
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
    
    def _arrange_products_for_express_store(self, all_products: List[Tuple]) -> List[Tuple]:
        """Arrange products for express store with aesthetic structure"""
        self.logger.info("Creating aesthetic arrangement for express store")
        
        # Separate by brand
        apple_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() == 'apple']
        tpa_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() != 'apple']
        
        # Sort each group by sales velocity
        apple_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        tpa_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        
        self.logger.info(f"Available products: {len(apple_products)} Apple, {len(tpa_products)} TPA")
        
        # Group TPA products by iPhone series for visual coherence
        tpa_by_series = {}
        for product, facings in tpa_products:
            series = getattr(product, 'series', 'Other')
            if series not in tpa_by_series:
                tpa_by_series[series] = []
            tpa_by_series[series].append((product, facings))
        
        # Debug: Log what series we found
        self.logger.info(f"TPA products by series: {list(tpa_by_series.keys())}")
        
        # Create structured arrangement - Apple products should be on TOP row
        arranged_products = []
        products_per_row = 6  # Express store grid
        
        # TOP ROW (Row 1): Apple products ONLY - prioritize iPhone case products
        # Filter Apple products to prioritize iPhone cases (actual cases, not screen protectors)
        apple_cases = [(p, f) for p, f in apple_products if str(getattr(p, 'category', '')).lower() == 'case']
        apple_others = [(p, f) for p, f in apple_products if str(getattr(p, 'category', '')).lower() != 'case']
        
        # Prioritize iPhone cases in top row, then other Apple products
        apple_row = (apple_cases + apple_others)[:products_per_row]
        arranged_products.extend(apple_row)
        self.logger.info(f"TOP ROW (Apple): {len(apple_row)} products ({len(apple_cases)} cases)")
        
        # Don't fill empty slots in top row - let them be empty if no Apple products
        
        # Rows 2-4: Group TPA products by series for aesthetics
        # Group similar iPhone series together for visual coherence
        
        # Prioritize iPhone 15 series together, then iPhone 16 series
        iphone_15_series = ['iPhone 15 Base', 'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max']
        iphone_16_series = ['iPhone 16 Base', 'iPhone 16 Plus', 'iPhone 16 Pro', 'iPhone 16 Pro Max']
        
        # Row 2: iPhone 15 series - Group ALL iPhone 15 together
        iphone_15_products = []
        for series in iphone_15_series:
            if series in tpa_by_series:
                iphone_15_products.extend(tpa_by_series[series])
                
        # Also check for any products that have iPhone 15 in the name or series
        for product_tuple in tpa_products:
            product, facings = product_tuple
            product_name = getattr(product, 'product_name', '').lower()
            if 'iphone 15' in product_name and product_tuple not in iphone_15_products:
                iphone_15_products.append(product_tuple)
        
        # Sort iPhone 15 products by sales velocity
        iphone_15_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        row_2_products = iphone_15_products[:products_per_row]
        arranged_products.extend(row_2_products)
        self.logger.info(f"Row 2 (iPhone 15): {len(row_2_products)} products")
        
        # Row 3: iPhone 16 series  
        iphone_16_products = []
        for series in iphone_16_series:
            if series in tpa_by_series:
                iphone_16_products.extend(tpa_by_series[series])
        
        # Sort iPhone 16 products by sales velocity
        iphone_16_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        row_3_products = iphone_16_products[:products_per_row]
        arranged_products.extend(row_3_products)
        self.logger.info(f"Row 3 (iPhone 16): {len(row_3_products)} products")
        
        # Row 4: Other series and remaining products
        other_products = []
        used_product_ids = set()
        for product_tuple in row_2_products + row_3_products:
            if product_tuple:
                product, facings = product_tuple
                used_product_ids.add(getattr(product, 'product_id', id(product)))
                
        for product_tuple in tpa_products:
            if product_tuple:
                product, facings = product_tuple
                product_id = getattr(product, 'product_id', id(product))
                if product_id not in used_product_ids:
                    other_products.append(product_tuple)
        
        row_4_products = other_products[:products_per_row]
        arranged_products.extend(row_4_products)
        self.logger.info(f"Row 4 (Other): {len(row_4_products)} products")
        
        # Return arranged products - don't force full grid
        return arranged_products
        
    def _arrange_products_for_flagship_store(self, all_products: List[Tuple]) -> List[Tuple]:
        """Arrange products for flagship store: First 4 rows Apple only, last 4 rows TPA only"""
        self.logger.info("Creating flagship arrangement: First 4 rows Apple, last 4 rows TPA")
        
        # Separate by brand
        apple_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() == 'apple']
        tpa_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() != 'apple']
        
        # Sort each group by sales velocity
        apple_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        tpa_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        
        self.logger.info(f"Available products: {len(apple_products)} Apple, {len(tpa_products)} TPA")
        
        arranged_products = []
        products_per_row = 5  # Flagship store: 5 columns
        
        # First 4 rows: ONLY Apple products (20 slots total)
        apple_slots = 4 * products_per_row  # 20 slots for Apple
        apple_for_display = apple_products[:apple_slots]
        arranged_products.extend(apple_for_display)
        
        # Fill remaining Apple slots with None if needed
        while len(arranged_products) < apple_slots:
            arranged_products.append(None)
            
        self.logger.info(f"Apple rows 1-4: {len([p for p in arranged_products if p is not None])} products")
        
        # Last 4 rows: ONLY TPA products (20 slots total)
        tpa_slots = 4 * products_per_row  # 20 slots for TPA
        tpa_for_display = tpa_products[:tpa_slots]
        arranged_products.extend(tpa_for_display)
        
        # Fill remaining TPA slots with None if needed
        while len(arranged_products) < apple_slots + tpa_slots:
            arranged_products.append(None)
            
        self.logger.info(f"TPA rows 5-8: {len(tpa_for_display)} products")
        
        return arranged_products
    
    def _arrange_products_for_standard_store(self, all_products: List[Tuple]) -> List[Tuple]:
        """Arrange products for standard store: First row Apple only, rest TPA only"""
        self.logger.info("Creating standard arrangement: First row Apple, rest TPA")
        
        # Separate by brand
        apple_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() == 'apple']
        tpa_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() != 'apple']
        
        # Sort each group by sales velocity
        apple_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        tpa_products.sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        
        self.logger.info(f"Available products: {len(apple_products)} Apple, {len(tpa_products)} TPA")
        
        arranged_products = []
        products_per_row = 6  # Standard store: 6 columns
        
        # First row: ONLY Apple products (6 slots)
        apple_slots = products_per_row  # 6 slots for Apple
        apple_for_display = apple_products[:apple_slots]
        arranged_products.extend(apple_for_display)
        
        # Fill remaining Apple slots with None if needed
        while len(arranged_products) < apple_slots:
            arranged_products.append(None)
            
        self.logger.info(f"Apple row 1: {len([p for p in arranged_products if p is not None])} products")
        
        # Remaining 5 rows: ONLY TPA products (30 slots total)
        tpa_slots = 5 * products_per_row  # 30 slots for TPA
        tpa_for_display = tpa_products[:tpa_slots]
        arranged_products.extend(tpa_for_display)
        
        # Fill remaining TPA slots with None if needed
        while len(arranged_products) < apple_slots + tpa_slots:
            arranged_products.append(None)
            
        self.logger.info(f"TPA rows 2-6: {len(tpa_for_display)} products")
        
        return arranged_products
    
    def create_realistic_retail_planogram(self, result: OptimizationResult,
                                         product_lookup: Dict[str, Product],
                                         title: str = "Apple Store Accessory Display",
                                         save_path: Optional[str] = None) -> plt.Figure:
        """Create a clean, modern retail planogram with proper grid layout"""
        
        # Import and use the clean planogram function
        from src.visualization.clean_planogram import create_clean_planogram
        self.logger.debug(f"Calling create_clean_planogram with save_path={save_path}")
        return create_clean_planogram(result, product_lookup, title, save_path, self.figsize)
    
    def _create_clean_label(self, product: Product) -> str:
        """Create a clean label for a product"""
        # Create a clean product name (remove extra spaces and truncate if too long)
        clean_name = product.product_name.strip()
        if len(clean_name) > 40:
            clean_name = clean_name[:37] + "..."
        
        # Add brand if available
        if hasattr(product, 'brand') and product.brand:
            return f"{product.brand}\n{clean_name}"
        else:
            return clean_name
    
    def _create_realistic_retail_display(self, result: OptimizationResult, 
                                       product_lookup: Dict[str, Product], 
                                       display_products: List[Tuple[Product, int]],
                                       title: str = "Apple Store Accessory Display", 
                                       save_path: Optional[str] = None) -> plt.Figure:
        """Create the actual retail display visualization"""
        # Get layout parameters
        if result.store.store_type == 'express':
            total_rows = 5
            products_per_row = 6
        elif result.store.store_type == 'flagship':
            total_rows = 8
            products_per_row = 5
        else:
            total_rows = 6
            products_per_row = 6
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_facecolor('#F8F9FA')
        
        # Product display parameters - adjusted for phone cases
        product_width = 10   # cm - reduced width for phone cases
        product_height = 16  # cm - reduced height for phone cases
        gap_x = 2           # horizontal gap
        gap_y = 3           # vertical gap
        margin_x = 15       # left margin
        margin_y = 10       # bottom margin
        
        # Calculate total display area
        total_width = margin_x * 2 + (products_per_row * product_width) + ((products_per_row - 1) * gap_x)
        total_height = margin_y * 2 + (total_rows * product_height) + ((total_rows - 1) * gap_y)
        
        ax.set_xlim(0, total_width)
        ax.set_ylim(0, total_height + 100)  # Extra space for legend at bottom
        
        # Draw shelf backgrounds (like reference image sections)
        shelf_height = (total_height - margin_y * 2) / 4  # 4 main shelf sections
        for i in range(4):
            shelf_y = margin_y + i * shelf_height
            shelf_bg = Rectangle(
                (margin_x - 10, shelf_y - 5),
                total_width - margin_x * 2 + 20,
                shelf_height + 10,
                facecolor='#FFFFFF',
                edgecolor='#E8E8E8',
                linewidth=1.5,
                alpha=0.7
            )
            ax.add_patch(shelf_bg)
        
        # Draw products in grid layout
        for idx, product_data in enumerate(display_products):
            # Skip empty slots
            if product_data is None:
                continue
                
            product, facings = product_data
            row = idx // products_per_row
            col = idx % products_per_row
            
            # Calculate position
            x = margin_x + col * (product_width + gap_x)
            y = total_height - margin_y - (row + 1) * (product_height + gap_y)
            
            # Draw product package (like hanging retail display)
            # Main product rectangle
            product_rect = FancyBboxPatch(
                (x, y),
                product_width,
                product_height,
                boxstyle="round,pad=0.3",
                facecolor='white',
                edgecolor='#333333',
                linewidth=1.5,
                alpha=0.95
            )
            ax.add_patch(product_rect)
            
            # Get brand and model colors
            brand = getattr(product, 'brand', '').lower()
            series = getattr(product, 'series', '').lower()
            
            # Determine primary color based on brand
            brand_color = self.brand_colors.get(brand, self.brand_colors['default'])
            
            # Determine secondary color based on iPhone model
            model_color = self.iphone_model_colors['default']
            for model_key in self.iphone_model_colors:
                if model_key in series:
                    model_color = self.iphone_model_colors[model_key]
                    break
            
            # Add brand color strip (top of package)
            brand_strip = Rectangle(
                (x + 1, y + product_height - 3),
                product_width - 2, 2.5,
                facecolor=brand_color,
                alpha=0.9
            )
            ax.add_patch(brand_strip)
            
            # Add model color accent (left side)
            model_accent = Rectangle(
                (x, y + 1),
                2, product_height - 4,
                facecolor=model_color,
                alpha=0.8
            )
            ax.add_patch(model_accent)
            
            # Add product image area (center)
            image_area = Rectangle(
                (x + 2, y + 5),
                product_width - 4, product_height - 10,
                facecolor='#F5F5F5',
                edgecolor='#DDDDDD',
                linewidth=0.5,
                alpha=0.8
            )
            ax.add_patch(image_area)
            
            # Add product name with better visibility
            name = self._create_retail_label(product)
            product_name_short = name.split('\n')[0]
            
            # Add white background for product name
            name_bg = Rectangle(
                (x + 1, y + product_height - 8),
                product_width - 2, 6,
                facecolor='white',
                edgecolor='none',
                alpha=0.95
            )
            ax.add_patch(name_bg)
            
            # Product name with dark text on white background
            ax.text(x + product_width/2, y + product_height - 5,
                   product_name_short,
                   ha='center', va='center',
                   fontsize=7, fontweight='bold',
                   color='#333333')  # Dark text for better readability
            
            # Add brand and model at bottom with background
            brand_bg = Rectangle(
                (x + 1, y + 1),
                product_width - 2, 4,
                facecolor='#F0F0F0',
                edgecolor='none',
                alpha=0.9
            )
            ax.add_patch(brand_bg)
            
            # Format brand and model text
            brand_text = getattr(product, 'brand', 'Unknown').upper()
            series_text = getattr(product, 'series', '')
            
            # Extract iPhone model for cleaner display
            if 'iPhone 16' in series_text:
                model_text = series_text.replace('iPhone ', 'i').replace(' ', '')
            else:
                model_text = series_text.replace('iPhone ', 'i').replace(' ', '')[:8]
            
            # Display brand prominently
            ax.text(x + product_width/2, y + 3.2,
                   brand_text,
                   ha='center', va='center',
                   fontsize=7, fontweight='bold',
                   color='#000000')
            
            # Display model below brand
            if model_text:
                ax.text(x + product_width/2, y + 1.8,
                       model_text,
                       ha='center', va='center',
                       fontsize=5, fontweight='normal',
                       color='#666666')
            
        # Add performance indicators on the product itself (not on top)
            if product.total_qty > 300:  # Bestseller
                # Gold circle for bestseller
                star_circle = plt.Circle((x + product_width - 3, y + 3), 1.8,
                                       color='#FFD700', alpha=0.95)
                ax.add_patch(star_circle)
                ax.text(x + product_width - 3, y + 3, 'BEST',
                       ha='center', va='center', fontsize=5, color='white', fontweight='bold')
            elif product.total_qty > 100:  # Popular
                # Orange circle for popular
                pop_circle = plt.Circle((x + product_width - 3, y + 3), 1.5,
                                      color='#FF8C00', alpha=0.95)
                ax.add_patch(pop_circle)
                ax.text(x + product_width - 3, y + 3, 'POP',
                       ha='center', va='center', fontsize=5, color='white', fontweight='bold')
            
            # Add brand badge (small colored square)
            brand_color = self._get_brand_color(product.brand)
            brand_badge = Rectangle(
                (x + 1, y + 1),
                2, 2,
                facecolor=brand_color,
                alpha=0.8
            )
            ax.add_patch(brand_badge)
            
            # Add quantity indicator if multiple facings
            if facings > 1:
                ax.text(x + product_width - 1, y + 1,
                       f'{facings}x',
                       ha='right', va='bottom',
                       fontsize=6, fontweight='bold',
                       color='#333333',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        
        # Add title
        ax.text(total_width/2, total_height - 5,
               title, ha='center', va='top',
               fontsize=16, fontweight='bold', color='#333333')
        
        # Brand and Model legend at bottom - positioned properly
        legend_y = 50  # Move legend down to avoid overlap
        brands_shown = set()
        models_shown = set()
        
        # Extract brands and models from displayed products (skip None values)
        for product_data in display_products:
            if product_data is None:
                continue
            product, _ = product_data
            brand = getattr(product, 'brand', 'Unknown')
            brands_shown.add(brand)
            
            series = getattr(product, 'series', '')
            for model_key in self.iphone_model_colors:
                if model_key in series.lower():
                    models_shown.add(model_key)
                    break
        
        # Brand legend - centered horizontally
        brand_legend_width = len(brands_shown) * 80
        brand_legend_start_x = max(margin_x, (total_width - brand_legend_width) // 2)
        
        ax.text(brand_legend_start_x, legend_y + 25, 'Brands (Top Strip):', 
               fontsize=10, fontweight='bold', color='#333333')
        
        legend_x = brand_legend_start_x
        for i, brand in enumerate(sorted(brands_shown)):
            brand_color = self.brand_colors.get(brand.lower(), self.brand_colors['default'])
            
            # Brand color box
            brand_box = Rectangle(
                (legend_x, legend_y + 15),
                12, 6,
                facecolor=brand_color,
                edgecolor='#333333',
                linewidth=1,
                alpha=0.9
            )
            ax.add_patch(brand_box)
            
            # Brand name
            ax.text(legend_x + 16, legend_y + 18, 
                   brand.upper(),
                   fontsize=9, color='#333333', va='center')
            
            legend_x += 80
        
        # iPhone Model legend - centered horizontally below brands
        if models_shown:
            model_legend_width = len(models_shown) * 70
            model_legend_start_x = max(margin_x, (total_width - model_legend_width) // 2)
            
            ax.text(model_legend_start_x, legend_y, 'iPhone Models (Left Accent):', 
                   fontsize=10, fontweight='bold', color='#333333')
            
            model_legend_x = model_legend_start_x
            for model in sorted(models_shown):
                model_color = self.iphone_model_colors[model]
                
                # Model color box
                model_box = Rectangle(
                    (model_legend_x, legend_y - 10),
                    8, 6,
                    facecolor=model_color,
                    edgecolor='#333333',
                    linewidth=1,
                    alpha=0.8
                )
                ax.add_patch(model_box)
                
                # Model name
                ax.text(model_legend_x + 12, legend_y - 7, 
                       model.replace('iphone ', 'i').title(),
                       fontsize=8, color='#333333', va='center')
                
                model_legend_x += 70
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight',
            facecolor='white', edgecolor='none')
            self.logger.info(f"Realistic retail planogram saved to {save_path}")
        
        return fig
    
    def _create_clean_label(self, product: Product) -> str:
        """Create clean, readable product label"""
        name = getattr(product, 'product_name', 'Unknown')
        brand = getattr(product, 'brand', 'Unknown')
        
        # For Apple products, show simple name
        if brand.lower() == 'apple':
            if 'Pro Max' in name:
                return 'Pro Max\nClear'
            elif 'Pro' in name:
                return 'Pro\nClear'
            elif 'Plus' in name:
                return 'Plus\nClear'
            else:
                return '16\nClear'
        else:
            # For TPA products, show brand
            return f'{brand}\nCase'
    
    def _create_retail_label(self, product: Product) -> str:
        """Create realistic retail product label"""
        name = product.product_name.strip()
        
        # Remove iPhone model number if present
        name = name.replace('iPhone 16 Pro Max', 'Pro Max')
        name = name.replace('iPhone 16 Pro', 'Pro')
        name = name.replace('iPhone 16 Plus', 'Plus')
        name = name.replace('iPhone 16', '16')
        name = name.replace('iPhone 15', '15')
        
        # Simplify case types
        name = name.replace('Case with MagSafe', 'MagSafe')
        name = name.replace('Silicone Case', 'Silicone')
        name = name.replace('Clear Case', 'Clear')
        name = name.replace('Tempered Glass', 'Glass')
        name = name.replace('Camera Lens Protector', 'Lens')
        
        # Take first few important words
        words = name.split()
        if len(words) > 4:
            name = ' '.join(words[:4])
        
        # Add brand on new line
        return f"{name}\n{product.brand}"
    
    def create_retail_grid_planogram(self, result: OptimizationResult,
                                   product_lookup: Dict[str, Product],
                                   title: str = "Apple Store Accessory Planogram",
                                   save_path: Optional[str] = None) -> plt.Figure:
        """Wrapper that calls the realistic retail planogram"""
        return self.create_realistic_retail_planogram(result, product_lookup, title, save_path)
    
    def _shorten_product_name(self, name: str) -> str:
        """Intelligently shorten product names for display"""
        # Remove common prefixes
        name = name.replace('iPhone ', '')
        name = name.replace('Case with MagSafe', 'MagSafe')
        name = name.replace('Silicone Case', 'Silicone')
        name = name.replace('Clear Case', 'Clear')
        name = name.replace('Tempered Glass', 'Glass')
        name = name.replace('Camera Lens Protector', 'Lens')
        
        # Split and take important parts
        parts = name.split()
        if len(parts) > 3:
            # Take model, type, and color/variant
            important_parts = []
            for part in parts[:3]:
                if len(part) > 2:  # Skip very short words
                    important_parts.append(part)
            name = ' '.join(important_parts)
        
        # Limit length
        if len(name) > 20:
            name = name[:17] + '...'
        
        return name
    
    def _get_brand_color(self, brand: str) -> str:
        """Get brand-specific color"""
        brand_colors = {
            'Apple': '#007AFF',
            'Gripp': '#34C759',
            'Pulse': '#FF3B30',
            'Hyphen': '#5856D6',
            'AT Minimal': '#FF9500',
            'Roskilde': '#8E8E93',
            'nmaxn': '#FFCC00',
            'Robocare': '#FF2D92',
            'Flayrr': '#30D158',
            'PG': '#64D2FF'
        }
        return brand_colors.get(brand, '#999999')

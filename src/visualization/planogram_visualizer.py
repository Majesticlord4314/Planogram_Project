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
    
    def __init__(self, figsize: Tuple[int, int] = (20, 12)):
        self.figsize = figsize
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
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
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
                ax.text(position.x_end - 5, shelf_y + product.height - 5, '💰',
                    fontsize=8, color='green')
            elif product.profit > 10:  # Medium margin
                ax.text(position.x_end - 5, shelf_y + product.height - 5, '💵',
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
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
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
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
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
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_realistic_retail_planogram(self, result: OptimizationResult,
                                         product_lookup: Dict[str, Product],
                                         title: str = "Apple Store Accessory Display",
                                         save_path: Optional[str] = None) -> plt.Figure:
        """Create a realistic retail planogram that looks like actual store displays"""
        
        # Create figure with portrait orientation like real planograms
        fig, ax = plt.subplots(figsize=(12, 16))  # Portrait orientation
        ax.set_facecolor('#F8F8F8')  # Clean store background
        
        # Get all placed products and sort by sales performance
        all_products = []
        for shelf in result.store.shelves:
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    all_products.append((product, position.facings))
        
        # Ensure we have products to display
        if not all_products:
            # If no products were placed, create a message
            ax.text(0.5, 0.5, 'No products were successfully placed\nCheck product dimensions and shelf constraints',
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=16, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            return fig
        
        # Sort by sales performance and limit display count based on shelf configuration
        all_products.sort(key=lambda x: x[0].total_qty, reverse=True)
        max_display = min(len(all_products), len(result.store.shelves) * 8)  # 8 products per shelf max
        display_products = all_products[:max_display]
        
        # Calculate optimal grid to fill all shelf positions
        # Determine best layout based on store configuration and available products
        if len(result.store.shelves) >= 8:  # Flagship store
            products_per_row = 10
            target_rows = 8
        elif len(result.store.shelves) >= 6:  # Standard store  
            products_per_row = 8
            target_rows = 6
        else:  # Express store
            products_per_row = 6
            target_rows = 4
        
        # Fill all positions by repeating products if necessary
        target_positions = products_per_row * target_rows
        
        # If we have fewer products than target positions, repeat best sellers
        if len(display_products) < target_positions:
            # Repeat top products to fill empty spots
            top_products = display_products[:min(10, len(display_products))]  # Top 10 products
            while len(display_products) < target_positions and top_products:
                for product_data in top_products:
                    if len(display_products) >= target_positions:
                        break
                    display_products.append(product_data)
        
        # Limit to target positions
        display_products = display_products[:target_positions]
        total_rows = target_rows
        
        # Product display parameters
        product_width = 12   # cm
        product_height = 18  # cm  
        gap_x = 3           # horizontal gap
        gap_y = 4           # vertical gap
        margin_x = 20       # left margin
        margin_y = 15       # bottom margin
        
        # Calculate total display area
        total_width = margin_x * 2 + (products_per_row * product_width) + ((products_per_row - 1) * gap_x)
        total_height = margin_y * 2 + (total_rows * product_height) + ((total_rows - 1) * gap_y)
        
        ax.set_xlim(0, total_width)
        ax.set_ylim(0, total_height)
        
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
        for idx, (product, facings) in enumerate(display_products):
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
            
            # Add category color strip (top of package)
            category_color = self.category_colors.get(product.category, '#B0B0B0')
            color_strip = Rectangle(
                (x + 1, y + product_height - 3),
                product_width - 2, 2.5,
                facecolor=category_color,
                alpha=0.9
            )
            ax.add_patch(color_strip)
            
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
            
            # Add brand at bottom with background
            brand_bg = Rectangle(
                (x + 1, y + 1),
                product_width - 2, 4,
                facecolor='#F0F0F0',
                edgecolor='none',
                alpha=0.9
            )
            ax.add_patch(brand_bg)
            
            ax.text(x + product_width/2, y + 3,
                   product.brand,
                   ha='center', va='center',
                   fontsize=6, fontweight='bold',
                   color='#333333')  # Dark text
            
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
        
        # Category legend at bottom
        legend_y = 10
        categories_shown = set(product[0].category for product in display_products)
        
        ax.text(margin_x, legend_y + 15, 'Categories:', 
               fontsize=10, fontweight='bold', color='#333333')
        
        legend_x = margin_x
        for i, category in enumerate(categories_shown):
            color = self.category_colors.get(category, '#B0B0B0')
            
            # Category color box
            cat_box = Rectangle(
                (legend_x, legend_y),
                8, 8,
                facecolor=color,
                edgecolor='#333333',
                linewidth=1,
                alpha=0.8
            )
            ax.add_patch(cat_box)
            
            # Category name
            ax.text(legend_x + 12, legend_y + 4, 
                   category.value.replace('_', ' ').title(),
                   fontsize=9, color='#333333', va='center')
            
            legend_x += 80
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            self.logger.info(f"Realistic retail planogram saved to {save_path}")
        
        return fig
    
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

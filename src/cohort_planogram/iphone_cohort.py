"""
iPhone Cohort-Based Planogram Generator

This module generates detailed cohort-based planograms for iPhone,
showing relationships between iPhone models and their accessories
based on customer purchase behavior and attach rates.
"""

import pandas as pd
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib import patches
from typing import Dict, List, Tuple
from pathlib import Path

from .base import CohortPlanogramBase, StoreTemplateLoader
from .data_loader import CohortDataLoader

class iPhoneCohortPlanogram(CohortPlanogramBase):
    """Generate iPhone cohort-based planograms"""
    
    def __init__(self):
        super().__init__('iPhone')
        self.data_loader = CohortDataLoader()
        self.store_template_loader = StoreTemplateLoader()
        
    def generate_cohort_planogram(self, store_type: str) -> Path:
        """Generate comprehensive iPhone cohort planogram"""
        self.logger.info(f"Generating iPhone cohort planogram for {store_type} store")
        
        # Load iPhone cohort data
        iphone_data = self.data_loader.get_lob_data('iPhone')
        
        # Get top iPhone models and accessory categories based on store type
        matrix_config = self.store_template_loader.get_matrix_config(store_type)
        top_models = self.data_loader.get_top_core_products('iPhone', limit=matrix_config['max_models'])
        top_categories = self.data_loader.get_top_accessory_categories('iPhone', limit=matrix_config['max_categories'])
        
        # Get cohort matrices
        attach_rate_matrix = self.data_loader.get_cohort_matrix('iPhone', top_models, top_categories)
        frequency_matrix = self.data_loader.get_frequency_matrix('iPhone', top_models, top_categories)
        
        # Fill missing values with 0
        attach_rate_matrix = attach_rate_matrix.fillna(0)
        frequency_matrix = frequency_matrix.fillna(0)
        
        # Get insights
        top_cohort_pairs = self.data_loader.get_top_cohort_pairs('iPhone', limit=8)
        summary_stats = self.data_loader.get_lob_summary_stats('iPhone')
        
        # Create figure with store-specific dimensions
        fig, ax = self.create_figure(store_type)
        
        # Get store-specific layout positions
        layout_positions = self.store_template_loader.get_layout_positions(store_type)
        core_product_config = self.store_template_loader.get_core_product_config(store_type)
        
        # Add title
        self.add_title(ax, f"iPhone Cohort Planogram - {store_type.title()} Store", y_pos=layout_positions['title_y'])
        
        # Create core product zones (store-specific sizing)
        self._create_core_product_zones(ax, iphone_data, top_models, store_type, **core_product_config)
        
        # Create cohort matrix (main section, store-specific)
        self._create_cohort_matrix(ax, attach_rate_matrix, frequency_matrix, iphone_data, store_type, y_start=layout_positions['matrix_y'])
        
        # Add insights panel (store-specific positioning)
        self._add_insights_panel(ax, top_cohort_pairs, summary_stats, x_pos=layout_positions['insights_x'], y_pos=layout_positions['insights_y'])
        
        # Add recommended layout (store-specific positioning)
        self._add_recommended_layout(ax, top_models, top_categories, x_pos=layout_positions['recommended_x'], y_pos=layout_positions['recommended_y'])
        
        # Add legend (store-specific positioning)
        self.create_legend(ax, top_categories, x_pos=layout_positions['legend_x'], y_pos=layout_positions['legend_y'])
        
        # Save planogram
        filename = f"iphone_cohort_detailed_{store_type}.png"
        planogram_path = self.save_planogram(fig, filename)
        
        # Generate detailed product list
        self._generate_product_list(top_models, top_categories, store_type)
        
        return planogram_path
    
    def _create_core_product_zones(self, ax, iphone_data: pd.DataFrame, 
                                  top_models: List[str], store_type: str,
                                  zone_width: int, zone_height: int, 
                                  x_start: int, y_start: int, x_spacing: int) -> None:
        """Create iPhone core product zones with performance indicators"""
        self.add_section_label(ax, "CORE PRODUCTS", x_start, y_start + 10, ha='left')
        
        for i, model in enumerate(top_models):
            x_pos = x_start + i * (zone_width + x_spacing)
            
            # Get model statistics
            model_data = iphone_data[iphone_data['core_product'] == model]
            total_sales = model_data['purchase_frequency'].sum()
            avg_attach_rate = model_data['attach_rate'].mean()
            category_count = model_data['accessory_category'].nunique()
            
            # Color based on performance
            color = self.get_performance_color(avg_attach_rate)
            
            # Draw zone
            zone_rect = FancyBboxPatch(
                (x_pos, y_start), zone_width, zone_height,
                boxstyle="round,pad=3",
                facecolor=color,
                edgecolor='#86868B',
                linewidth=1.5,
                alpha=0.9
            )
            ax.add_patch(zone_rect)
            
            # Add model name (formatted)
            model_name = self.format_product_name(model, max_length=8)
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 + 2, 
                   model_name, fontsize=8, ha='center', va='center',
                   color='white', weight='bold')
            
            # Add attach rate
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 - 2, 
                   f'{avg_attach_rate:.1%}', fontsize=7, ha='center', va='center',
                   color='white', weight='medium')
            
            # Add sales volume
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 - 6, 
                   f'{total_sales:,.0f}', fontsize=6, ha='center', va='center',
                   color='white', weight='medium')
            
            # Add performance indicator
            self.add_performance_indicator(ax, x_pos + zone_width - 6, y_start + zone_height - 6, 
                                         avg_attach_rate, size=3)
    
    def _create_cohort_matrix(self, ax, attach_rate_matrix: pd.DataFrame, 
                             frequency_matrix: pd.DataFrame, iphone_data: pd.DataFrame, 
                             store_type: str, y_start: int) -> None:
        """Create clean cohort matrix showing iPhone models vs accessories"""
        self.add_section_label(ax, "COHORT MATRIX", 20, y_start + 15)
        
        # Get store-specific matrix configuration
        matrix_config = self.store_template_loader.get_matrix_config(store_type)
        cell_width = matrix_config['cell_width']
        cell_height = matrix_config['cell_height']
        x_spacing = matrix_config['x_spacing']
        y_spacing = matrix_config['y_spacing']
        x_start = matrix_config['x_start']
        
        # Calculate starting positions - leave more room for category labels
        models = list(attach_rate_matrix.columns)
        categories = list(attach_rate_matrix.index)
        
        # Add column headers (iPhone models) - properly aligned
        header_y = y_start - 5
        for col, model in enumerate(models):
            x_pos = x_start + col * (cell_width + x_spacing)
            model_name = self.format_product_name(model, max_length=8)
            ax.text(x_pos + cell_width/2, header_y, model_name, 
                   fontsize=9, ha='center', va='center', 
                   color='#1D1D1F', weight='bold', rotation=45)
        
        # Create matrix cells with proper alignment
        for row, category in enumerate(categories):
            matrix_y = y_start - 25 - row * (cell_height + y_spacing)
            
            # Category label - properly positioned and aligned next to matrix
            ax.text(x_start - 5, matrix_y - cell_height/2, 
                   category, fontsize=9, ha='right', va='center', 
                   color='#1D1D1F', weight='medium')
            
            for col, model in enumerate(models):
                x_pos = x_start + col * (cell_width + x_spacing)
                y_pos = matrix_y - cell_height
                
                # Get attach rate and frequency
                attach_rate = attach_rate_matrix.loc[category, model]
                frequency = frequency_matrix.loc[category, model]
                
                if attach_rate > 0:
                    # Base color from category
                    base_color = self.category_colors.get(category, '#8E8E93')
                    
                    # Alpha based on attach rate (higher rate = more opaque)
                    alpha = min(1.0, max(0.4, attach_rate * 4))
                    
                    # Draw cell
                    cell_rect = FancyBboxPatch(
                        (x_pos, y_pos), cell_width, cell_height,
                        boxstyle="round,pad=1",
                        facecolor=base_color,
                        edgecolor='#86868B',
                        linewidth=1,
                        alpha=alpha
                    )
                    ax.add_patch(cell_rect)
                    
                    # Text color based on background
                    text_color = 'white' if alpha > 0.6 else 'black'
                    
                    # Clean display - just attach rate and frequency
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2 + 2, 
                           f'{attach_rate:.1%}', fontsize=9, ha='center', va='center',
                           color=text_color, weight='bold')
                    
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2 - 4, 
                           f'{frequency:.0f}', fontsize=7, ha='center', va='center',
                           color=text_color, weight='medium')
                    
                    # Add star for high attach rates
                    self.add_performance_indicator(ax, x_pos + cell_width - 3, y_pos + cell_height - 3, 
                                                 attach_rate, size=2)
                else:
                    # Find top seller from this category to repeat
                    top_seller = self._get_top_seller_for_category(iphone_data, category)
                    if top_seller:
                        # Use lighter styling for repeated top seller
                        base_color = self.category_colors.get(category, '#8E8E93')
                        
                        # Draw cell with different styling to indicate it's a repeat
                        cell_rect = FancyBboxPatch(
                            (x_pos, y_pos), cell_width, cell_height,
                            boxstyle="round,pad=1",
                            facecolor=base_color,
                            edgecolor='#86868B',
                            linewidth=1,
                            alpha=0.3,
                            linestyle='--'  # Dashed border to indicate repeat
                        )
                        ax.add_patch(cell_rect)
                        
                        # Add repeat indicator
                        ax.text(x_pos + cell_width/2, y_pos + cell_height/2 + 2, 
                               'TOP SELLER', fontsize=7, ha='center', va='center',
                               color='#666666', weight='bold')
                        
                        # Add simplified product name
                        product_name = self._format_product_name_short(top_seller['product_name'])
                        ax.text(x_pos + cell_width/2, y_pos + cell_height/2 - 3, 
                               product_name, fontsize=6, ha='center', va='center',
                               color='#666666', weight='medium')
                    else:
                        # Fallback: empty cell
                        cell_rect = FancyBboxPatch(
                            (x_pos, y_pos), cell_width, cell_height,
                            boxstyle="round,pad=1",
                            facecolor='#F8F9FA',
                            edgecolor='#E0E0E0',
                            linewidth=1,
                            alpha=0.5
                        )
                        ax.add_patch(cell_rect)
                        
                        # Add dash for no data
                        ax.text(x_pos + cell_width/2, y_pos + cell_height/2, 
                               '-', fontsize=12, ha='center', va='center',
                               color='#8E8E93', weight='bold')
    
    def _get_top_seller_for_category(self, iphone_data: pd.DataFrame, category: str) -> Dict:
        """Get the top-selling product for a specific category"""
        try:
            category_data = iphone_data[iphone_data['accessory_category'] == category]
            if len(category_data) > 0:
                top_product = category_data.nlargest(1, 'purchase_frequency').iloc[0]
                return {
                    'product_name': top_product['accessory_product'],
                    'frequency': top_product['purchase_frequency'],
                    'attach_rate': top_product['attach_rate']
                }
        except Exception:
            pass
        return None
    
    def _format_product_name_short(self, name: str) -> str:
        """Format product name for short display in matrix cells"""
        if not name:
            return ""
        
        # Remove common words and shorten
        name = name.replace('iPhone ', '').replace('Apple ', '')
        name = name.replace('Wireless ', 'W-').replace('Magnetic ', 'Mag ')
        name = name.replace('Protector', 'Prot').replace('Charger', 'Chg')
        
        # Take first word and truncate
        words = name.split()
        if words:
            return words[0][:8] + '..' if len(words[0]) > 8 else words[0]
        return name[:8]
    
    def _get_top_product_for_combination(self, category: str, model: str) -> str:
        """Get the top-selling product for a specific category-model combination"""
        try:
            iphone_data = self.data_loader.get_lob_data('iPhone')
            combo_data = iphone_data[
                (iphone_data['core_product'] == model) & 
                (iphone_data['accessory_category'] == category)
            ]
            
            if len(combo_data) > 0:
                top_product = combo_data.nlargest(1, 'purchase_frequency')['accessory_product'].iloc[0]
                return top_product
        except:
            pass
        return None
    
    def _format_accessory_name(self, name: str, max_length: int = 12) -> str:
        """Format accessory name for display in matrix cells"""
        if not name:
            return ""
        
        # Remove common words
        name = name.replace('iPhone ', '').replace('for iPhone', '')
        name = name.replace('Apple ', '').replace('Magnetic ', 'Mag ')
        name = name.replace('Wireless ', 'W-').replace('Charger', 'Chg')
        name = name.replace('Protector', 'Prot').replace('Tempered Glass', 'Glass')
        
        # Truncate if too long
        if len(name) > max_length:
            name = name[:max_length-2] + '..'
        
        return name
    
    def _add_insights_panel(self, ax, top_cohort_pairs: List[Dict], 
                           summary_stats: Dict, x_pos: int, y_pos: int) -> None:
        """Add insights panel with key statistics and recommendations"""
        self.add_section_label(ax, "COHORT INSIGHTS", x_pos, y_pos + 70, ha='left')
        
        # Top Cohort Pairs
        ax.text(x_pos, y_pos + 55, "Top Cohort Pairs:", fontsize=11, fontweight='bold', color=self.text_color, ha='left')
        y_offset = y_pos + 45
        for i, pair in enumerate(top_cohort_pairs[:5]):
            text = f"• {pair['core_product']} + {pair['accessory_category']}: {pair['attach_rate']:.1%}"
            ax.text(x_pos, y_offset - i * 5, text, fontsize=10, color=self.text_color, ha='left')
        
        # Summary Statistics
        ax.text(x_pos, y_pos + 15, "Summary Statistics:", fontsize=11, fontweight='bold', color=self.text_color, ha='left')
        stats = [
            f"Total Combinations: {summary_stats['total_records']:,}",
            f"Avg Attach Rate: {summary_stats['avg_attach_rate']:.1%}",
            f"High Attach Items: {summary_stats['high_attach_count']}",
            f"Total Core Products: {summary_stats['unique_core_products']}",
            f"Total Categories: {summary_stats['unique_categories']}"
        ]
        for i, stat in enumerate(stats):
            ax.text(x_pos, y_pos + 5 - i * 5, stat, fontsize=10, color=self.text_color, ha='left')
    
    def _add_recommended_layout(self, ax, top_models: List[str], 
                               top_categories: List[str], x_pos: int, y_pos: int) -> None:
        """Add recommended planogram layout based on cohort insights"""
        self.add_section_label(ax, "RECOMMENDED LAYOUT", x_pos, y_pos + 45, ha='left')
        
        # Create a more sophisticated planogram representation
        shelf_width = 75
        shelf_height = 8
        shelf_spacing = 2
        
        # Define shelf layout (eye level = middle shelves)
        shelves = [
            {'name': 'Top Shelf', 'products': ['Low-attach accessories', 'Seasonal items'], 'color': '#E5E5EA'},
            {'name': 'Eye Level 1', 'products': ['iPhone 16 Pro Max', 'iPhone 16 Pro'], 'color': '#007AFF'},
            {'name': 'Eye Level 2', 'products': ['High-attach accessories', 'Screen protectors'], 'color': '#34C759'},
            {'name': 'Mid Level', 'products': ['iPhone 16', 'iPhone 15 series'], 'color': '#FF9500'},
            {'name': 'Bottom Shelf', 'products': ['Cross-sell items', 'Cables & adapters'], 'color': '#8E8E93'}
        ]
        
        current_y = y_pos + 25
        
        # Draw shelves
        for shelf in shelves:
            # Draw shelf background
            shelf_rect = FancyBboxPatch(
                (x_pos, current_y), shelf_width, shelf_height,
                boxstyle="round,pad=1",
                facecolor=shelf['color'],
                edgecolor='#86868B',
                linewidth=1,
                alpha=0.8
            )
            ax.add_patch(shelf_rect)
            
            # Add shelf label
            ax.text(x_pos - 2, current_y + shelf_height/2, shelf['name'],
                    ha='right', va='center', fontsize=7, color='#1D1D1F', weight='medium')
            
            # Add product examples
            product_text = ', '.join(shelf['products'][:2])  # Show first 2 products
            if len(shelf['products']) > 2:
                product_text += '...'
            
            ax.text(x_pos + shelf_width/2, current_y + shelf_height/2, product_text,
                    ha='center', va='center', fontsize=7, color='white', weight='medium')
            
            current_y -= (shelf_height + shelf_spacing)
        
        # Add merchandising principles
        principles = [
            "Eye Level = Buy Level",
            "High-attach next to core",
            "Color-coded categories",
            "Cross-sell at bottom"
        ]
        
        ax.text(x_pos, y_pos - 15, "MERCHANDISING PRINCIPLES:", 
                fontsize=8, fontweight='bold', color=self.text_color, ha='left')
        
        for i, principle in enumerate(principles):
            ax.text(x_pos, y_pos - 25 - i*8, principle, fontsize=7, color=self.text_color, va='center', ha='left')
    
    def _generate_product_list(self, top_models: List[str], top_categories: List[str], 
                              store_type: str) -> None:
        """Generate detailed product list for each iPhone model + accessory category combination"""
        self.logger.info("Generating detailed product list for iPhone cohort combinations")
        
        # Load iPhone data
        iphone_data = self.data_loader.get_lob_data('iPhone')
        
        # Create output file
        output_path = self.output_dir / f"iphone_cohort_products_{store_type}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("iPhone Cohort-Based Product List\n")
            f.write("=" * 50 + "\n")
            f.write(f"Store Type: {store_type.title()}\n")
            f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # For each iPhone model
            for model in top_models:
                f.write(f"\n{model}\n")
                f.write("-" * (len(model) + 5) + "\n")
                
                model_data = iphone_data[iphone_data['core_product'] == model]
                
                # For each accessory category
                for category in top_categories:
                    category_data = model_data[model_data['accessory_category'] == category]
                    
                    if len(category_data) == 0:
                        f.write(f"\n{category}: No products available\n")
                        continue
                    
                    # Sort by attach rate descending
                    category_data = category_data.sort_values('attach_rate', ascending=False)
                    
                    # Get top products for this combination
                    top_products = category_data.head(5)  # Top 5 products
                    
                    avg_attach_rate = category_data['attach_rate'].mean()
                    total_frequency = category_data['purchase_frequency'].sum()
                    
                    f.write(f"\n{category} (Avg Attach Rate: {avg_attach_rate:.1%})\n")
                    f.write(f"   Total Sales: {total_frequency:,.0f}\n")
                    f.write(f"   Recommended Products:\n")
                    
                    for i, (_, product) in enumerate(top_products.iterrows(), 1):
                        attach_rate = product['attach_rate']
                        frequency = product['purchase_frequency']
                        facings = product['recommended_facings']
                        product_name = product['accessory_product']
                        
                        # Performance indicator
                        if attach_rate > 0.15:
                            indicator = "***"
                        elif attach_rate > 0.08:
                            indicator = "**"
                        elif attach_rate > 0.03:
                            indicator = "*"
                        else:
                            indicator = "-"
                        
                        f.write(f"   {i}. {indicator} {product_name}\n")
                        f.write(f"      Attach Rate: {attach_rate:.1%} | Sales: {frequency:,.0f} | Facings: {facings}\n")
                    
                    f.write("\n")
            
            # Add summary section
            f.write("\n" + "=" * 50 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 50 + "\n")
            
            # Overall top combinations
            f.write("\nTop Overall Combinations (All Models):\n")
            f.write("-" * 40 + "\n")
            
            top_combinations = iphone_data[
                (iphone_data['core_product'].isin(top_models)) &
                (iphone_data['accessory_category'].isin(top_categories))
            ].nlargest(10, 'attach_rate')
            
            for i, (_, combo) in enumerate(top_combinations.iterrows(), 1):
                model = combo['core_product']
                category = combo['accessory_category']
                product_name = combo['accessory_product']
                attach_rate = combo['attach_rate']
                frequency = combo['purchase_frequency']
                
                f.write(f"{i:2d}. {model} + {product_name}\n")
                f.write(f"     Category: {category} | Attach Rate: {attach_rate:.1%} | Sales: {frequency:,.0f}\n\n")
            
            # Performance tiers
            f.write("\nPerformance Indicators:\n")
            f.write("-" * 25 + "\n")
            f.write("*** High Performance: >15% attach rate\n")
            f.write("** Medium Performance: 8-15% attach rate\n")
            f.write("* Low Performance: 3-8% attach rate\n")
            f.write("- Very Low Performance: <3% attach rate\n")
            
            # Category summary
            f.write("\nCategory Performance Summary:\n")
            f.write("-" * 35 + "\n")
            
            for category in top_categories:
                category_data = iphone_data[
                    (iphone_data['core_product'].isin(top_models)) &
                    (iphone_data['accessory_category'] == category)
                ]
                
                if len(category_data) > 0:
                    avg_attach = category_data['attach_rate'].mean()
                    total_sales = category_data['purchase_frequency'].sum()
                    product_count = len(category_data)
                    
                    f.write(f"• {category}: {avg_attach:.1%} avg attach rate | {total_sales:,.0f} total sales | {product_count} products\n")
        
        self.logger.info(f"Generated detailed product list: {output_path}")
        print(f"Detailed product list generated: {output_path}")

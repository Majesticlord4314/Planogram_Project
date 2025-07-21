"""
Watch Cohort-Based Planogram Generator
"""

from pathlib import Path
from .base import CohortPlanogramBase, StoreTemplateLoader
from .data_loader import CohortDataLoader

class WatchCohortPlanogram(CohortPlanogramBase):
    """Generate Watch cohort-based planograms"""
    
    def __init__(self):
        super().__init__('Watch')
        self.data_loader = CohortDataLoader()
        self.store_template_loader = StoreTemplateLoader()
        
    def generate_cohort_planogram(self, store_type: str) -> Path:
        """Generate comprehensive Watch cohort planogram"""
        self.logger.info(f"Generating Watch cohort planogram for {store_type} store")
        
        # Load Watch cohort data
        watch_data = self.data_loader.get_lob_data('Watch')
        
        # Get Watch cohort data and matrices (same structure as iPhone)
        try:
            # Get store-specific matrix configuration
            matrix_config = self.store_template_loader.get_matrix_config(store_type)
            
            top_models = self.data_loader.get_top_core_products('Watch', limit=matrix_config['max_models'])
            top_categories = self.data_loader.get_top_accessory_categories('Watch', limit=matrix_config['max_categories'])
            
            # Get cohort matrices
            attach_rate_matrix = self.data_loader.get_cohort_matrix('Watch', top_models, top_categories)
            frequency_matrix = self.data_loader.get_frequency_matrix('Watch', top_models, top_categories)
            
            # Fill missing values with 0
            attach_rate_matrix = attach_rate_matrix.fillna(0)
            frequency_matrix = frequency_matrix.fillna(0)
            
            # Get insights
            top_cohort_pairs = self.data_loader.get_top_cohort_pairs('Watch', limit=8)
            summary_stats = self.data_loader.get_lob_summary_stats('Watch')
            
        except Exception as e:
            self.logger.warning(f"Could not load complete Watch data: {e}")
            # Create fallback with simple data
            top_models = watch_data.groupby('core_product')['purchase_frequency'].sum().sort_values(ascending=False).head(4).index.tolist()
            top_categories = watch_data.groupby('accessory_category')['attach_rate'].mean().sort_values(ascending=False).head(6).index.tolist()
            attach_rate_matrix = watch_data.pivot_table(values='attach_rate', index='accessory_category', columns='core_product', aggfunc='mean').fillna(0)
            frequency_matrix = watch_data.pivot_table(values='purchase_frequency', index='accessory_category', columns='core_product', aggfunc='sum').fillna(0)
            top_cohort_pairs = []
            summary_stats = {'avg_attach_rate': watch_data['attach_rate'].mean()}

        # Create figure with store-specific dimensions (same as iPhone)
        fig, ax = self.create_figure(store_type)
        
        # Get store-specific layout positions (same as iPhone)
        layout_positions = self.store_template_loader.get_layout_positions(store_type)
        core_product_config = self.store_template_loader.get_core_product_config(store_type)
        
        # Add title
        self.add_title(ax, f"Watch Cohort Planogram - {store_type.title()} Store", y_pos=layout_positions['title_y'])
        
        # Create core product zones (same structure as iPhone)
        self._create_core_product_zones(ax, watch_data, top_models, store_type, **core_product_config)
        
        # Create cohort matrix (same structure as iPhone)
        self._create_cohort_matrix(ax, attach_rate_matrix, frequency_matrix, watch_data, store_type, y_start=layout_positions['matrix_y'])
        
        # Add insights panel (same structure as iPhone)
        self._add_insights_panel(ax, top_cohort_pairs, summary_stats, x_pos=layout_positions['insights_x'], y_pos=layout_positions['insights_y'])
        
        # Add recommended layout (same structure as iPhone)
        self._add_recommended_layout(ax, top_models, top_categories, x_pos=layout_positions['recommended_x'], y_pos=layout_positions['recommended_y'])
        
        # Add legend (same structure as iPhone)
        self.create_legend(ax, top_categories, x_pos=layout_positions['legend_x'], y_pos=layout_positions['legend_y'])
        
        # Generate detailed product list
        self._generate_product_list(top_models, top_categories, store_type)
        
        # Save planogram
        filename = f"watch_cohort_detailed_{store_type}.png"
        planogram_path = self.save_planogram(fig, filename)
        
        return planogram_path
    
    def _create_core_product_zones(self, ax, watch_data, top_models, store_type,
                                  zone_width: int, zone_height: int, 
                                  x_start: int, y_start: int, x_spacing: int) -> None:
        """Create Watch core product zones with performance indicators (same as iPhone)"""
        self.add_section_label(ax, "CORE PRODUCTS", x_start, y_start + 10, ha='left')
        
        for i, model in enumerate(top_models):
            x_pos = x_start + i * (zone_width + x_spacing)
            
            # Get model statistics
            model_data = watch_data[watch_data['core_product'] == model]
            total_sales = model_data['purchase_frequency'].sum()
            avg_attach_rate = model_data['attach_rate'].mean()
            
            # Color based on performance
            color = self.get_performance_color(avg_attach_rate)
            
            # Draw zone
            from matplotlib.patches import FancyBboxPatch
            zone_rect = FancyBboxPatch(
                (x_pos, y_start), zone_width, zone_height,
                boxstyle="round,pad=3",
                facecolor=color,
                edgecolor='#86868B',
                linewidth=1.5,
                alpha=0.9
            )
            ax.add_patch(zone_rect)
            
            # Add model name (formatted for Watch)
            model_name = model.replace('Apple Watch ', '').replace('Watch ', '')[:8]
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

    def _create_cohort_matrix(self, ax, attach_rate_matrix, frequency_matrix, watch_data, store_type, y_start: int) -> None:
        """Create clean cohort matrix showing Watch models vs accessories (same as iPhone)"""
        self.add_section_label(ax, "COHORT MATRIX", 20, y_start + 15)
        
        # Get store-specific matrix configuration
        matrix_config = self.store_template_loader.get_matrix_config(store_type)
        cell_width = matrix_config['cell_width']
        cell_height = matrix_config['cell_height']
        x_spacing = matrix_config['x_spacing']
        y_spacing = matrix_config['y_spacing']
        x_start = matrix_config['x_start']
        
        # Calculate starting positions
        models = list(attach_rate_matrix.columns)
        categories = list(attach_rate_matrix.index)
        
        # Add column headers (Watch models) - properly aligned
        header_y = y_start - 5
        for col, model in enumerate(models):
            x_pos = x_start + col * (cell_width + x_spacing)
            model_name = model.replace('Apple Watch ', '').replace('Watch ', '')[:8]
            ax.text(x_pos + cell_width/2, header_y, model_name, 
                   fontsize=9, ha='center', va='center', 
                   color='#1D1D1F', weight='bold', rotation=45)
        
        # Create matrix cells with proper alignment
        for row, category in enumerate(categories):
            matrix_y = y_start - 25 - row * (cell_height + y_spacing)
            
            # Category label
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
                    
                    # Adjust intensity based on attach rate
                    intensity = min(attach_rate * 4, 1.0)  # Scale for visibility
                    
                    # Draw cell
                    from matplotlib.patches import FancyBboxPatch
                    cell_rect = FancyBboxPatch(
                        (x_pos, y_pos), cell_width, cell_height,
                        boxstyle="round,pad=1",
                        facecolor=base_color,
                        alpha=intensity,
                        edgecolor='white',
                        linewidth=1
                    )
                    ax.add_patch(cell_rect)
                    
                    # Add attach rate text
                    text_color = 'white' if intensity > 0.5 else '#1D1D1F'
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2 + 1, 
                           f'{attach_rate:.1%}', fontsize=7, ha='center', va='center',
                           color=text_color, weight='bold')
                    
                    # Add frequency below
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2 - 3, 
                           f'{frequency:,.0f}', fontsize=5, ha='center', va='center',
                           color=text_color, weight='medium')
                    
                    # Add performance indicator
                    if attach_rate > 0.10:  # High performance threshold
                        indicator_color = '#FFD60A'  # Gold star
                        ax.text(x_pos + cell_width - 3, y_pos + cell_height - 3, '●', 
                               fontsize=6, ha='center', va='center', color=indicator_color)

    def _add_insights_panel(self, ax, top_cohort_pairs, summary_stats, x_pos: int, y_pos: int) -> None:
        """Add insights panel with key Watch cohort findings (same as iPhone)"""
        self.add_section_label(ax, "COHORT INSIGHTS", x_pos, y_pos + 70, ha='left')
        
        # Top Cohort Pairs
        ax.text(x_pos, y_pos + 55, "Top Cohort Pairs:", fontsize=11, fontweight='bold', color=self.text_color, ha='left')
        y_offset = y_pos + 45
        for i, pair in enumerate(top_cohort_pairs[:5]):
            if isinstance(pair, dict):
                core_name = str(pair['core_product']).replace('Apple Watch ', '').replace('Watch ', '')[:10]
                text = f"• {core_name} + {pair['accessory_category']}: {pair['attach_rate']:.1%}"
            else:
                # Fallback for tuple format
                text = f"• Watch + Accessory: N/A"
            ax.text(x_pos, y_offset - i * 5, text, fontsize=10, color=self.text_color, ha='left')
        
        # Summary Statistics
        ax.text(x_pos, y_pos + 15, "Summary Statistics:", fontsize=11, fontweight='bold', color=self.text_color, ha='left')
        stats = [
            f"Total Combinations: {summary_stats.get('total_records', 0):,}",
            f"Avg Attach Rate: {summary_stats.get('avg_attach_rate', 0):.1%}",
            f"High Attach Items: {summary_stats.get('high_attach_count', 0)}",
            f"Total Core Products: {summary_stats.get('unique_core_products', 0)}",
            f"Total Categories: {summary_stats.get('unique_categories', 0)}"
        ]
        for i, stat in enumerate(stats):
            ax.text(x_pos, y_pos + 5 - i * 5, stat, fontsize=10, color=self.text_color, ha='left')

    def _add_recommended_layout(self, ax, top_models, top_categories, x_pos: int, y_pos: int) -> None:
        """Add recommended store layout section (same as iPhone)"""
        self.add_section_label(ax, "RECOMMENDED LAYOUT", x_pos, y_pos)
        
        # Zone placement recommendations
        recommendations = [
            "Eye Level: Top Watch Models",
            "High-attach next to core",
            "Group complementary",
            "Cross-merchandise by use case"
        ]
        
        for i, recommendation in enumerate(recommendations):
            ax.text(x_pos, y_pos - 15 - i*10, f"• {recommendation}",
                   fontsize=8, color=self.text_color)
    
    def _generate_product_list(self, top_models: list, top_categories: list, 
                              store_type: str) -> None:
        """Generate detailed product list for each Watch model + accessory category combination"""
        self.logger.info("Generating detailed product list for Watch cohort combinations")
        
        # Load Watch cohort data
        watch_data = self.data_loader.get_lob_data('Watch')
        
        output_path = self.output_dir / f"watch_cohort_products_{store_type}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Watch Cohort-Based Product List\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Store Type: {store_type.title()}\n")
            f.write(f"Generated for top {len(top_models)} Watch models and {len(top_categories)} accessory categories\n\n")
            
            # Write top performing Watch models
            f.write("TOP PERFORMING WATCH MODELS:\n")
            f.write("-" * 30 + "\n")
            for i, model in enumerate(top_models, 1):
                model_data = watch_data[watch_data['core_product'] == model]
                total_sales = model_data['purchase_frequency'].sum()
                avg_attach_rate = model_data['attach_rate'].mean()
                f.write(f"{i}. {model}\n")
                f.write(f"   Sales Volume: {total_sales:,.0f} units\n")
                f.write(f"   Avg Attach Rate: {avg_attach_rate:.1%}\n\n")
            
            # Write top accessory categories
            f.write("TOP ACCESSORY CATEGORIES:\n")
            f.write("-" * 25 + "\n")
            for i, category in enumerate(top_categories, 1):
                category_data = watch_data[watch_data['accessory_category'] == category]
                avg_attach_rate = category_data['attach_rate'].mean()
                combinations_count = len(category_data)
                f.write(f"{i}. {category}\n")
                f.write(f"   Avg Attach Rate: {avg_attach_rate:.1%}\n")
                f.write(f"   Watch Combinations: {combinations_count}\n\n")
            
            # Write detailed combinations
            f.write("DETAILED PRODUCT COMBINATIONS:\n")
            f.write("-" * 35 + "\n")
            
            for model in top_models:
                f.write(f"\n{model}:\n")
                model_data = watch_data[watch_data['core_product'] == model]
                
                for category in top_categories:
                    combo_data = model_data[model_data['accessory_category'] == category]
                    if len(combo_data) > 0:
                        avg_attach_rate = combo_data['attach_rate'].mean()
                        total_sales = combo_data['purchase_frequency'].sum()
                        
                        if avg_attach_rate > 0.01:  # Only include meaningful combinations
                            f.write(f"  + {category}: {avg_attach_rate:.1%} attach rate, {total_sales:,.0f} units\n")
                            
                            # List specific accessories in this category
                            unique_accessories = combo_data['accessory_product'].unique()
                            for accessory in sorted(unique_accessories)[:3]:  # Top 3 accessories
                                acc_data = combo_data[combo_data['accessory_product'] == accessory]
                                if len(acc_data) > 0:
                                    acc_attach_rate = acc_data['attach_rate'].iloc[0]
                                    f.write(f"    - {accessory} ({acc_attach_rate:.1%})\n")
            
            # Write summary statistics
            f.write(f"\nSUMMARY STATISTICS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Watch Combinations Analyzed: {len(watch_data)}\n")
            f.write(f"Average Attach Rate: {watch_data['attach_rate'].mean():.1%}\n")
            f.write(f"Highest Attach Rate: {watch_data['attach_rate'].max():.1%}\n")
            f.write(f"High Performance Combinations (>10%): {len(watch_data[watch_data['attach_rate'] > 0.10])}\n")
            f.write(f"Medium Performance Combinations (5-10%): {len(watch_data[(watch_data['attach_rate'] > 0.05) & (watch_data['attach_rate'] <= 0.10)])}\n")
            
        self.logger.info(f"Generated detailed product list: {output_path}")
        print("Detailed product list generated: " + str(output_path))
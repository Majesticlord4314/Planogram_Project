"""
iPad Cohort-Based Planogram Generator
"""

import pandas as pd
from typing import List
from pathlib import Path
from matplotlib.patches import FancyBboxPatch
from .base import CohortPlanogramBase, StoreTemplateLoader
from .data_loader import CohortDataLoader

class iPadCohortPlanogram(CohortPlanogramBase):
    """Generate iPad cohort-based planograms"""
    
    def __init__(self):
        super().__init__('iPad')
        self.data_loader = CohortDataLoader()
        self.store_template_loader = StoreTemplateLoader()
        
    def generate_cohort_planogram(self, store_type: str) -> Path:
        """Generate comprehensive iPad cohort planogram"""
        self.logger.info(f"Generating iPad cohort planogram for {store_type} store")
        
        # Load iPad cohort data
        try:
            ipad_data = self.data_loader.get_lob_data('iPad')
        except Exception as e:
            self.logger.warning(f"Could not load iPad cohort data: {e}")
            # Create a fallback planogram with available data
            return self._create_fallback_planogram(store_type)
        
        # Get top iPad models and accessory categories based on store type
        matrix_config = self.store_template_loader.get_matrix_config(store_type)
        
        try:
            top_models = self.data_loader.get_top_core_products('iPad', limit=matrix_config['max_models'])
            top_categories = self.data_loader.get_top_accessory_categories('iPad', limit=matrix_config['max_categories'])
            
            # Get cohort matrices
            attach_rate_matrix = self.data_loader.get_cohort_matrix('iPad', top_models, top_categories)
            frequency_matrix = self.data_loader.get_frequency_matrix('iPad', top_models, top_categories)
            
            # Fill missing values with 0
            attach_rate_matrix = attach_rate_matrix.fillna(0)
            frequency_matrix = frequency_matrix.fillna(0)
            
            # Get insights
            top_cohort_pairs = self.data_loader.get_top_cohort_pairs('iPad', limit=8)
            summary_stats = self.data_loader.get_lob_summary_stats('iPad')
            
        except Exception as e:
            self.logger.warning(f"Could not load complete iPad data: {e}")
            return self._create_fallback_planogram(store_type)
        
        # Create figure with store-specific dimensions (same as iPhone)
        fig, ax = self.create_figure(store_type)
        
        # Get store-specific layout positions (same as iPhone)
        layout_positions = self.store_template_loader.get_layout_positions(store_type)
        core_product_config = self.store_template_loader.get_core_product_config(store_type)
        
        # Add title
        self.add_title(ax, f"iPad Cohort Planogram - {store_type.title()} Store", y_pos=layout_positions['title_y'])
        
        # Create core product zones (same structure as iPhone)
        self._create_core_product_zones(ax, ipad_data, top_models, store_type, **core_product_config)
        
        # Create cohort matrix (same structure as iPhone)
        self._create_cohort_matrix(ax, attach_rate_matrix, frequency_matrix, ipad_data, store_type, y_start=layout_positions['matrix_y'])
        
        # Add insights panel (same structure as iPhone)
        self._add_insights_panel(ax, top_cohort_pairs, summary_stats, x_pos=layout_positions['insights_x'], y_pos=layout_positions['insights_y'])
        
        # Add recommended layout (same structure as iPhone)
        self._add_recommended_layout(ax, top_models, top_categories, x_pos=layout_positions['recommended_x'], y_pos=layout_positions['recommended_y'])
        
        # Add legend (same structure as iPhone)
        self.create_legend(ax, top_categories, x_pos=layout_positions['legend_x'], y_pos=layout_positions['legend_y'])
        
        # Save planogram
        filename = f"ipad_cohort_detailed_{store_type}.png"
        planogram_path = self.save_planogram(fig, filename)
        
        # Generate detailed product list
        self._generate_product_list(top_models, top_categories, store_type)
        
        return planogram_path
    
    def _create_fallback_planogram(self, store_type: str) -> Path:
        """Create a fallback planogram when data is not available"""
        self.logger.info(f"Creating fallback iPad planogram for {store_type} store")
        
        fig, ax = self.create_figure(store_type)
        self.add_title(ax, f"iPad Cohort Planogram - {store_type.title()} Store", y_pos=200)
        
        # Add informative message instead of "implementation in progress"
        message = "iPad Cohort Data Loading...\n\nThis planogram will be generated once\niPad cohort data is available.\n\nFor now, please use LOB optimization\nfor iPad product placement."
        ax.text(ax.get_xlim()[1]/2, ax.get_ylim()[1]/2, 
                message, 
                fontsize=14, ha='center', va='center', color=self.text_color,
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.7))
        
        # Add some basic iPad categories as reference
        basic_categories = ['Cases', 'Screen Protectors', 'Keyboards', 'Stands & Mounts', 'Cables & Adapters']
        y_pos = ax.get_ylim()[1] * 0.25
        
        ax.text(ax.get_xlim()[1]/2, y_pos, 
                "Common iPad Accessory Categories:\n" + " • ".join(basic_categories),
                fontsize=10, ha='center', va='center', color=self.text_color,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.7))
        
        # Save planogram
        filename = f"ipad_cohort_detailed_{store_type}.png"
        planogram_path = self.save_planogram(fig, filename)
        
        return planogram_path
    
    def _create_cohort_matrix(self, ax, attach_rate_matrix: pd.DataFrame, 
                             frequency_matrix: pd.DataFrame, ipad_data: pd.DataFrame, 
                             store_type: str, y_start: int) -> None:
        """Create clean cohort matrix showing iPad models vs accessories (same as iPhone)"""
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
        
        # Add column headers (iPad models) - properly aligned
        header_y = y_start - 5
        for col, model in enumerate(models):
            x_pos = x_start + col * (cell_width + x_spacing)
            model_name = model.replace('iPad ', '')[:8]
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
                    if attach_rate > 0.15:  # High performance threshold for iPad
                        indicator_color = '#FFD60A'  # Gold star
                        ax.text(x_pos + cell_width - 3, y_pos + cell_height - 3, '●', 
                               fontsize=6, ha='center', va='center', color=indicator_color)

    def _add_insights_panel(self, ax, top_cohort_pairs: List[tuple], 
                           summary_stats: dict, x_pos: int, y_pos: int) -> None:
        """Add insights panel with key iPad cohort findings (same as iPhone)"""
        self.add_section_label(ax, "COHORT INSIGHTS", x_pos, y_pos + 70, ha='left')
        
        # Top Cohort Pairs
        ax.text(x_pos, y_pos + 55, "Top Cohort Pairs:", fontsize=11, fontweight='bold', color=self.text_color, ha='left')
        y_offset = y_pos + 45
        for i, pair in enumerate(top_cohort_pairs[:5]):
            if isinstance(pair, dict):
                core_name = str(pair['core_product']).replace('iPad ', '')[:10]
                text = f"• {core_name} + {pair['accessory_category']}: {pair['attach_rate']:.1%}"
            else:
                # Fallback for tuple format
                text = f"• iPad + Accessory: N/A"
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

    def _add_recommended_layout(self, ax, top_models: List[str], 
                               top_categories: List[str], x_pos: int, y_pos: int) -> None:
        """Add recommended store layout section (same as iPhone)"""
        self.add_section_label(ax, "RECOMMENDED LAYOUT", x_pos, y_pos)
        
        # Zone placement recommendations
        recommendations = [
            "Eye Level: Featured iPads",
            "High-attach next to core",
            "Group complementary items",
            "Cross-merchandise by use case"
        ]
        
        for i, recommendation in enumerate(recommendations):
            ax.text(x_pos, y_pos - 15 - i*10, f"• {recommendation}",
                   fontsize=8, color=self.text_color)
    
    def _create_core_product_zones(self, ax, ipad_data: pd.DataFrame, 
                                  top_models: List[str], store_type: str,
                                  zone_width: int, zone_height: int, 
                                  x_start: int, y_start: int, x_spacing: int) -> None:
        """Create iPad core product zones with performance indicators"""
        self.add_section_label(ax, "CORE PRODUCTS", x_start, y_start + 10, ha='left')
        
        for i, model in enumerate(top_models):
            x_pos = x_start + i * (zone_width + x_spacing)
            
            # Get model statistics
            model_data = ipad_data[ipad_data['core_product'] == model]
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
                             frequency_matrix: pd.DataFrame, ipad_data: pd.DataFrame, 
                             store_type: str, y_start: int) -> None:
        """Create clean cohort matrix showing iPad models vs accessories"""
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
        
        # Create matrix cells
        for i, category in enumerate(categories):
            for j, model in enumerate(models):
                x_pos = x_start + j * (cell_width + x_spacing)
                y_pos = y_start - i * (cell_height + y_spacing)
                
                # Get values
                attach_rate = attach_rate_matrix.loc[category, model]
                frequency = frequency_matrix.loc[category, model]
                
                # Color based on attach rate
                color = self.get_performance_color(attach_rate)
                
                # Draw cell
                cell_rect = FancyBboxPatch(
                    (x_pos, y_pos), cell_width, cell_height,
                    boxstyle="round,pad=1",
                    facecolor=color,
                    edgecolor='#86868B',
                    linewidth=0.8,
                    alpha=0.9
                )
                ax.add_patch(cell_rect)
                
                # Add attach rate text
                if attach_rate > 0:
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2, 
                           f'{attach_rate:.1%}', fontsize=6, ha='center', va='center',
                           color='white', weight='bold')
        
        # Add model headers
        for j, model in enumerate(models):
            x_pos = x_start + j * (cell_width + x_spacing)
            formatted_name = self.format_product_name(model, max_length=10)
            ax.text(x_pos + cell_width/2, y_start + cell_height + 5, 
                   formatted_name, fontsize=7, ha='center', va='bottom',
                   color=self.text_color, weight='bold', rotation=0)
        
        # Add category labels
        for i, category in enumerate(categories):
            y_pos = y_start - i * (cell_height + y_spacing)
            formatted_category = self.format_product_name(category, max_length=15)
            ax.text(x_start - 5, y_pos + cell_height/2, 
                   formatted_category, fontsize=7, ha='right', va='center',
                   color=self.text_color, weight='medium')
    
    def _add_insights_panel(self, ax, top_cohort_pairs: List[tuple], 
                           summary_stats: dict, x_pos: int, y_pos: int) -> None:
        """Add insights panel with key iPad cohort findings"""
        self.add_section_label(ax, "KEY INSIGHTS", x_pos, y_pos)
        
        # Insights box
        insights_rect = FancyBboxPatch(
            (x_pos, y_pos - 80), 140, 75,
            boxstyle="round,pad=5",
            facecolor='#F2F2F7',
            edgecolor='#C7C7CC',
            linewidth=1
        )
        ax.add_patch(insights_rect)
        
        # Add top cohort pairs
        ax.text(x_pos + 5, y_pos - 10, "Top iPad Cohorts:", 
               fontsize=8, weight='bold', color=self.text_color)
        
        for i, cohort_pair in enumerate(top_cohort_pairs[:5]):
            # Handle different tuple lengths
            if len(cohort_pair) == 3:
                core, accessory, rate = cohort_pair
            elif len(cohort_pair) == 2:
                core, accessory = cohort_pair
                rate = 0.0
            else:
                continue
                
            formatted_core = self.format_product_name(str(core), max_length=12)
            formatted_accessory = self.format_product_name(str(accessory), max_length=15)
            ax.text(x_pos + 5, y_pos - 20 - i*8, 
                   f"• {formatted_core} → {formatted_accessory} ({rate:.1%})",
                   fontsize=6, color=self.text_color)
        
        # Add summary stats
        if summary_stats:
            ax.text(x_pos + 5, y_pos - 65, 
                   f"Avg Attach Rate: {summary_stats.get('avg_attach_rate', 0):.1%}",
                   fontsize=7, weight='bold', color='#007AFF')
    
    def _add_recommended_layout(self, ax, top_models: List[str], 
                               top_categories: List[str], x_pos: int, y_pos: int) -> None:
        """Add recommended store layout section"""
        self.add_section_label(ax, "RECOMMENDED LAYOUT", x_pos, y_pos)
        
        # Layout box
        layout_rect = FancyBboxPatch(
            (x_pos, y_pos - 60), 140, 55,
            boxstyle="round,pad=5",
            facecolor='#E8F5E8',
            edgecolor='#34C759',
            linewidth=1
        )
        ax.add_patch(layout_rect)
        
        # Add layout recommendations
        ax.text(x_pos + 5, y_pos - 10, "Zone Placement:", 
               fontsize=8, weight='bold', color=self.text_color)
        
        zone_recommendations = [
            "1. Featured iPad models (front)",
            "2. High-attach accessories nearby",
            "3. Group complementary items",
            "4. Cross-merchandise by use case"
        ]
        
        for i, recommendation in enumerate(zone_recommendations):
            ax.text(x_pos + 5, y_pos - 20 - i*8, recommendation,
                   fontsize=6, color=self.text_color)
    
    def _generate_product_list(self, top_models: List[str], 
                              top_categories: List[str], store_type: str) -> None:
        """Generate detailed product list for each iPad model + accessory category combination"""
        self.logger.info("Generating detailed product list for iPad cohort combinations")
        
        # Load iPad cohort data
        ipad_data = self.data_loader.get_lob_data('iPad')
        
        output_path = self.output_dir / f"ipad_cohort_products_{store_type}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("iPad Cohort-Based Product List\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Store Type: {store_type.title()}\n")
            f.write(f"Generated for top {len(top_models)} iPad models and {len(top_categories)} accessory categories\n\n")
            
            # Write top performing iPad models
            f.write("TOP PERFORMING IPAD MODELS:\n")
            f.write("-" * 30 + "\n")
            for i, model in enumerate(top_models, 1):
                model_data = ipad_data[ipad_data['core_product'] == model]
                total_sales = model_data['purchase_frequency'].sum()
                avg_attach_rate = model_data['attach_rate'].mean()
                f.write(f"{i}. {model}\n")
                f.write(f"   Sales Volume: {total_sales:,.0f} units\n")
                f.write(f"   Avg Attach Rate: {avg_attach_rate:.1%}\n\n")
            
            # Write top accessory categories
            f.write("TOP ACCESSORY CATEGORIES:\n")
            f.write("-" * 25 + "\n")
            for i, category in enumerate(top_categories, 1):
                category_data = ipad_data[ipad_data['accessory_category'] == category]
                avg_attach_rate = category_data['attach_rate'].mean()
                combinations_count = len(category_data)
                f.write(f"{i}. {category}\n")
                f.write(f"   Avg Attach Rate: {avg_attach_rate:.1%}\n")
                f.write(f"   iPad Combinations: {combinations_count}\n\n")
            
            # Write summary statistics
            f.write(f"\nSUMMARY STATISTICS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total iPad Combinations Analyzed: {len(ipad_data)}\n")
            f.write(f"Average Attach Rate: {ipad_data['attach_rate'].mean():.1%}\n")
            f.write(f"Highest Attach Rate: {ipad_data['attach_rate'].max():.1%}\n")
            f.write(f"High Performance Combinations (>15%): {len(ipad_data[ipad_data['attach_rate'] > 0.15])}\n")
            f.write(f"Medium Performance Combinations (8-15%): {len(ipad_data[(ipad_data['attach_rate'] > 0.08) & (ipad_data['attach_rate'] <= 0.15)])}\n")
            
        self.logger.info(f"Generated detailed product list: {output_path}")
        print("Detailed product list generated: " + str(output_path))
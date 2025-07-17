"""
Mac Cohort-Based Planogram Generator
"""

from pathlib import Path
from matplotlib.patches import FancyBboxPatch
from .base import CohortPlanogramBase, StoreTemplateLoader
from .data_loader import CohortDataLoader

class MacCohortPlanogram(CohortPlanogramBase):
    """Generate Mac cohort-based planograms"""
    
    def __init__(self):
        super().__init__('Mac')
        self.data_loader = CohortDataLoader()
        self.store_template_loader = StoreTemplateLoader()
    
    def create_rounded_rect(self, xy, width, height, facecolor='#007AFF', alpha=1.0, edgecolor='#86868B'):
        """Create a rounded rectangle patch"""
        return FancyBboxPatch(
            xy, width, height,
            boxstyle="round,pad=2",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1,
            alpha=alpha
        )
        
    def generate_cohort_planogram(self, store_type: str) -> Path:
        """Generate comprehensive Mac cohort planogram"""
        self.logger.info(f"Generating Mac cohort planogram for {store_type} store")
        
        # Load Mac cohort data
        mac_data = self.data_loader.get_lob_data('Mac')
        
        if len(mac_data) == 0:
            self.logger.warning("No Mac cohort data found, creating placeholder")
            return self._create_placeholder_planogram(store_type)
        
        # Create figure
        fig, ax = self.create_figure(store_type)
        
        # Add title
        self.add_title(ax, f"Mac Cohort Planogram - {store_type.title()} Store", y_pos=280)
        
        # Get top Mac models and accessories
        top_models = mac_data.groupby('core_product')['purchase_frequency'].sum().sort_values(ascending=False).head(6).index.tolist()
        top_categories = mac_data.groupby('accessory_category')['attach_rate'].mean().sort_values(ascending=False).head(8).index.tolist()
        
        # Create Mac product zones (top section)
        self._create_mac_product_zones(ax, mac_data, top_models, y_start=240)
        
        # Create accessory matrix (middle section)
        self._create_mac_accessory_matrix(ax, mac_data, top_models, top_categories, y_start=180)
        
        # Add cohort insights (left side)
        self._add_mac_cohort_insights(ax, mac_data, x_pos=20, y_pos=120)
        
        # Add category legend (right side)
        self._add_mac_category_legend(ax, top_categories, x_pos=320, y_pos=120)
        
        # Save planogram
        filename = f"mac_cohort_detailed_{store_type}.png"
        planogram_path = self.save_planogram(fig, filename)
        
        return planogram_path
    
    def _create_placeholder_planogram(self, store_type: str) -> Path:
        """Create placeholder when no data is available"""
        fig, ax = self.create_figure(store_type)
        self.add_title(ax, f"Mac Cohort Planogram - {store_type.title()} Store", y_pos=200)
        
        ax.text(ax.get_xlim()[1]/2, ax.get_ylim()[1]/2, 
                "Mac Cohort Planogram\n(No cohort data available)", 
                fontsize=16, ha='center', va='center', color=self.text_color)
        
        filename = f"mac_cohort_detailed_{store_type}.png"
        return self.save_planogram(fig, filename)
    
    def _create_mac_product_zones(self, ax, data, top_models, y_start):
        """Create Mac product zones showing different Mac models"""
        zone_width = 50
        zone_height = 30
        x_spacing = 5
        
        # Calculate starting position to center the zones
        total_width = len(top_models) * zone_width + (len(top_models) - 1) * x_spacing
        x_start = (ax.get_xlim()[1] - total_width) / 2
        
        # Add section label
        ax.text(20, y_start + 10, "MAC MODELS", fontsize=14, fontweight='bold', color=self.text_color)
        
        for i, model in enumerate(top_models):
            x_pos = x_start + i * (zone_width + x_spacing)
            
            # Get model data
            model_data = data[data['core_product'] == model]
            total_sales = model_data['purchase_frequency'].sum()
            avg_attach_rate = model_data['attach_rate'].mean()
            
            # Color based on performance
            if avg_attach_rate > 0.15:
                color = '#007AFF'  # High performance - blue
            elif avg_attach_rate > 0.08:
                color = '#34C759'  # Medium performance - green
            else:
                color = '#8E8E93'  # Low performance - gray
            
            # Draw zone
            zone_rect = self.create_rounded_rect(
                (x_pos, y_start), zone_width, zone_height,
                facecolor=color, alpha=0.9
            )
            ax.add_patch(zone_rect)
            
            # Add model name (simplified)
            model_name = model.replace('MacBook ', '').replace('Mac ', '').replace(' Pro', ' P').replace(' Air', ' A')
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 + 3, 
                   model_name, fontsize=10, ha='center', va='center',
                   color='white', weight='bold')
            
            # Add sales info
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 - 5, 
                   f'{total_sales:,.0f} units', fontsize=8, ha='center', va='center',
                   color='white', weight='medium')
    
    def _create_mac_accessory_matrix(self, ax, data, top_models, top_categories, y_start):
        """Create matrix showing Mac accessory categories for each model"""
        cell_width = 35
        cell_height = 18
        x_spacing = 3
        y_spacing = 3
        
        # Calculate starting positions
        total_width = len(top_models) * cell_width + (len(top_models) - 1) * x_spacing
        x_start = 90  # Fixed position to leave room for labels
        
        # Add section label
        ax.text(20, y_start + 10, "ACCESSORY MATRIX", fontsize=14, fontweight='bold', color=self.text_color)
        
        for row, category in enumerate(top_categories):
            # Category label
            ax.text(x_start - 5, y_start - row * (cell_height + y_spacing) - cell_height/2, 
                   category, fontsize=9, ha='right', va='center', 
                   color=self.text_color, weight='medium')
            
            for col, model in enumerate(top_models):
                x_pos = x_start + col * (cell_width + x_spacing)
                y_pos = y_start - row * (cell_height + y_spacing) - cell_height
                
                # Get data for this model-category combination
                model_cat_data = data[(data['core_product'] == model) & 
                                     (data['accessory_category'] == category)]
                
                if len(model_cat_data) > 0:
                    avg_attach_rate = model_cat_data['attach_rate'].mean()
                    
                    # Color based on category
                    category_colors = {
                        'Hub/Adapter': '#007AFF',
                        'Case': '#34C759',
                        'Sleeve': '#FF9500',
                        'Mouse/Trackpad': '#AF52DE',
                        'Keyboard': '#FF3B30',
                        'Stand': '#FFCC00',
                        'Cable': '#FF2D92',
                        'Storage': '#00C7BE'
                    }
                    base_color = category_colors.get(category, '#8E8E93')
                    alpha = min(1.0, max(0.3, avg_attach_rate * 5))
                    
                    # Draw cell
                    cell_rect = self.create_rounded_rect(
                        (x_pos, y_pos), cell_width, cell_height,
                        facecolor=base_color, alpha=alpha
                    )
                    ax.add_patch(cell_rect)
                    
                    # Add attach rate
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2, 
                           f'{avg_attach_rate:.1%}', fontsize=8, ha='center', va='center',
                           color='white', weight='bold')
                    
                    # Add star for high attach rates
                    if avg_attach_rate > 0.15:
                        from matplotlib import patches
                        star = patches.Circle((x_pos + cell_width - 4, y_pos + cell_height - 4), 
                                            2, color='gold', alpha=0.9)
                        ax.add_patch(star)
                else:
                    # Empty cell
                    cell_rect = self.create_rounded_rect(
                        (x_pos, y_pos), cell_width, cell_height,
                        facecolor='#F2F2F7', alpha=0.5
                    )
                    ax.add_patch(cell_rect)
    
    def _add_mac_cohort_insights(self, ax, data, x_pos, y_pos):
        """Add Mac-specific cohort insights"""
        ax.text(x_pos, y_pos + 40, "MAC COHORT INSIGHTS", fontsize=12, fontweight='bold', color=self.text_color)
        
        # Top Mac cohort pairs
        top_cohorts = data.nlargest(5, 'attach_rate')[['core_product', 'accessory_category', 'attach_rate']]
        
        ax.text(x_pos, y_pos + 30, "Top Mac Cohort Pairs:", fontsize=10, fontweight='bold', color=self.text_color)
        
        for i, (_, row) in enumerate(top_cohorts.iterrows()):
            model = row['core_product'].replace('MacBook ', '').replace('Mac ', '')
            category = row['accessory_category']
            rate = row['attach_rate']
            
            ax.text(x_pos, y_pos + 20 - i*8, f"{model} + {category}: {rate:.1%}", 
                   fontsize=8, color=self.text_color)
        
        # Mac-specific stats
        total_combinations = len(data)
        avg_attach_rate = data['attach_rate'].mean()
        high_attach_count = len(data[data['attach_rate'] > 0.15])
        
        ax.text(x_pos, y_pos - 20, f"Total Mac Combinations: {total_combinations}", 
               fontsize=9, color=self.text_color)
        ax.text(x_pos, y_pos - 28, f"Avg Mac Attach Rate: {avg_attach_rate:.1%}", 
               fontsize=9, color=self.text_color)
        ax.text(x_pos, y_pos - 36, f"High Attach Items: {high_attach_count}", 
               fontsize=9, color=self.text_color)
        
        # Mac-specific insights
        ax.text(x_pos, y_pos - 50, "Key Insights:", fontsize=10, fontweight='bold', color=self.text_color)
        ax.text(x_pos, y_pos - 58, "• Hubs/Adapters have highest attach rates", fontsize=8, color=self.text_color)
        ax.text(x_pos, y_pos - 66, "• Professional users buy more accessories", fontsize=8, color=self.text_color)
        ax.text(x_pos, y_pos - 74, "• MacBook Pro drives premium accessory sales", fontsize=8, color=self.text_color)
    
    def _add_mac_category_legend(self, ax, categories, x_pos, y_pos):
        """Add legend for Mac accessory categories"""
        ax.text(x_pos, y_pos + 40, "MAC CATEGORIES", fontsize=12, fontweight='bold', color=self.text_color)
        
        category_colors = {
            'Hub/Adapter': '#007AFF',
            'Case': '#34C759',
            'Sleeve': '#FF9500',
            'Mouse/Trackpad': '#AF52DE',
            'Keyboard': '#FF3B30',
            'Stand': '#FFCC00',
            'Cable': '#FF2D92',
            'Storage': '#00C7BE'
        }
        
        for i, category in enumerate(categories):
            color = category_colors.get(category, '#8E8E93')
            
            # Draw color square
            legend_rect = self.create_rounded_rect(
                (x_pos, y_pos + 28 - i*10), 10, 8,
                facecolor=color
            )
            ax.add_patch(legend_rect)
            
            # Add category name
            ax.text(x_pos + 15, y_pos + 32 - i*10, category, 
                   fontsize=9, ha='left', va='center', color=self.text_color)
        
        # Add legend for attach rate indicators
        ax.text(x_pos, y_pos - 20, "Attach Rate Legend:", fontsize=10, fontweight='bold', color=self.text_color)
        
        # High attach rate
        from matplotlib import patches
        star = patches.Circle((x_pos + 5, y_pos - 28), 2, color='gold', alpha=0.9)
        ax.add_patch(star)
        ax.text(x_pos + 12, y_pos - 28, "> 15% (High)", 
               fontsize=8, ha='left', va='center', color=self.text_color)
        
        # Medium attach rate
        medium_rect = self.create_rounded_rect(
            (x_pos + 2, y_pos - 40), 6, 4,
            facecolor='#34C759', alpha=0.7
        )
        ax.add_patch(medium_rect)
        ax.text(x_pos + 12, y_pos - 38, "> 8% (Medium)", 
               fontsize=8, ha='left', va='center', color=self.text_color)
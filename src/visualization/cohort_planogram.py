import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import patches
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import seaborn as sns

class CohortPlanogramGenerator:
    """Generate cohort-based planograms showing LOB-accessory relationships"""
    
    def __init__(self):
        self.cohort_file = Path("data/raw/cohorts/planogram_cohorts_corrected.csv")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Color schemes for different categories
        self.category_colors = {
            'Case': '#007AFF',
            'Screen Protector': '#34C759',
            'Cable': '#FF9500',
            'Charger/Adapter': '#FF3B30',
            'Wireless Charger': '#AF52DE',
            'Car Mount': '#FFCC00',
            'PopSocket': '#FF2D92',
            'Power Bank': '#8E8E93',
            'Headphones': '#00C7BE',
            'Cleaning Kit': '#A2845E',
            'Ring Holder': '#5856D6',
            'Wallet': '#32ADE6',
            'Stand': '#FF6B35',
            'Tracking': '#6AC4DC',
            'Apple Pencil': '#1D1D1F',
            'Keyboard': '#48484A',
            'Mouse/Trackpad': '#636366',
            'Watch Band': '#F2F2F7',
            'Hooks/Holders': '#D1D1D6',
            'Hub/Adapter': '#8E8E93',
            'Sleeve': '#E5E5EA',
            'Bag': '#F2F2F7',
            'Storage': '#D1D1D6',
            'Privacy Filter': '#A2845E',
            'Peripheral': '#636366'
        }
        
        # High attach rate thresholds
        self.high_attach_threshold = 0.15
        self.medium_attach_threshold = 0.08
    
    def generate_cohort_planogram(self, lob: str, store_type: str = 'flagship') -> None:
        """Generate cohort-based planogram for a specific LOB"""
        print(f"Generating cohort planogram for {lob} - {store_type} store...")
        
        # Load corrected cohort data
        df = pd.read_csv(self.cohort_file)
        lob_data = df[df['lob'] == lob]
        
        if len(lob_data) == 0:
            print(f"No data found for LOB: {lob}")
            return
        
        # Generate planogram based on LOB type
        if lob == 'iPhone':
            self._generate_iphone_cohort_planogram(lob_data, store_type)
        elif lob == 'iPad':
            self._generate_ipad_cohort_planogram(lob_data, store_type)
        elif lob == 'Mac':
            self._generate_mac_cohort_planogram(lob_data, store_type)
        elif lob == 'Watch':
            self._generate_watch_cohort_planogram(lob_data, store_type)
        elif lob == 'AirPods':
            self._generate_airpods_cohort_planogram(lob_data, store_type)
        else:
            print(f"Unsupported LOB: {lob}")
    
    def _generate_iphone_cohort_planogram(self, data: pd.DataFrame, store_type: str) -> None:
        """Generate iPhone cohort planogram organized by core products and accessories"""
        
        # Get top iPhone models by total accessory sales
        model_sales = data.groupby('core_product')['purchase_frequency'].sum().sort_values(ascending=False)
        top_models = model_sales.head(6).index.tolist()
        
        # Get top accessory categories by attach rate
        category_stats = data.groupby('accessory_category').agg({
            'attach_rate': 'mean',
            'purchase_frequency': 'sum'
        }).sort_values('attach_rate', ascending=False)
        
        # Create figure with optimized layout
        fig, ax = plt.subplots(figsize=(24, 18))
        ax.set_facecolor('#F8F9FA')
        ax.set_xlim(0, 380)
        ax.set_ylim(0, 280)
        ax.axis('off')
        
        # Title
        ax.text(190, 265, f"iPhone Cohort Planogram - {store_type.title()} Store", 
                fontsize=22, fontweight='bold', ha='center', va='center', color='#1D1D1F')
        
        # Create core product zones (smaller, on right side)
        self._create_iphone_core_zones(ax, data, top_models, y_start=240, x_start=240, zone_width=22, zone_height=12)
        
        # Create accessory categories matrix (main center)
        self._create_accessory_matrix(ax, data, top_models, category_stats.index.tolist(), y_start=200)
        
        # Add cohort insights (left side)
        self._add_cohort_insights(ax, data, x_pos=20, y_pos=60)
        
        # Add legend (far right side)
        self._add_category_legend(ax, category_stats.index.tolist()[:8], x_pos=310, y_pos=100)
        
        # Save planogram
        output_path = self.output_dir / f"iphone_cohort_{store_type}.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"Saved iPhone cohort planogram: {output_path}")
    
    def _create_iphone_core_zones(self, ax, data: pd.DataFrame, top_models: List[str], y_start: int, 
                                 x_start: int = None, zone_width: int = 45, zone_height: int = 25) -> None:
        """Create core product zones showing iPhone models"""
        x_spacing = 3
        
        # Calculate starting position to center the zones if not provided
        if x_start is None:
            total_width = len(top_models) * zone_width + (len(top_models) - 1) * x_spacing
            x_start = (320 - total_width) / 2
        
        # Add section label
        ax.text(x_start if x_start else 20, y_start + 5, "CORE PRODUCTS", fontsize=14, fontweight='bold', color='#1D1D1F', ha='left')
        
        for i, model in enumerate(top_models):
            x_pos = x_start + i * (zone_width + x_spacing)
            
            # Get model data
            model_data = data[data['core_product'] == model]
            total_sales = model_data['purchase_frequency'].sum()
            avg_attach_rate = model_data['attach_rate'].mean()
            
            # Color based on performance
            if avg_attach_rate > self.high_attach_threshold:
                color = '#007AFF'
            elif avg_attach_rate > self.medium_attach_threshold:
                color = '#34C759'
            else:
                color = '#8E8E93'
            
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
            
            # Add model name (simplified)
            model_name = model.replace('iPhone ', '').replace(' Pro Max', ' PM').replace(' Plus', ' +')
            # Adjust font size based on zone size
            font_size = 8 if zone_width < 30 else 10
            sales_font_size = 6 if zone_width < 30 else 8
            
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 + 2, 
                   model_name, fontsize=font_size, ha='center', va='center',
                   color='white', weight='bold')
            
            # Add sales info
            ax.text(x_pos + zone_width/2, y_start + zone_height/2 - 3, 
                   f'{total_sales:,}', fontsize=sales_font_size, ha='center', va='center',
                   color='white', weight='medium')
    
    def _create_accessory_matrix(self, ax, data: pd.DataFrame, top_models: List[str], 
                                top_categories: List[str], y_start: int) -> None:
        """Create matrix showing accessory categories for each core product"""
        
        # Matrix dimensions
        cell_width = 32
        cell_height = 16
        x_spacing = 3
        y_spacing = 3
        
        # Calculate starting positions
        total_width = len(top_models) * cell_width + (len(top_models) - 1) * x_spacing
        x_start = 90  # Fixed position to leave room for labels
        
        # Show top 8 categories
        display_categories = top_categories[:8]
        
        for row, category in enumerate(display_categories):
            # Category label - positioned next to matrix
            ax.text(x_start - 5, y_start - row * (cell_height + y_spacing) - cell_height/2, 
                   category, fontsize=9, ha='right', va='center', 
                   color='#1D1D1F', weight='medium')
            
            for col, model in enumerate(top_models):
                x_pos = x_start + col * (cell_width + x_spacing)
                y_pos = y_start - row * (cell_height + y_spacing) - cell_height
                
                # Get data for this model-category combination
                model_cat_data = data[(data['core_product'] == model) & 
                                     (data['accessory_category'] == category)]
                
                if len(model_cat_data) > 0:
                    avg_attach_rate = model_cat_data['attach_rate'].mean()
                    total_frequency = model_cat_data['purchase_frequency'].sum()
                    
                    # Color intensity based on attach rate
                    base_color = self.category_colors.get(category, '#8E8E93')
                    alpha = min(1.0, max(0.3, avg_attach_rate * 5))  # Scale alpha by attach rate
                    
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
                    
                    # Add attach rate
                    ax.text(x_pos + cell_width/2, y_pos + cell_height/2, 
                           f'{avg_attach_rate:.1%}', fontsize=8, ha='center', va='center',
                           color='white', weight='bold')
                    
                    # Add star for high attach rates
                    if avg_attach_rate > self.high_attach_threshold:
                        star = patches.Circle((x_pos + cell_width - 4, y_pos + cell_height - 4), 
                                            2, color='gold', alpha=0.9)
                        ax.add_patch(star)
                else:
                    # Empty cell
                    cell_rect = FancyBboxPatch(
                        (x_pos, y_pos), cell_width, cell_height,
                        boxstyle="round,pad=1",
                        facecolor='#F2F2F7',
                        edgecolor='#D1D1D6',
                        linewidth=1,
                        alpha=0.5
                    )
                    ax.add_patch(cell_rect)
    
    def _add_cohort_insights(self, ax, data: pd.DataFrame, x_pos: int, y_pos: int) -> None:
        """Add cohort insights and statistics"""
        ax.text(x_pos, y_pos + 30, "COHORT INSIGHTS", fontsize=12, fontweight='bold', color='#1D1D1F')
        
        # Top cohort pairs
        top_cohorts = data.nlargest(5, 'attach_rate')[['core_product', 'accessory_category', 'attach_rate']]
        
        ax.text(x_pos, y_pos + 20, "Top Cohort Pairs:", fontsize=10, fontweight='bold', color='#1D1D1F')
        
        for i, (_, row) in enumerate(top_cohorts.iterrows()):
            model = row['core_product'].replace('iPhone ', '')
            category = row['accessory_category']
            rate = row['attach_rate']
            
            ax.text(x_pos, y_pos + 10 - i*8, f"{model} + {category}: {rate:.1%}", 
                   fontsize=8, color='#1D1D1F')
        
        # Overall stats
        total_combinations = len(data)
        avg_attach_rate = data['attach_rate'].mean()
        high_attach_count = len(data[data['attach_rate'] > self.high_attach_threshold])
        
        ax.text(x_pos, y_pos - 30, f"Total Combinations: {total_combinations}", 
               fontsize=9, color='#1D1D1F')
        ax.text(x_pos, y_pos - 38, f"Avg Attach Rate: {avg_attach_rate:.1%}", 
               fontsize=9, color='#1D1D1F')
        ax.text(x_pos, y_pos - 46, f"High Attach Items: {high_attach_count}", 
               fontsize=9, color='#1D1D1F')
    
    def _add_category_legend(self, ax, categories: List[str], x_pos: int, y_pos: int) -> None:
        """Add legend for accessory categories"""
        ax.text(x_pos, y_pos + 30, "CATEGORIES", fontsize=12, fontweight='bold', color='#1D1D1F')
        
        for i, category in enumerate(categories):
            color = self.category_colors.get(category, '#8E8E93')
            
            # Draw color square
            legend_rect = Rectangle((x_pos, y_pos + 18 - i*8), 8, 6, 
                                  facecolor=color, edgecolor='#86868B', linewidth=1)
            ax.add_patch(legend_rect)
            
            # Add category name
            ax.text(x_pos + 12, y_pos + 21 - i*8, category, 
                   fontsize=8, ha='left', va='center', color='#1D1D1F')
        
        # Add legend for attach rate indicators
        ax.text(x_pos, y_pos - 30, "Attach Rate:", fontsize=10, fontweight='bold', color='#1D1D1F')
        
        # High attach rate
        star = patches.Circle((x_pos + 5, y_pos - 38), 2, color='gold', alpha=0.9)
        ax.add_patch(star)
        ax.text(x_pos + 12, y_pos - 38, f"> {self.high_attach_threshold:.0%} (High)", 
               fontsize=8, ha='left', va='center', color='#1D1D1F')
        
        # Medium attach rate
        medium_rect = Rectangle((x_pos + 2, y_pos - 48), 6, 4, 
                              facecolor='#34C759', alpha=0.7, edgecolor='#86868B', linewidth=1)
        ax.add_patch(medium_rect)
        ax.text(x_pos + 12, y_pos - 46, f"> {self.medium_attach_threshold:.0%} (Medium)", 
               fontsize=8, ha='left', va='center', color='#1D1D1F')
    
    def _generate_ipad_cohort_planogram(self, data: pd.DataFrame, store_type: str) -> None:
        """Generate iPad cohort planogram"""
        print(f"Generating iPad cohort planogram for {store_type} store...")
        # Implementation similar to iPhone but adapted for iPad accessories
        pass
    
    def _generate_mac_cohort_planogram(self, data: pd.DataFrame, store_type: str) -> None:
        """Generate Mac cohort planogram"""
        print(f"Generating Mac cohort planogram for {store_type} store...")
        # Implementation similar to iPhone but adapted for Mac accessories
        pass
    
    def _generate_watch_cohort_planogram(self, data: pd.DataFrame, store_type: str) -> None:
        """Generate Watch cohort planogram"""
        print(f"Generating Watch cohort planogram for {store_type} store...")
        # Implementation similar to iPhone but adapted for Watch accessories
        pass
    
    def _generate_airpods_cohort_planogram(self, data: pd.DataFrame, store_type: str) -> None:
        """Generate AirPods cohort planogram"""
        print(f"Generating AirPods cohort planogram for {store_type} store...")
        # Implementation similar to iPhone but adapted for AirPods accessories
        pass

def main():
    """Generate cohort planograms for all LOBs"""
    generator = CohortPlanogramGenerator()
    
    # Generate iPhone cohort planogram
    generator.generate_cohort_planogram('iPhone', 'flagship')
    
    print("Cohort planogram generation completed!")

if __name__ == "__main__":
    main()

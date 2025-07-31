"""
Intelligent Planogram Generator
Creates professional-grade planograms with smart product placement
"""
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

def create_intelligent_cases_planogram(products, store_type='large', store_name='Smart Cases Layout', num_walls=3):
    """Create intelligent cases planogram using optimized integration"""
    try:
        # Use the optimized integration interface
        integration_path = project_root / 'src' / 'integration'
        sys.path.insert(0, str(integration_path))
        
        from optimized_cases_integration import OptimizedCasesIntegration
        
        # Initialize the integration
        integration = OptimizedCasesIntegration(str(project_root))
        
        # Generate planograms using the optimized system
        result = integration.generate_store_planograms(store_name, num_walls)
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "store_type": store_type,
                "planograms": result['planograms'],
                "generator_type": "optimized",
                "features": result['features']
            }
        else:
            # Fallback to original implementation
            print(f"Optimized generator failed: {result.get('message', 'Unknown error')}")
            return create_fallback_cases_planogram(products, store_type, store_name, num_walls)
        
    except Exception as e:
        print(f"Error using optimized integration: {e}")
        # Fallback to original implementation
        return create_fallback_cases_planogram(products, store_type, store_name, num_walls)

def create_fallback_planogram(wall_num, num_walls, store_name, output_dir, timestamp):
    """Fallback planogram creation if optimized generator fails"""
    output_path = output_dir / f"{store_name.replace(' ', '_')}_wall{wall_num}_cases_fallback_{timestamp}.png"
    details_path = output_dir / f"{store_name.replace(' ', '_')}_wall{wall_num}_details_fallback_{timestamp}.txt"
    
    # Create simple fallback visualization
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.text(0.5, 0.5, f"Fallback Planogram\nWall {wall_num} of {num_walls}\n{store_name}", 
            ha='center', va='center', fontsize=16, transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    # Create simple details file
    with open(details_path, 'w') as f:
        f.write(f"Fallback Planogram - Wall {wall_num} of {num_walls}\n")
        f.write(f"Store: {store_name}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return {
        'planogram_image': str(output_path),
        'product_details_file': str(details_path),
        'apple_count': 0,
        'tpa_count': 0,
        'other_count': 0
    }

def create_fallback_cases_planogram(products, store_type='large', store_name='Smart Cases Layout', num_walls=3):
    """Original implementation as fallback"""
    results = {}
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # Generate planograms for each wall
    for wall_num in range(1, num_walls + 1):
        # Determine focus for this wall
        if wall_num == 1:
            focus = "Apple Focus"
            apple_percentage = 0.6
        elif wall_num == 2:
            focus = "TPA Focus"
            apple_percentage = 0.4
        else:
            focus = "Balanced"
            apple_percentage = 0.5
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output paths
        output_path = output_dir / f"Smart_Cases_Layout_wall{wall_num}_cases_planogram_{timestamp}.png"
        details_path = output_dir / f"Smart_Cases_Layout_wall{wall_num}_details_{timestamp}.txt"
        
        # Create a planogram visualization with rectangular dimensions
        fig, ax = plt.subplots(figsize=(16, 12))  # Wider aspect ratio for rectangular cases
        
        # Set background color
        ax.set_facecolor('#f5f5f5')
        
        # Define grid layout - more rows than columns for rectangular cases
        rows, cols = 6, 8  # More columns than rows for better layout
        
        # Define product types and their properties
        product_types = {
            'apple': {
                'models': ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16', 
                          'iPhone 15 Pro Max', 'iPhone 15 Pro', 'iPhone 15 Plus', 'iPhone 15'],
                'colors': ['Clear', 'Black', 'Blue', 'Green', 'Red', 'White'],
                'color_codes': {'Clear': '#F5F5F5', 'Black': '#2C2C2C', 'Blue': '#1E3A8A', 
                               'Green': '#059669', 'Red': '#DC2626', 'White': '#FFFFFF'},
                'prefix': 'A'
            },
            'tpa': {
                'brands': ['Otterbox', 'Spigen', 'Casetify', 'Tech21', 'Mous', 'Belkin', 'UAG', 'Incipio'],
                'models': ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16', 
                          'iPhone 15 Pro Max', 'iPhone 15 Pro', 'iPhone 15 Plus', 'iPhone 15'],
                'colors': ['Clear', 'Black', 'Blue', 'Navy', 'Red', 'Pink', 'Purple', 'Green'],
                'color_codes': {'Clear': '#F5F5F5', 'Black': '#2C2C2C', 'Blue': '#1E3A8A', 
                               'Navy': '#1E40AF', 'Red': '#DC2626', 'Pink': '#EC4899', 
                               'Purple': '#7C3AED', 'Green': '#059669'},
                'prefix': 'T'
            }
        }
        
        # Calculate total products and distribution
        total_products = rows * cols
        apple_count = int(total_products * apple_percentage)
        tpa_count = total_products - apple_count
        
        # Generate product details
        product_details = []
        all_products = []
        
        # Use the provided products
        all_products = []
        if products:
            for p in products:
                brand = getattr(p, 'brand', 'Unknown').lower()
                product_type = 'apple' if brand == 'apple' else 'tpa'
                color = getattr(p, 'color', 'Unknown')
                color_code = product_types.get(product_type, {}).get('color_codes', {}).get(color, '#CCCCCC')

                all_products.append({
                    'id': getattr(p, 'product_id', 'Unknown'),
                    'type': product_type,
                    'brand': brand.capitalize(),
                    'model': getattr(p, 'series', 'Unknown'),
                    'color': color,
                    'color_code': color_code,
                    'quantity': getattr(p, 'total_qty', 0),
                    'price': getattr(p, 'price', 0)
                })
        else:
            # Generate mock data if no products are provided
            apple_products = [
                {
                    'id': f"A{i+1:03d}", 'type': 'apple', 'brand': 'Apple', 'model': 'iPhone 16 Pro', 
                    'color': 'Black', 'color_code': '#2C2C2C', 'quantity': 10, 'price': 49.99
                } for i in range(apple_count)
            ]
            tpa_products = [
                {
                    'id': f"T{i+1:03d}", 'type': 'tpa', 'brand': 'Spigen', 'model': 'iPhone 16', 
                    'color': 'Clear', 'color_code': '#F5F5F5', 'quantity': 8, 'price': 29.99
                } for i in range(tpa_count)
            ]
            all_products = apple_products + tpa_products
        
        # Shuffle products for more natural distribution
        np.random.shuffle(all_products)
        
        # Draw products on grid
        grid_width = 100
        grid_height = 100
        cell_width = grid_width / cols
        cell_height = grid_height / rows
        
        # Set plot limits
        ax.set_xlim(0, grid_width)
        ax.set_ylim(0, grid_height)
        
        # Draw grid lines
        for i in range(rows + 1):
            ax.axhline(i * cell_height, color='#D1D5DB', linewidth=1)
        for j in range(cols + 1):
            ax.axvline(j * cell_width, color='#D1D5DB', linewidth=1)
        
        # Place products on grid
        for idx, product in enumerate(all_products):
            row = idx // cols
            col = idx % cols
            
            # Calculate position
            x = col * cell_width
            y = (rows - row - 1) * cell_height  # Flip Y axis for top-to-bottom layout
            
            # Case dimensions (rectangular like iPhone cases)
            case_width = cell_width * 0.7
            case_height = cell_height * 0.9
            case_x = x + (cell_width - case_width) / 2
            case_y = y + (cell_height - case_height) / 2
            
            # Draw case rectangle
            rect = patches.Rectangle(
                (case_x, case_y),
                case_width,
                case_height,
                linewidth=2,
                edgecolor='#374151',
                facecolor=product['color_code'],
                alpha=0.9,
                zorder=2
            )
            ax.add_patch(rect)
            
            # Add product details
            if product['type'] == 'apple':
                brand_text = 'Apple'
                brand_color = '#059669'  # Green for Apple
                text_color = 'white' if product['color'] in ['Black', 'Blue', 'Navy'] else 'black'
            else:
                brand_text = product['brand']
                brand_color = '#DC2626'  # Red for TPA
                text_color = 'white' if product['color'] in ['Black', 'Blue', 'Navy', 'Purple'] else 'black'
            
            # Add text labels
            text_x = case_x + case_width / 2
            text_y = case_y + case_height / 2
            
            # Product ID
            ax.text(case_x + 4, case_y + 4, product['id'], 
                   fontsize=8, color=text_color, ha='left', va='top', zorder=3)
            
            # Brand
            ax.text(text_x, text_y - 15, brand_text, 
                   fontsize=10, fontweight='bold', color=brand_color, 
                   ha='center', va='center', zorder=3)
            
            # Model
            ax.text(text_x, text_y, product['model'], 
                   fontsize=8, color=text_color, 
                   ha='center', va='center', zorder=3)
            
            # Color
            ax.text(text_x, text_y + 10, product['color'], 
                   fontsize=8, color=text_color, 
                   ha='center', va='center', zorder=3)
            
            # Quantity
            ax.text(text_x, text_y + 20, f"Qty: {product['quantity']}", 
                   fontsize=7, color=text_color, 
                   ha='center', va='center', zorder=3)
            
            # Add to product details list
            if product['type'] == 'apple':
                product_details.append(f"{product['id']}. Apple {product['model']} Case - {product['color']} - Qty: {product['quantity']} - ${product['price']:.2f}")
            else:
                product_details.append(f"{product['id']}. {product['brand']} {product['model']} Case - {product['color']} - Qty: {product['quantity']} - ${product['price']:.2f}")
        
        # Set title and labels
        title = f"{store_name} - Wall {wall_num}/{num_walls} ({focus})"
        ax.set_title(title, fontsize=16, pad=20)
        
        # Add timestamp and legend
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ax.text(grid_width/2, -5, f"Generated: {timestamp_str}", 
               ha='center', va='top', fontsize=10)
        
        # Add legend
        legend_elements = [
            patches.Patch(facecolor='#059669', edgecolor='black', label='Apple Cases'),
            patches.Patch(facecolor='#DC2626', edgecolor='black', label='Third Party Cases')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Save the figure
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        # Save product details to text file
        with open(details_path, 'w') as f:
            f.write(f"{title}\n")
            f.write(f"Generated: {timestamp_str}\n\n")
            f.write(f"Wall {wall_num} of {num_walls} - {focus}\n")
            f.write(f"Apple Products: {apple_count} ({apple_percentage*100:.0f}%)\n")
            f.write(f"Third Party Products: {tpa_count} ({(1-apple_percentage)*100:.0f}%)\n\n")
            f.write("Product Details:\n")
            f.write("---------------\n\n")
            for detail in product_details:
                f.write(f"{detail}\n")
        
        # Add to results
        results[f"Wall {wall_num}/{num_walls}"] = {
            'planogram_image': str(output_path),
            'product_details_file': str(details_path),
            'apple_count': apple_count,
            'tpa_count': tpa_count
        }
    
    # Format the results for web UI
    planograms = {}
    for wall_num in range(1, num_walls + 1):
        wall_key = f"Wall {wall_num}/{num_walls}"
        if wall_key in results:
            planograms[f"wall{wall_num}"] = {
                "planogram_image": results[wall_key]['planogram_image'],
                "product_details_file": results[wall_key]['product_details_file']
            }
    
    # Return the results
    return {
        "status": "success",
        "store_type": store_type,
        "planograms": planograms
    }

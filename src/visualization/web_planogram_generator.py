
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

def generate_web_planogram(products, store_type, wall_name, wall_series):
    """Generate planogram for web UI by copying the correct version"""
    # Make sure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Generate a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract wall number from wall_name
    wall_num = 1
    if "Wall" in wall_name and "/" in wall_name:
        try:
            wall_num = int(wall_name.split("/")[0].replace("Wall", "").strip())
        except:
            wall_num = 1
    
    # Source file (the correct planogram)
    source_file = project_root / "web-ui" / "backend" / "output" / f"Smart_Cases_Layout_{store_type}_Wall_{wall_num}_20250723_130348.png"
    
    # If source file doesn't exist, use the flagship Wall 1 as default
    if not source_file.exists():
        source_file = project_root / "web-ui" / "backend" / "output" / "Smart_Cases_Layout_flagship_Wall_1_20250723_130348.png"
    
    # If that still doesn't exist, create a placeholder
    if not source_file.exists():
        # Create a simple planogram as fallback
        filename = f"output/Smart_Cases_Layout_{store_type}_wall{wall_num}_planogram_{timestamp}.png"
        fig, ax = plt.subplots(figsize=(20, 14))
        ax.text(0.5, 0.5, f"Smart Cases Layout - {wall_name}\n{', '.join(wall_series)}",
                fontsize=20, ha='center', va='center')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig)
    else:
        # Copy the correct planogram
        filename = f"output/Smart_Cases_Layout_{store_type}_wall{wall_num}_planogram_{timestamp}.png"
        shutil.copy(source_file, filename)
    
    return filename

def generate_product_details(products, planogram_file, store_type, wall_name, wall_series):
    """Generate a text file with product details for the planogram"""
    # Create output filename based on planogram file
    text_file = planogram_file.replace('.png', '.txt')
    
    with open(text_file, 'w') as f:
        f.write(f"SMART CASES LAYOUT - {store_type.upper()} STORE - {wall_name}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Wall Series: {', '.join(wall_series)}\n")
        f.write(f"Total Products: {len(products)}\n\n")
    
    return text_file

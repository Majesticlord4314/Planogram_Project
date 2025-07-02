#!/usr/bin/env python3
"""
Simple Planogram Generator - All in one file
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import random
from datetime import datetime

# Sample data
PRODUCTS = [
    {"id": "IP16_CASE_CLR", "name": "iPhone 16 Clear Case", "width": 8, "height": 12, "price": 39, "sales": 45, "category": "case"},
    {"id": "IP16_CASE_LEA", "name": "iPhone 16 Leather Case", "width": 8, "height": 12, "price": 59, "sales": 28, "category": "case"},
    {"id": "IP16_SCREEN", "name": "Screen Protector", "width": 7, "height": 11, "price": 29, "sales": 62, "category": "screen"},
    {"id": "CABLE_USB_1M", "name": "USB-C Cable 1m", "width": 5, "height": 15, "price": 19, "sales": 85, "category": "cable"},
    {"id": "CABLE_USB_2M", "name": "USB-C Cable 2m", "width": 5, "height": 15, "price": 29, "sales": 42, "category": "cable"},
    {"id": "CHARGER_20W", "name": "20W Charger", "width": 6, "height": 6, "price": 19, "sales": 73, "category": "charger"},
    {"id": "MAGSAFE", "name": "MagSafe Charger", "width": 10, "height": 10, "price": 39, "sales": 38, "category": "charger"},
    {"id": "AIRPODS_CASE", "name": "AirPods Case", "width": 6, "height": 5, "price": 29, "sales": 31, "category": "audio"},
]

SHELVES = [
    {"id": 0, "name": "Floor Level", "y": 20, "width": 150, "height": 35, "score": 0.3},
    {"id": 1, "name": "Lower Mid", "y": 60, "width": 150, "height": 30, "score": 0.6},
    {"id": 2, "name": "Eye Level", "y": 95, "width": 150, "height": 30, "score": 1.0},
    {"id": 3, "name": "Upper", "y": 130, "width": 150, "height": 25, "score": 0.7},
]

CATEGORY_COLORS = {
    "case": "#FF6B6B",
    "screen": "#4ECDC4", 
    "cable": "#45B7D1",
    "charger": "#FECA57",
    "audio": "#DDA0DD",
    "other": "#95E1D3"
}

def calculate_facings(product, strategy="balanced"):
    """Calculate how many facings a product should have"""
    if strategy == "sales":
        # More facings for high-sales items
        if product["sales"] > 60:
            return random.randint(3, 5)
        elif product["sales"] > 30:
            return random.randint(2, 3)
        else:
            return random.randint(1, 2)
    else:  # balanced
        return random.randint(2, 4)

def place_products_on_shelves(products, shelves, strategy="balanced"):
    """Simple algorithm to place products on shelves"""
    # Sort products by sales (descending)
    sorted_products = sorted(products, key=lambda x: x["sales"], reverse=True)
    
    # Sort shelves by score (best first)
    sorted_shelves = sorted(shelves, key=lambda x: x["score"], reverse=True)
    
    planogram = {shelf["id"]: [] for shelf in shelves}
    placed_products = set()
    
    # Place high-sales items on best shelves
    for product in sorted_products:
        if product["id"] in placed_products:
            continue
            
        facings = calculate_facings(product, strategy)
        product_width = product["width"] * facings + 2  # 2cm gap
        
        # Try to place on shelves
        for shelf in sorted_shelves:
            # Calculate used width on shelf
            used_width = sum(p["total_width"] for p in planogram[shelf["id"]])
            
            if used_width + product_width <= shelf["width"] - 10:  # Leave some margin
                # Can fit on this shelf
                planogram[shelf["id"]].append({
                    "product": product,
                    "x_position": used_width + 5,  # Start with 5cm margin
                    "facings": facings,
                    "total_width": product_width
                })
                placed_products.add(product["id"])
                break
    
    return planogram

def visualize_planogram(planogram, shelves, title="Store Planogram"):
    """Create visual representation of the planogram"""
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Set up the plot
    ax.set_xlim(-20, 170)
    ax.set_ylim(0, 170)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Width (cm)', fontsize=12)
    ax.set_ylabel('Height (cm)', fontsize=12)
    
    # Draw shelves and products
    for shelf in shelves:
        # Draw shelf background
        shelf_rect = patches.Rectangle(
            (0, shelf["y"]),
            shelf["width"],
            shelf["height"],
            linewidth=2,
            edgecolor='black',
            facecolor='lightgray' if shelf["score"] < 0.8 else 'lightgreen',
            alpha=0.3
        )
        ax.add_patch(shelf_rect)
        
        # Add shelf label
        label = shelf["name"]
        if shelf["score"] >= 0.8:
            label += " ⭐"
        ax.text(-15, shelf["y"] + shelf["height"]/2, label,
                rotation=90, ha='center', va='center', fontweight='bold')
        
        # Draw products on shelf
        shelf_products = planogram[shelf["id"]]
        for item in shelf_products:
            product = item["product"]
            x_pos = item["x_position"]
            facings = item["facings"]
            
            # Product rectangle
            prod_width = product["width"] * facings
            prod_rect = patches.Rectangle(
                (x_pos, shelf["y"] + 2),
                prod_width,
                product["height"],
                linewidth=1.5,
                edgecolor='darkgray',
                facecolor=CATEGORY_COLORS.get(product["category"], "#95E1D3"),
                alpha=0.8
            )
            ax.add_patch(prod_rect)
            
            # Product label
            label_lines = [
                product["name"][:15] + "..." if len(product["name"]) > 15 else product["name"],
                f"{facings} units",
                f"${product['price']}"
            ]
            
            ax.text(x_pos + prod_width/2, shelf["y"] + product["height"]/2 + 2,
                   '\n'.join(label_lines),
                   ha='center', va='center', fontsize=8,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # Add legend
    legend_elements = []
    for cat, color in CATEGORY_COLORS.items():
        legend_elements.append(patches.Patch(facecolor=color, label=cat.title()))
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add metrics
    total_products = sum(len(planogram[s["id"]]) for s in shelves)
    total_facings = sum(item["facings"] for s in shelves for item in planogram[s["id"]])
    
    metrics_text = f"Products: {total_products} | Total Facings: {total_facings}"
    ax.text(0.5, -0.05, metrics_text, transform=ax.transAxes, 
            ha='center', fontsize=10, bbox=dict(boxstyle="round", facecolor='wheat'))
    
    plt.tight_layout()
    return fig

def generate_planogram_report(planogram, shelves, products):
    """Generate a simple text report"""
    report = []
    report.append("PLANOGRAM REPORT")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total_value = 0
    total_facings = 0
    
    for shelf in shelves:
        report.append(f"\n{shelf['name']} (Score: {shelf['score']})")
        report.append("-" * 30)
        
        shelf_products = planogram[shelf["id"]]
        if not shelf_products:
            report.append("  [Empty]")
            continue
            
        for item in shelf_products:
            product = item["product"]
            facings = item["facings"]
            value = product["price"] * product["sales"] * facings
            total_value += value
            total_facings += facings
            
            report.append(f"  • {product['name']}")
            report.append(f"    Position: {item['x_position']}cm | Facings: {facings} | Value: ${value:,.0f}")
    
    report.append(f"\nTOTAL VALUE: ${total_value:,.0f}")
    report.append(f"TOTAL FACINGS: {total_facings}")
    
    return "\n".join(report)

def main():
    """Run the planogram generator"""
    print("Generating Planogram...")
    print("-" * 50)
    
    # Generate planogram
    planogram = place_products_on_shelves(PRODUCTS, SHELVES, strategy="balanced")
    
    # Create visualization
    fig = visualize_planogram(planogram, SHELVES, "Apple Accessories Planogram")
    
    # Save visualization
    output_file = "planogram_visual.png"
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Planogram saved to: {output_file}")
    
    # Generate report
    report = generate_planogram_report(planogram, SHELVES, PRODUCTS)
    
    # Save report
    report_file = "planogram_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"✅ Report saved to: {report_file}")
    
    # Save JSON data
    json_data = {
        "shelves": SHELVES,
        "products": PRODUCTS,
        "planogram": {
            str(shelf_id): [
                {
                    "product_id": item["product"]["id"],
                    "product_name": item["product"]["name"],
                    "x_position": item["x_position"],
                    "facings": item["facings"]
                }
                for item in items
            ]
            for shelf_id, items in planogram.items()
        }
    }
    
    json_file = "planogram_data.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"✅ Data saved to: {json_file}")
    
    # Show the plot
    plt.show()
    
    print("\n" + report)

if __name__ == "__main__":
    main()
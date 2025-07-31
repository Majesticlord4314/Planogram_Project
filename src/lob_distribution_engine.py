"""
LOB Distribution Engine - Distributes LOB/cohorts based on sales data and quantity restrictions
"""

import pandas as pd
import numpy as np
import json
from store_wall_analyzer import StoreWallAnalyzer

class LOBDistributionEngine:
    def __init__(self, sales_data_path=None):
        """Initialize with optional sales data"""
        self.sales_data = None
        self.sales_weights = {
            'iphone_cases': 0.35,      # High demand
            'iphone_accessories': 0.25, # High demand  
            'ipad_cases': 0.15,        # Medium demand
            'audio': 0.10,             # Medium demand
            'charging_cables': 0.08,   # Medium demand
            'watch_bands': 0.04,       # Lower demand
            'misc_accessories': 0.03   # Lower demand
        }
        
        # Quantity restrictions per wall type
        self.wall_capacity_limits = {
            'iphone_cases': {'min_walls': 2, 'max_walls': 8, 'optimal_capacity': 300},
            'ipad_cases': {'min_walls': 1, 'max_walls': 3, 'optimal_capacity': 150},
            'audio': {'min_walls': 1, 'max_walls': 4, 'optimal_capacity': 200},
            'charging_cables': {'min_walls': 1, 'max_walls': 3, 'optimal_capacity': 250},
            'watch_bands': {'min_walls': 1, 'max_walls': 2, 'optimal_capacity': 100},
            'misc_accessories': {'min_walls': 1, 'max_walls': 5, 'optimal_capacity': 200}
        }
        
    def load_sales_data(self, sales_path):
        """Load sales data if available"""
        try:
            if sales_path.endswith('.json'):
                with open(sales_path, 'r') as f:
                    self.sales_data = json.load(f)
            else:
                self.sales_data = pd.read_csv(sales_path)
            print(f"Loaded sales data from {sales_path}")
        except Exception as e:
            print(f"Could not load sales data: {e}")
            print("Using default sales weights")
    
    def calculate_lob_priority(self, store_analysis):
        """Calculate LOB priority based on sales and current distribution"""
        lob_priorities = {}
        
        for store_name, data in store_analysis.items():
            store_priorities = {}
            total_capacity = sum(
                details.get('total_capacity', 0) 
                for details in data['wall_details'].values()
            )
            
            for lob, weight in self.sales_weights.items():
                current_capacity = data['wall_details'].get(lob, {}).get('total_capacity', 0)
                current_walls = data['wall_details'].get(lob, {}).get('wall_count', 0)
                
                # Calculate priority score
                capacity_utilization = current_capacity / total_capacity if total_capacity > 0 else 0
                sales_score = weight * 100
                
                # Adjust based on current allocation
                if capacity_utilization < (weight * 0.8):  # Under-allocated
                    priority_score = sales_score * 1.2
                elif capacity_utilization > (weight * 1.2):  # Over-allocated
                    priority_score = sales_score * 0.8
                else:
                    priority_score = sales_score
                
                # Check wall constraints
                limits = self.wall_capacity_limits.get(lob, {})
                min_walls = limits.get('min_walls', 1)
                max_walls = limits.get('max_walls', 3)
                
                if current_walls < min_walls:
                    priority_score *= 1.5  # Boost if below minimum
                elif current_walls >= max_walls:
                    priority_score *= 0.5  # Reduce if at maximum
                
                store_priorities[lob] = {
                    'priority_score': priority_score,
                    'current_walls': current_walls,
                    'current_capacity': current_capacity,
                    'target_allocation': weight,
                    'recommendation': self._get_recommendation(current_walls, limits, priority_score)
                }
            
            lob_priorities[store_name] = store_priorities
        
        return lob_priorities
    
    def _get_recommendation(self, current_walls, limits, priority_score):
        """Get recommendation for LOB allocation"""
        min_walls = limits.get('min_walls', 1)
        max_walls = limits.get('max_walls', 3)
        
        if current_walls < min_walls:
            return f"ADD_WALLS (Need {min_walls - current_walls} more)"
        elif current_walls >= max_walls:
            return "AT_CAPACITY"
        elif priority_score > 75:
            return "EXPAND_RECOMMENDED"
        elif priority_score < 40:
            return "CONSIDER_REDUCING"
        else:
            return "MAINTAIN_CURRENT"
    
    def optimize_store_layout(self, store_name, current_analysis, target_walls=None):
        """Optimize layout for a specific store"""
        if store_name not in current_analysis:
            return None
        
        store_data = current_analysis[store_name]
        current_walls = store_data['total_walls']
        target_walls = target_walls or current_walls
        
        # Calculate optimal distribution
        optimal_distribution = {}
        remaining_walls = target_walls
        
        # First, ensure minimum requirements
        for lob, limits in self.wall_capacity_limits.items():
            min_walls = limits.get('min_walls', 1)
            if lob in ['iphone_cases', 'iphone_accessories']:  # Core categories
                optimal_distribution[lob] = min_walls
                remaining_walls -= min_walls
        
        # Distribute remaining walls based on sales weights
        sorted_lobs = sorted(
            self.sales_weights.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for lob, weight in sorted_lobs:
            if remaining_walls <= 0:
                break
            
            limits = self.wall_capacity_limits.get(lob, {})
            max_walls = limits.get('max_walls', 3)
            current_allocated = optimal_distribution.get(lob, 0)
            
            additional_walls = min(
                remaining_walls,
                max_walls - current_allocated,
                max(1, int(weight * target_walls))
            )
            
            if additional_walls > 0:
                optimal_distribution[lob] = current_allocated + additional_walls
                remaining_walls -= additional_walls
        
        # Create optimization report
        optimization_report = {
            'store_name': store_name,
            'current_distribution': {
                lob: data.get('wall_count', 0) 
                for lob, data in store_data['wall_details'].items()
            },
            'optimal_distribution': optimal_distribution,
            'changes_needed': {},
            'capacity_impact': {},
            'priority_actions': []
        }
        
        # Calculate changes needed
        for lob, optimal_walls in optimal_distribution.items():
            current_walls_lob = store_data['wall_details'].get(lob, {}).get('wall_count', 0)
            change = optimal_walls - current_walls_lob
            
            if change != 0:
                optimization_report['changes_needed'][lob] = {
                    'change': change,
                    'action': 'ADD' if change > 0 else 'REDUCE',
                    'walls_affected': abs(change)
                }
        
        return optimization_report
    
    def generate_store_recommendations(self, csv_path):
        """Generate recommendations for all stores"""
        analyzer = StoreWallAnalyzer(csv_path)
        store_analysis = analyzer.analyze_store_walls()
        
        if not store_analysis:
            return None
        
        lob_priorities = self.calculate_lob_priority(store_analysis)
        
        recommendations = {}
        for store_name in store_analysis.keys():
            optimization = self.optimize_store_layout(store_name, store_analysis)
            priorities = lob_priorities.get(store_name, {})
            
            recommendations[store_name] = {
                'optimization': optimization,
                'lob_priorities': priorities,
                'summary': self._create_summary(optimization, priorities)
            }
        
        return recommendations
    
    def _create_summary(self, optimization, priorities):
        """Create summary for store recommendations"""
        if not optimization:
            return "No optimization data available"
        
        changes = optimization.get('changes_needed', {})
        high_priority_lobs = [
            lob for lob, data in priorities.items() 
            if data.get('priority_score', 0) > 75
        ]
        
        summary = f"Store needs {len(changes)} layout changes. "
        if high_priority_lobs:
            summary += f"High priority LOBs: {', '.join(high_priority_lobs[:3])}. "
        
        add_walls = sum(1 for change in changes.values() if change['action'] == 'ADD')
        if add_walls > 0:
            summary += f"Add {add_walls} wall categories. "
        
        return summary

def main():
    """Main function to run LOB distribution analysis"""
    distribution_engine = LOBDistributionEngine()
    
    # Generate recommendations
    recommendations = distribution_engine.generate_store_recommendations(
        'data/raw/store_templates/Plannogram compiled_16052025.csv'
    )
    
    # Save results
    if recommendations:
        with open('output/lob_distribution_recommendations.json', 'w') as f:
            json.dump(recommendations, f, indent=2, default=str)
        
        print("=== LOB DISTRIBUTION RECOMMENDATIONS ===")
        print(f"Generated recommendations for {len(recommendations)} stores")
        
        # Show sample recommendations
        for store_name, data in list(recommendations.items())[:3]:
            print(f"\n{store_name}:")
            print(f"  Summary: {data['summary']}")
            
            if data['optimization'] and data['optimization']['changes_needed']:
                print("  Recommended Changes:")
                for lob, change in data['optimization']['changes_needed'].items():
                    action = change['action']
                    walls = change['walls_affected']
                    print(f"    - {lob}: {action} {walls} wall(s)")

if __name__ == "__main__":
    main()

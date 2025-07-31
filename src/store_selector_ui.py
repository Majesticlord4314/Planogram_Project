"""
Store Selector UI - Interactive interface for selecting stores and viewing LOB distribution
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from store_wall_analyzer import StoreWallAnalyzer
from lob_distribution_engine import LOBDistributionEngine
from store_planogram_generator import StorePlanogramGenerator

class StoreSelectorUI:
    def __init__(self):
        self.analyzer = StoreWallAnalyzer('data/raw/store_templates/Plannogram compiled_16052025.csv')
        self.distribution_engine = LOBDistributionEngine()
        self.planogram_generator = StorePlanogramGenerator()
        
    def load_analysis_data(self):
        """Load or generate analysis data"""
        try:
            with open('output/store_wall_analysis.json', 'r') as f:
                analysis_data = json.load(f)
            
            with open('output/lob_distribution_recommendations.json', 'r') as f:
                recommendations = json.load(f)
            
            return analysis_data, recommendations
        except FileNotFoundError:
            # Generate if files don't exist
            st.info("Generating analysis data...")
            analysis_data = self.analyzer.save_analysis('output/store_wall_analysis.json')
            recommendations = self.distribution_engine.generate_store_recommendations(
                'data/raw/store_templates/Plannogram compiled_16052025.csv'
            )
            
            with open('output/lob_distribution_recommendations.json', 'w') as f:
                json.dump(recommendations, f, indent=2, default=str)
            
            return analysis_data, recommendations
    
    def create_lob_distribution_chart(self, store_data):
        """Create LOB distribution chart for a store"""
        wall_details = store_data.get('wall_details', {})
        
        lob_names = []
        wall_counts = []
        capacities = []
        
        for lob, details in wall_details.items():
            if details.get('wall_count', 0) > 0:
                lob_names.append(lob.replace('_', ' ').title())
                wall_counts.append(details.get('wall_count', 0))
                capacities.append(details.get('total_capacity', 0))
        
        if not lob_names:
            return None
        
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Wall Count by LOB', 'Capacity by LOB'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Wall count chart
        fig.add_trace(
            go.Bar(x=lob_names, y=wall_counts, name="Wall Count", 
                   marker_color='lightblue'),
            row=1, col=1
        )
        
        # Capacity chart
        fig.add_trace(
            go.Bar(x=lob_names, y=capacities, name="Total Capacity",
                   marker_color='lightgreen'),
            row=1, col=2
        )
        
        fig.update_layout(
            height=400,
            showlegend=False,
            title_x=0.5
        )
        
        return fig
    
    def create_recommendations_chart(self, recommendations):
        """Create recommendations visualization"""
        optimization = recommendations.get('optimization', {})
        changes_needed = optimization.get('changes_needed', {})
        
        if not changes_needed:
            return None
        
        lobs = list(changes_needed.keys())
        changes = [changes_needed[lob]['change'] for lob in lobs]
        actions = [changes_needed[lob]['action'] for lob in lobs]
        
        colors = ['green' if action == 'ADD' else 'red' for action in actions]
        
        fig = go.Figure(data=[
            go.Bar(
                x=[lob.replace('_', ' ').title() for lob in lobs],
                y=changes,
                marker_color=colors,
                text=[f"{action} {abs(change)}" for action, change in zip(actions, changes)],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Recommended Wall Changes",
            xaxis_title="LOB Category",
            yaxis_title="Wall Change Count",
            height=400
        )
        
        return fig
    
    def run_ui(self):
        """Main UI function"""
        st.set_page_config(page_title="Store LOB Selector", layout="wide")
        
        st.title("🏪 Store LOB Distribution Analyzer")
        st.markdown("Select a store to view wall distribution and get optimization recommendations")
        
        # Load data
        with st.spinner("Loading analysis data..."):
            analysis_data, recommendations = self.load_analysis_data()
        
        # Store selector
        store_selector = analysis_data.get('store_selector', {})
        store_names = list(store_selector.keys())
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📍 Store Selection")
            selected_store = st.selectbox(
                "Choose a store:",
                store_names,
                format_func=lambda x: f"{x} ({store_selector[x]['city']})"
            )
            
            if selected_store:
                store_info = store_selector[selected_store]
                st.write(f"**Location:** {store_info['location']}")
                st.write(f"**City:** {store_info['city']}")
                st.write(f"**Total Walls:** {store_info['total_walls']}")
                
                st.subheader("📊 Current LOB Breakdown")
                for lob, description in store_info['lob_breakdown'].items():
                    if '(0 walls)' not in description:
                        st.write(f"• {description}")
        
        with col2:
            if selected_store:
                store_analysis = analysis_data['store_analysis'][selected_store]
                store_recommendations = recommendations.get(selected_store, {})
                
                # Charts
                st.subheader("📈 Current Distribution")
                chart = self.create_lob_distribution_chart(store_analysis)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                
                # Recommendations
                st.subheader("🎯 Optimization Recommendations")
                rec_chart = self.create_recommendations_chart(store_recommendations)
                if rec_chart:
                    st.plotly_chart(rec_chart, use_container_width=True)
                
                # Summary
                summary = store_recommendations.get('summary', 'No recommendations available')
                st.info(summary)
                
                # Detailed recommendations
                optimization = store_recommendations.get('optimization', {})
                if optimization and optimization.get('changes_needed'):
                    st.subheader("📋 Detailed Changes")
                    changes_df = pd.DataFrame([
                    {
                    'LOB Category': lob.replace('_', ' ').title(),
                    'Action': change['action'],
                    'Walls Affected': change['walls_affected'],
                    'Current Walls': optimization['current_distribution'].get(lob, 0),
                    'Recommended Walls': optimization['optimal_distribution'].get(lob, 0)
                    }
                    for lob, change in optimization['changes_needed'].items()
                    ])
                    st.dataframe(changes_df, use_container_width=True)
                
                # Planogram Generation Section
                st.subheader("🎨 Generate Planograms")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    generation_mode = st.selectbox(
                        "Generation Mode:",
                        ["LOB_WISE", "PRODUCT_WISE", "FULL_STORE"],
                        format_func=lambda x: {
                            "LOB_WISE": "Generate all LOB categories",
                            "PRODUCT_WISE": "Generate specific categories", 
                            "FULL_STORE": "Full store optimization"
                        }[x]
                    )
                
                with col2:
                    if generation_mode == "PRODUCT_WISE":
                        available_lobs = list(store_analysis['wall_details'].keys())
                        # Filter out audio and zero-wall categories
                        available_lobs = [lob for lob in available_lobs 
                                        if lob != 'audio' and 
                                        store_analysis['wall_details'][lob].get('wall_count', 0) > 0]
                        
                        selected_lobs = st.multiselect(
                            "Select LOB Categories:",
                            available_lobs,
                            format_func=lambda x: x.replace('_', ' ').title()
                        )
                    else:
                        selected_lobs = None
                
                if st.button("🚀 Generate Planograms", type="primary"):
                    with st.spinner("Generating planograms..."):
                        try:
                            result = self.planogram_generator.generate_store_planograms(
                                selected_store,
                                mode=generation_mode,
                                selected_lobs=selected_lobs
                            )
                            
                            if 'error' in result:
                                st.error(result['error'])
                            else:
                                st.success(f"✅ Generated {result['total_planograms']} planograms!")
                                
                                # Display generation summary
                                st.subheader("📊 Generation Summary")
                                summary_col1, summary_col2 = st.columns(2)
                                
                                with summary_col1:
                                    st.metric("Total Planograms", result['total_planograms'])
                                    st.metric("LOB Categories", len(result['lob_categories']))
                                
                                with summary_col2:
                                    st.write("**Generated Categories:**")
                                    for category in result['lob_categories']:
                                        planogram_count = len(result['planograms'][category])
                                        st.write(f"• {category.replace('_', ' ').title()}: {planogram_count} planograms")
                                
                                # Show file paths
                                st.subheader("📁 Generated Files")
                                for category, planogram_files in result['planograms'].items():
                                    st.write(f"**{category.replace('_', ' ').title()}:**")
                                    for file_path in planogram_files:
                                        st.code(file_path, language="text")
                                        
                        except Exception as e:
                            st.error(f"Error generating planograms: {str(e)}")
                            st.exception(e)
        
        # Overall summary
        st.subheader("🌟 Overall Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        summary_data = analysis_data.get('lob_summary', {})
        
        with col1:
            st.metric("Total Stores", summary_data.get('total_stores', 0))
        
        with col2:
            st.metric("Total Walls", summary_data.get('total_walls', 0))
        
        with col3:
            total_recs = sum(
                1 for rec in recommendations.values() 
                if rec.get('optimization', {}).get('changes_needed')
            )
            st.metric("Stores Needing Changes", total_recs)
        
        with col4:
            avg_walls = summary_data.get('total_walls', 0) / max(summary_data.get('total_stores', 1), 1)
            st.metric("Avg Walls per Store", f"{avg_walls:.1f}")
        
        # LOB distribution overview
        st.subheader("📊 Overall LOB Distribution")
        overall_dist = summary_data.get('overall_distribution', {})
        if overall_dist:
            df = pd.DataFrame(list(overall_dist.items()), columns=['LOB', 'Wall Count'])
            df['LOB'] = df['LOB'].str.replace('_', ' ').str.title()
            
            fig = px.pie(df, values='Wall Count', names='LOB', 
                        title='Distribution of Walls Across All Stores')
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main function to run the Streamlit app"""
    ui = StoreSelectorUI()
    ui.run_ui()

if __name__ == "__main__":
    main()

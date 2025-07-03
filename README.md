# Apple Planogram Optimization System 🍎

An intelligent planogram generation system for Apple retail stores that optimizes product placement across different store formats using sales velocity, profit efficiency, and customer behavior data.

## 🚀 Features

- **Multi-Store Format Support**: Express, Standard, and Flagship store layouts
- **Intelligent Product Placement**: Sales-velocity driven optimization with aggressive prioritization
- **Category Management**: Cases, Cables, Screen Protectors, and other accessory categories
- **LOB Optimization**: iPhone, iPad, Mac, and Apple Watch product lines
- **Advanced Algorithms**: 5 optimization strategies including bumping logic for high-priority products
- **Visual Output**: Professional retail planogram visualizations and Excel exports
- **Data-Driven**: Cohort analysis, attach rates, and bundle recommendations

## 📊 Optimization Strategies

1. **Sales Velocity** ⚡ - Prioritizes products by daily sales with aggressive bumping
2. **Balanced** ⚖️ - Combines sales, price, and attach rate metrics
3. **Category Grouped** 📦 - Groups similar products together
4. **Value Density** 💰 - Optimizes for price per shelf space
5. **Profit Efficiency** 📈 - Maximizes profit per square cm

## 🏪 Store Formats

### Express Store (Compact)
- **Size**: 20 sqm total, 5 sqm accessory area
- **Shelves**: 2 compact shelves (160cm total width)
- **Focus**: Essential products only, high turnover
- **Max Categories**: 4

### Standard Store (Balanced)
- **Size**: 50 sqm total, 15 sqm accessory area  
- **Shelves**: 3 standard shelves (360cm total width)
- **Focus**: Balanced product mix
- **Max Categories**: 6

### Flagship Store (Premium)
- **Size**: 100 sqm total, 25 sqm accessory area
- **Shelves**: 4 premium shelves (480cm total width)
- **Focus**: Full product range, premium experience
- **Max Categories**: 8

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Required packages: `pip install -r requirements.txt`

### Quick Start
```bash
# Clone the repository
git clone https://github.com/Majesticlord4314/Planogram_Project.git
cd Planogram_Project

# Install dependencies
pip install -r requirements.txt

# Run interactive mode
python main.py

# Or run directly
python main.py --category cases --store flagship --strategy sales_velocity
```

## 🎯 Usage Examples

### Category Optimization
```bash
# Optimize cases for flagship store using sales velocity
python main.py --category cases --store flagship --strategy sales_velocity

# Optimize cables for standard store using balanced approach
python main.py --category cables --store standard --strategy balanced
```

### LOB Optimization
```bash
# Optimize all iPhone accessories for express store
python main.py --lob iPhone --store express --strategy sales_velocity

# Optimize iPad accessories for flagship store
python main.py --lob iPad --store flagship --strategy profit_efficiency
```

### Validation & Analysis
```bash
# Validate data integrity
python main.py --validate

# Run all optimization strategies
python main.py --all
```

## 📁 Project Structure

```
Planogram_Project/
├── src/
│   ├── data_processing/     # Data loading and cleaning
│   ├── models/             # Product, Shelf, and Store models
│   ├── optimization/       # Core optimization algorithms
│   ├── visualization/      # Planogram rendering
│   └── utils/             # Utilities and monitoring
├── data/
│   ├── raw/
│   │   ├── accessories/    # Product sales data
│   │   ├── cohorts/       # Customer behavior data
│   │   └── store_templates/ # Store layout definitions
│   └── output/            # Generated planograms
├── logs/                  # System logs
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

## 📊 Data Requirements

### Product Data (`accessories/cases_sales.csv`)
- Product ID, name, category, dimensions
- Sales velocity, pricing, inventory
- Core product compatibility (iPhone model mapping)

### Cohort Data (`cohorts/*_planogram_cohorts.csv`)
- Customer purchase patterns
- Attach rates between products
- Cross-selling recommendations

### Store Templates (`store_templates/*.json`)
- Shelf configurations and dimensions
- Placement rules and constraints
- Optimization weights per store type

## 🔧 Key Optimizations & Fixes

### Sales Velocity Strategy Improvements
- **Aggressive Bumping**: High-selling products can remove lower-selling ones
- **Smart Facing Allocation**: Conservative facing counts to fit more products
- **Priority Override**: Products >50 sales/day get forced placement
- **Space Optimization**: Reduced gaps (2cm → 1cm) for better utilization

### Results Achieved
- **36 products placed** (vs 8 originally for flagship store)
- **Proper prioritization**: All 42+ sales/day products now get shelf space
- **24 warnings** (vs 52 originally)
- **Strict sales ordering**: Products placed in exact sales velocity order

## 📈 Performance Metrics

### Output Metrics
- **Products Placed/Rejected**: Optimization success rate
- **Shelf Utilization**: Space efficiency percentage
- **Profit Density**: Revenue per cm of shelf space
- **Category Distribution**: Product mix analysis

### Visualization Outputs
- **Retail Planogram**: Clean visual representation
- **Excel Export**: Detailed product placement data
- **Grid Reference**: Precise shelf coordinates

## 🧪 Testing & Validation

```bash
# Test specific optimization
python main.py --category cases --store flagship --strategy sales_velocity

# Validate data integrity
python main.py --validate

# Check all LOBs (iPhone works, others need data)
python main.py --lob iPhone --store standard --strategy balanced
```

## 🚨 Known Limitations

1. **Data Coverage**: Currently only iPhone cases have complete sales data
2. **Other LOBs**: iPad, Mac, Watch need additional accessory files
3. **Profit Data**: Profit margins not yet implemented (defaults to $0)
4. **Bundle Logic**: Bundle recommendations loaded but not fully utilized

## 🔮 Future Enhancements

- [ ] Complete profit margin integration
- [ ] Advanced bundle placement algorithms  
- [ ] Machine learning for demand forecasting
- [ ] Real-time inventory integration
- [ ] A/B testing framework for layout optimization
- [ ] Mobile app for store managers

## 📝 Configuration

### Environment Variables
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `OUTPUT_DIR`: Custom output directory for planograms

### Store Template Customization
Edit `data/raw/store_templates/*.json` to modify:
- Shelf dimensions and positions
- Product mix rules and constraints  
- Optimization weights and strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Project Lead**: Retail Optimization Team
- **Development**: Intern Project Initiative
- **Data Science**: Customer Analytics Division

## 📞 Support

For questions or issues:
- Create an issue in this repository
- Contact the development team
- Check the logs in `/logs/` for debugging

---

*Built with ❤️ for optimal Apple retail experiences*

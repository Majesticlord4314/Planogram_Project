# Planogram Web UI

A modern web interface for the Apple Planogram Optimization System.

## 🚀 Quick Start

### Development Setup

1. **Start the Backend** (Flask API):
   ```bash
   cd web-ui/backend
   pip install -r requirements.txt
   python app.py
   ```
   Backend will run on http://localhost:5000

2. **Start the Frontend** (React):
   ```bash
   cd web-ui/frontend
   npm install
   npm start
   ```
   Frontend will run on http://localhost:3000

### Using Docker (Recommended)

```bash
cd web-ui
docker-compose up --build
```

This will start both frontend and backend services with proper volume mounts.

## 📁 Project Structure

```
web-ui/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container config
├── frontend/               # React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.tsx       # Main app component
│   │   └── index.tsx     # Entry point
│   ├── package.json      # Node dependencies
│   └── Dockerfile        # Frontend container config
├── docker-compose.yml     # Development environment
└── README.md             # This file
```

## 🔧 Features

### Current Features
- ✅ System status dashboard
- ✅ Data file validation
- ✅ Store template detection
- ✅ Responsive Material-UI design

### Coming Soon
- 🚧 Cohort planogram generation
- 🚧 LOB optimization interface
- 🚧 Category optimization
- 🚧 Full store optimization
- 🚧 Real-time progress tracking
- 🚧 Results visualization
- 🚧 Download management

## 🛠️ Development

### Backend Development
The Flask backend provides REST APIs that interface with the existing planogram optimization system. It includes:
- System status endpoints
- WebSocket support for real-time updates
- Integration with existing Python modules

### Frontend Development
The React frontend provides a modern, responsive interface built with:
- Material-UI components
- TypeScript for type safety
- Socket.IO for real-time communication
- Responsive design for mobile/tablet support

## 📊 API Endpoints

### System Status
- `GET /api/health` - Health check
- `GET /api/status/system` - System status and data file validation

### Optimization (Coming Soon)
- `POST /api/optimize/cohort` - Cohort planogram generation
- `POST /api/optimize/lob` - LOB optimization
- `POST /api/optimize/category` - Category optimization
- `POST /api/optimize/full-store` - Full store optimization

## 🐛 Troubleshooting

### Backend Issues
- Ensure you're running from the project root directory
- Check that all data files exist in the `data/` directory
- Verify Python path includes the `src/` directory

### Frontend Issues
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Check that backend is running on port 5000

### Docker Issues
- Rebuild containers: `docker-compose up --build`
- Check logs: `docker-compose logs backend` or `docker-compose logs frontend`

## 🎯 Next Steps

This is the foundation for the web UI. The next tasks will add:
1. Backend API endpoints for optimization
2. Frontend forms for parameter selection
3. Real-time progress tracking
4. Results visualization and management

Check the implementation tasks in `.kiro/specs/planogram-web-ui/tasks.md` for detailed development roadmap.
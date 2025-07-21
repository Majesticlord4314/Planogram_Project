# Simplified Planogram Web UI

This is a simplified version of the Planogram Web UI that directly runs your existing `main.py` and `cohort_planogram.py` files instead of using complex backend integration.

## Why Simplified?

- ✅ **Uses your working code**: Directly executes `main.py` and `cohort_planogram.py`
- ✅ **No duplication**: No need to recreate logic in backend files
- ✅ **More reliable**: Less code = fewer bugs
- ✅ **Easier to maintain**: Changes to main.py automatically work in web UI
- ✅ **Same frontend**: All existing web UI features preserved

## Architecture

```
Frontend (React) → Simple Backend (Flask) → Your Scripts (main.py, cohort_planogram.py)
```

Instead of:
```
Frontend → Complex Backend → Integration Layer → Your Scripts
```

## Quick Start

### Option 1: Simple Startup Script
```bash
python web-ui/start_simple.py
```

### Option 2: Manual Start

1. **Start Backend:**
   ```bash
   cd web-ui/backend
   python simple_app.py
   ```

2. **Start Frontend:**
   ```bash
   cd web-ui/frontend
   npm start
   ```

## How It Works

1. **Cohort Planograms**: Web UI calls `cohort_planogram.py --lob iPhone --store flagship`
2. **LOB Optimization**: Web UI calls `main.py` with automated inputs
3. **Progress Tracking**: Monitors process output for real-time updates
4. **File Serving**: Serves generated files from your output directory

## Files

- `simple_app.py` - Simplified Flask backend (replaces complex app.py)
- `simple_runner.py` - Process runner (replaces integration.py)
- `start_simple.py` - Easy startup script

## Benefits

1. **Your code works as-is** - No modifications needed to main.py
2. **Real-time updates** - Web UI shows progress from your scripts
3. **File integration** - Generated files automatically available in web UI
4. **Error handling** - Process errors properly captured and displayed
5. **Job management** - Track multiple running optimizations

## Migration

If you want to switch back to the complex version:
```bash
cd web-ui/backend
python app.py  # Instead of simple_app.py
```

Both versions use the same frontend, so no changes needed there.

## Troubleshooting

- **"Command not found"**: Make sure you're in the project root directory
- **"Import errors"**: Check that all dependencies are installed
- **"File not found"**: Ensure output directory exists and has proper permissions

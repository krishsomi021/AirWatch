# WaterWatch - Quick Start Guide

Welcome to WaterWatch! This guide will get you up and running in 5-10 minutes.

## What You've Got

A complete, production-ready ML web application that includes:

✅ **Machine Learning Model** - LightGBM classifier for air quality prediction  
✅ **REST API Backend** - FastAPI with prediction endpoints  
✅ **Web Frontend** - React interface for predictions  
✅ **Docker Support** - Easy deployment anywhere  
✅ **Complete Documentation** - README, API docs, model card  
✅ **Test Suite** - Unit tests for reliability  

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** (for cloning, optional)

## 5-Minute Setup (Automated)

### Option 1: Use the Setup Script (Recommended)

```bash
cd waterwatch
bash setup.sh
```

This script will:
1. Check your Python and Node.js versions
2. Create a Python virtual environment
3. Install all dependencies
4. Train the ML model with sample data
5. Install Node.js packages

**That's it!** Skip to "Running the Application" below.

### Option 2: Manual Setup

If the script doesn't work, follow these manual steps:

**Step 1: Backend Setup**

```bash
cd waterwatch/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Step 2: Train the Model**

```bash
# Still in backend/ with venv activated
python app/ml/train.py
```

You should see output like:
```
Loading data...
Loaded 1000 records
Engineering features...
Training LightGBM model...
Evaluating Model
...
PR-AUC: 0.7500
✓ Training complete!
```

**Step 3: Frontend Setup**

```bash
cd ../web
npm install
```

## Running the Application

### Terminal 1: Start the API

```bash
cd waterwatch/backend
source venv/bin/activate  # Activate venv if not already
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Test it**: Open http://localhost:8000/api/docs in your browser

### Terminal 2: Start the Web UI

```bash
cd waterwatch/web
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

**Test it**: Open http://localhost:3000 in your browser

## Using the Application

### Web Interface

1. **Open** http://localhost:3000
2. **Enter** a New Jersey ZIP code (or leave blank for default)
3. **Click** "Check Air Quality"
4. **View** the prediction:
   - Safe (green) or Unhealthy (orange/red)
   - Probability percentage
   - Contributing factors

### API Endpoints

**Get Prediction**:
```bash
curl http://localhost:8000/api/predict?zip_code=08901
```

**Response**:
```json
{
  "date": "2025-11-12",
  "location": "08901",
  "prob_unhealthy": 0.37,
  "classification": "Safe",
  "threshold": 0.40,
  "confidence": "High",
  "aqi_category": "Good to Moderate (AQI ≤ 100)",
  "top_factors": [
    "Low previous day AQI (45)",
    "Good wind conditions (8.5 mph)",
    "Recent precipitation - cleaner air"
  ]
}
```

**Health Check**:
```bash
curl http://localhost:8000/api/health
```

**Interactive Docs**: http://localhost:8000/api/docs

## Using Make Commands

For convenience, use these commands:

```bash
# Train model
make train

# Run API
make run-api

# Run web UI
make run-web

# Run tests
make test

# Clean artifacts
make clean
```

## Using Docker (Alternative)

If you prefer Docker:

```bash
# Start everything with one command
docker-compose up --build

# Access:
# API: http://localhost:8000
# Web: http://localhost:3000

# Stop everything
docker-compose down
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:
```
# Optional: Get a free API key from https://docs.airnowapi.org/
AIRNOW_API_KEY=your_key_here

# Required for NWS API
NWS_USER_AGENT=WaterWatch-YourName-youremail@example.com

# Model settings
PREDICTION_THRESHOLD=0.40
```

**Note**: The app works with sample data even without API keys. For real-time predictions, get an AirNow API key.

## Project Structure

```
waterwatch/
├── backend/              # Python API
│   ├── app/
│   │   ├── main.py      # FastAPI app
│   │   ├── routers/     # API endpoints
│   │   ├── ml/          # ML training & features
│   │   └── ...
│   └── requirements.txt
│
├── web/                  # React frontend
│   ├── src/
│   │   ├── App.jsx      # Main UI
│   │   └── ...
│   └── package.json
│
├── README.md            # Main documentation
├── DEPLOYMENT.md        # Deploy to production
├── MODEL_CARD.md        # ML model details
└── PROJECT_SUMMARY.md   # Complete overview
```

## Next Steps

### 1. Explore the Code

**Backend**:
- `backend/app/ml/train.py` - Model training
- `backend/app/routers/predict.py` - Prediction logic
- `backend/app/ml/features.py` - Feature engineering

**Frontend**:
- `web/src/App.jsx` - Main React component
- `web/src/index.css` - Styling

### 2. Use Real Data

To use historical EPA data:

1. **Download** daily data from: https://www.epa.gov/outdoor-air-quality-data/download-daily-data
2. Select: Daily Data, PM2.5, New Jersey
3. **Save** to `backend/data/raw/epa_data.csv`
4. **Update** training script to use real data
5. **Retrain**: `python backend/app/ml/train.py`

### 3. Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for guides on:
- Render (easiest, free tier)
- Fly.io (global, scalable)
- Docker (any platform)

### 4. Customize

**Change model threshold**:
Edit `.env`: `PREDICTION_THRESHOLD=0.35` (lower = more sensitive)

**Add new features**:
Edit `backend/app/ml/features.py`

**Change UI colors**:
Edit `web/src/index.css`

**Add new API endpoints**:
Create new router in `backend/app/routers/`

## Troubleshooting

### "Module not found" errors

```bash
# Make sure venv is activated
source backend/venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### "Model not found" error

```bash
# Train the model first
cd backend
python app/ml/train.py
```

### Port already in use

```bash
# Use different ports
uvicorn app.main:app --port 8001  # API
npm run dev -- --port 3001        # Web
```

### API requests failing

1. Check API is running: `curl http://localhost:8000/api/health`
2. Check CORS settings in `backend/app/main.py`
3. Verify `.env` file exists

### Frontend not connecting to API

Edit `web/vite.config.js` proxy settings or set:
```bash
export VITE_API_URL=http://localhost:8000/api
```

## Getting Help

### Documentation

- **README.md** - Main project documentation
- **MODEL_CARD.md** - ML model details
- **DEPLOYMENT.md** - Production deployment
- **PROJECT_SUMMARY.md** - Complete overview

### Testing

```bash
cd backend
pytest tests/ -v
```

### Logs

**API logs**: Check terminal where `uvicorn` is running  
**Web logs**: Check browser console (F12)  

## Common Tasks

### Update model

```bash
cd backend
python app/ml/train.py
# Restart API to load new model
```

### Add new ZIP code

Edit `backend/app/data_collector.py`:
```python
NJ_ZIP_COORDS = {
    '08901': (40.4862, -74.4518),
    '07960': (40.7968, -74.4821),
    'YOUR_ZIP': (LAT, LON),  # Add here
}
```

### Run in production mode

```bash
# API
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Web
cd web
npm run build
# Serve dist/ folder
```

## Performance Tips

1. **Cache predictions**: Predictions update daily, cache results
2. **Use persistent storage**: Save model to database instead of file
3. **Enable compression**: Gzip responses in production
4. **Monitor performance**: Track API response times

## Security Checklist

Before deploying:

- [ ] Change default API keys in `.env`
- [ ] Set specific CORS origins (not `*`)
- [ ] Use HTTPS in production
- [ ] Keep dependencies updated
- [ ] Enable rate limiting
- [ ] Review logs for sensitive data

## What's Included

### Code Files: ~2,500 lines
- Python backend: ~1,500 lines
- React frontend: ~500 lines
- Tests: ~300 lines
- Documentation: ~200 lines

### Documentation: ~10,000 words
- README.md - Getting started
- DEPLOYMENT.md - Production deployment
- MODEL_CARD.md - ML model docs
- PROJECT_SUMMARY.md - Overview
- QUICK_START.md - This file

### Features
- Binary classification ML model
- REST API with 3 endpoints
- Interactive web interface
- Docker support
- Comprehensive tests
- Production-ready deployment configs

## Support

For questions or issues:

1. Check documentation files
2. Review code comments
3. Open an issue on GitHub
4. Email: your.email@example.com

## License

MIT License - Free to use, modify, and distribute.

---

**Ready to predict air quality? Start with `bash setup.sh`!** 🌤️

---

Built with ❤️ for cleaner air in New Jersey

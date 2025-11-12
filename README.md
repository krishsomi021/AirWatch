# WaterWatch - Next-Day Air Quality Classification for New Jersey

A full-stack web application that predicts next-day air quality in New Jersey using machine learning, classifying air as **Safe** or **Unhealthy** (AQI ≥ 101).

![WaterWatch Demo](docs/screenshot.png)

## 🎯 Features

- **Next-day AQI prediction** using LightGBM classification model
- **Real-time data collection** from EPA AirNow and National Weather Service APIs
- **Interactive web interface** for ZIP code-based queries
- **Feature engineering pipeline** with lag features, rolling averages, and weather data
- **RESTful API** with FastAPI backend
- **Docker support** for easy deployment
- **Model explainability** with feature importance and top contributing factors

## 📊 Model Performance

- **PR-AUC**: ~0.75 on test set
- **Recall**: ~85% for unhealthy days
- **Precision**: Balanced to minimize false alarms
- **Target**: Recall ≥ 80% to avoid missing unhealthy days

## 🏗️ Architecture

```
waterwatch/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # FastAPI application
│   │   ├── routers/     # API endpoints
│   │   │   ├── health.py
│   │   │   └── predict.py
│   │   ├── ml/          # ML pipeline
│   │   │   ├── features.py
│   │   │   ├── train.py
│   │   │   └── artifacts/
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── data_collector.py
│   │   └── model_loader.py
│   ├── data/            # Training data
│   ├── tests/           # Unit tests
│   └── requirements.txt
├── web/                 # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API Keys (optional):
  - [AirNow API key](https://docs.airnowapi.org/) (free)
  - NWS API requires User-Agent header (no key needed)

### Local Setup

1. **Clone and setup environment**

```bash
git clone <repository-url>
cd waterwatch
cp .env.example .env
# Edit .env with your API keys
```

2. **Backend Setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Train the Model**

```bash
# Generate sample data and train model
python app/ml/train.py
```

This creates:
- `app/ml/artifacts/aqi_model.pkl` - Trained LightGBM model
- `app/ml/artifacts/feature_list.pkl` - Feature names
- `app/ml/artifacts/pr_curve.png` - Performance visualization
- `app/ml/artifacts/feature_importance.png` - Top features

4. **Run the API**

```bash
uvicorn app.main:app --reload
```

API available at: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/api/health
- Predict: http://localhost:8000/api/predict

5. **Frontend Setup** (in a new terminal)

```bash
cd web
npm install
npm run dev
```

Web UI available at: http://localhost:3000

### Docker Setup

```bash
# Build and run with docker-compose
docker-compose up --build

# Access:
# API: http://localhost:8000
# Web: http://localhost:3000
```

## 📡 API Usage

### Get Prediction

**GET** `/api/predict?zip_code=08901`

Response:
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

### Advanced: Predict with Custom Features

**POST** `/api/predict/features`

```json
{
  "aqi_prev1": 45.0,
  "aqi_prev2": 38.0,
  "aqi_3day_avg": 42.0,
  "temp_max": 75.0,
  "wind_avg": 8.5,
  "rh_avg": 65.0,
  "precip": 0.0,
  "month": 7,
  "day_of_week": 2,
  "is_weekend": false
}
```

## 🧪 Model Training

### Using Historical EPA Data

1. **Download EPA Data**
   - Visit: https://www.epa.gov/outdoor-air-quality-data/download-daily-data
   - Select: Daily Data, PM2.5, New Jersey
   - Save to: `backend/data/raw/epa_daily_data.csv`

2. **Prepare Data**

```python
import pandas as pd
from app.ml.features import FeatureEngineer

# Load raw data
df = pd.read_csv('data/raw/epa_daily_data.csv')

# Feature engineering
engineer = FeatureEngineer()
df_features = engineer.create_features(df, is_training=True)

# Save processed data
df_features.to_csv('data/processed/training_data.csv', index=False)
```

3. **Train Model**

```bash
python app/ml/train.py
```

### Model Features

The model uses the following feature groups:

**Persistence Features:**
- `AQI_prev1`, `AQI_prev2` - Previous days' AQI
- `AQI_3day_avg`, `AQI_7day_avg` - Rolling averages
- `AQI_3day_max` - Recent maximum
- `AQI_trend` - Difference from 7-day average

**Weather Features:**
- `temp_max` - Maximum temperature
- `wind_avg` - Average wind speed
- `precip` - Precipitation amount
- `rh_avg` - Relative humidity
- Derived: `temp_wind_ratio`, `is_stagnant`, `has_rain`

**Temporal Features:**
- `month`, `day_of_week`, `is_weekend`
- `season`, `is_holiday`
- Cyclical encodings: `month_sin`, `month_cos`, `dow_sin`, `dow_cos`

## 🎨 Frontend

The React frontend provides:
- **ZIP code search** for location-specific predictions
- **Visual classification** with color-coded badges
- **Probability display** with confidence indicators
- **Contributing factors** explanation
- **Responsive design** for mobile and desktop

### Customization

Edit `web/src/index.css` to change colors and styling.
Edit `web/src/App.jsx` to modify UI components.

## 🚢 Deployment

### Render

1. Create new Web Service
2. Connect GitHub repository
3. Configure:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env`
5. Deploy!

### Fly.io

```bash
cd backend
fly launch
fly deploy
```

### Frontend (Netlify/Vercel)

```bash
cd web
npm run build
# Deploy dist/ folder
```

Set environment variable:
```
VITE_API_URL=https://your-api-url.onrender.com/api
```

## 📊 Data Sources

- **EPA AirData**: Historical PM2.5 and AQI data
- **AirNow API**: Current and forecast AQI
- **National Weather Service API**: Weather forecasts
- **OpenAQ** (optional): Alternative PM2.5 data

## 🧪 Testing

```bash
cd backend
pytest tests/
```

## 📈 Monitoring & Updates

### Daily Prediction Updates

Use a scheduled job (cron or APScheduler) to update predictions:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(update_daily_prediction, 'cron', hour=16, minute=0)
scheduler.start()
```

### Model Retraining

Retrain quarterly with new data:

```bash
# Download latest EPA data
# Run training pipeline
python app/ml/train.py --data-path data/raw/epa_2025_q1.csv
```

## 🔬 Model Explainability

View feature importance:
```bash
# Generated during training
open app/ml/artifacts/feature_importance.png
```

Key findings:
- Previous day AQI is the strongest predictor
- Wind speed significantly affects dispersion
- Temperature and precipitation play important roles
- Weekend effects are observable

## 📝 License

MIT License - See LICENSE file

## 👥 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 🐛 Known Issues & Future Work

- [ ] Integrate wildfire smoke detection
- [ ] Add county-level predictions
- [ ] Include ozone (O3) forecasts
- [ ] Mobile app development
- [ ] Email/SMS notifications
- [ ] Historical prediction accuracy tracking

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Email: your.email@example.com

## 🙏 Acknowledgments

- EPA for public air quality data
- National Weather Service for forecast data
- AirNow for real-time AQI information
- Open source community for tools and libraries

---

**Built with ❤️ for cleaner air in New Jersey**

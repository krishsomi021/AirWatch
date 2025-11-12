# Deployment Guide

This guide covers deploying WaterWatch to production environments.

## Table of Contents

- [Render Deployment](#render-deployment)
- [Fly.io Deployment](#flyio-deployment)
- [Frontend Deployment (Netlify/Vercel)](#frontend-deployment)
- [Environment Variables](#environment-variables)
- [Monitoring & Maintenance](#monitoring--maintenance)

## Render Deployment

### Backend API

1. **Create Render Account**
   - Sign up at https://render.com

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `waterwatch-api`
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   Add the following environment variables in Render dashboard:
   ```
   API_PREFIX=/api
   LOG_LEVEL=INFO
   AIRNOW_API_KEY=your_key_here
   NWS_USER_AGENT=WaterWatch-YourName-email@example.com
   PREDICTION_THRESHOLD=0.40
   ```

4. **Upload Model Artifacts**
   - Train model locally
   - Upload `aqi_model.pkl` and `feature_list.pkl` to Render using their disk storage or
   - Store in cloud storage (S3, Google Cloud Storage) and download on startup

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Your API will be at: `https://waterwatch-api.onrender.com`

### Scheduled Jobs (Optional)

For daily prediction updates:

1. **Create Cron Job** on Render
   - Click "New +" → "Cron Job"
   - Configure:
     - **Name**: `update-predictions`
     - **Schedule**: `0 16 * * *` (4 PM daily)
     - **Command**: `python app/update_predictions.py`

## Fly.io Deployment

### Backend API

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Launch App**
   ```bash
   cd backend
   fly launch
   ```
   
   This will:
   - Create a `fly.toml` configuration
   - Ask for app name and region
   - Detect Dockerfile automatically

4. **Set Secrets**
   ```bash
   fly secrets set AIRNOW_API_KEY=your_key_here
   fly secrets set NWS_USER_AGENT="WaterWatch-email@example.com"
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Check Status**
   ```bash
   fly status
   fly logs
   ```

### Custom fly.toml

Create/edit `backend/fly.toml`:

```toml
app = "waterwatch-api"
primary_region = "ewr"  # Newark (close to NJ)

[build]
  dockerfile = "Dockerfile"

[env]
  API_PREFIX = "/api"
  LOG_LEVEL = "INFO"
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/api/health"

[mounts]
  source = "waterwatch_data"
  destination = "/app/data"
```

## Frontend Deployment

### Netlify

1. **Build for Production**
   ```bash
   cd web
   npm run build
   ```

2. **Deploy to Netlify**
   ```bash
   # Install Netlify CLI
   npm install -g netlify-cli
   
   # Deploy
   netlify deploy --prod --dir=dist
   ```

3. **Configure Environment Variables**
   In Netlify dashboard, add:
   ```
   VITE_API_URL=https://waterwatch-api.onrender.com/api
   ```

### Vercel

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd web
   vercel --prod
   ```

3. **Environment Variables**
   ```bash
   vercel env add VITE_API_URL production
   # Enter: https://waterwatch-api.onrender.com/api
   ```

### Manual Static Hosting

Build and upload to any static host:

```bash
cd web
npm run build
# Upload dist/ folder to:
# - AWS S3 + CloudFront
# - Google Cloud Storage
# - GitHub Pages
# - Azure Static Web Apps
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AIRNOW_API_KEY` | AirNow API key | `ABC123...` |
| `NWS_USER_AGENT` | User agent for NWS API | `WaterWatch-email@example.com` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PREFIX` | `/api` | API route prefix |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PREDICTION_THRESHOLD` | `0.40` | Classification threshold |
| `DATABASE_URL` | `sqlite:///./waterwatch.db` | Database connection |
| `ENABLE_SCHEDULER` | `true` | Enable daily updates |
| `UPDATE_TIME` | `16:00` | Daily update time |

## Monitoring & Maintenance

### Health Checks

Monitor these endpoints:
- `/api/health` - API and model status
- `/` - Root endpoint

### Logging

**Render**: View logs in dashboard or use CLI:
```bash
render logs --tail
```

**Fly.io**: View logs:
```bash
fly logs
```

### Performance Monitoring

1. **Set up alerts** for:
   - API response time > 2s
   - Error rate > 5%
   - Model prediction failures

2. **Monitor metrics**:
   - Daily request count
   - Prediction accuracy (actual vs predicted)
   - API uptime

### Model Updates

1. **Retrain quarterly** with new data:
   ```bash
   python app/ml/train.py --data-path data/epa_2025_q1.csv
   ```

2. **Deploy new model**:
   - Upload new `.pkl` files
   - Restart service
   - Monitor prediction quality

### Database Backups

If using PostgreSQL:
```bash
# Render
render db-backups create

# Fly.io
fly postgres backup create
```

## Scaling

### Vertical Scaling (More Resources)

**Render**: Upgrade instance type in dashboard
**Fly.io**: Scale VM size
```bash
fly scale vm shared-cpu-2x
```

### Horizontal Scaling (More Instances)

**Render**: Enable autoscaling in dashboard

**Fly.io**:
```bash
fly scale count 2
```

### Caching

Implement Redis for:
- Daily predictions cache
- Frequently accessed data
- Rate limiting

```python
import redis
cache = redis.Redis(host='localhost', port=6379)
```

## Security Checklist

- [ ] API keys stored as environment variables (not in code)
- [ ] HTTPS enabled (automatic on Render/Fly.io)
- [ ] CORS configured for specific origins only
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Logs don't contain sensitive data
- [ ] Dependencies regularly updated
- [ ] Security headers configured

## Troubleshooting

### "Model not found" error
- Ensure model files are uploaded
- Check MODEL_PATH environment variable
- Verify file permissions

### API timeout
- Increase server timeout settings
- Optimize model inference
- Implement caching

### High memory usage
- Use lighter model
- Implement model lazy loading
- Scale up instance

### Prediction errors
- Check external API availability
- Verify API keys
- Review logs for details

## Cost Optimization

### Render
- Use free tier for MVP (750 hours/month)
- Scale down during low traffic
- Use cron jobs instead of always-on worker

### Fly.io
- Use `auto_stop_machines` in fly.toml
- Minimize `min_machines_running`
- Use appropriate VM size

### General
- Cache predictions
- Batch API requests
- Use CDN for frontend
- Compress responses

## Support

For deployment issues:
- Check service status pages
- Review platform documentation
- Contact support: your.email@example.com

---

**Last Updated**: 2025-11-11

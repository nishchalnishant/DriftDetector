# 🚀 Quick Start Guide - Live Data + Training

Get up and running with **live, continuously updating data** in 5 minutes!

## Step 1: Get Free API Key (30 seconds)

1. Visit https://openweathermap.org/api
2. Click "Sign Up" → Create free account
3. Go to API Keys → Copy your key
4. **Free tier**: 1,000 calls/day (plenty for this project!)

## Step 2: Install Dependencies (2 minutes)

```bash
cd DriftDetector

# Install Python dependencies
pip install -r src/training/requirements.txt
pip install -r src/data/requirements.txt
```

## Step 3: Collect Live Data (5-10 minutes)

### Option A: Quick Demo (Recommended for First Time)

Collect 2 hours of data in 10 minutes:

```bash
# Replace YOUR_KEY with your actual API key
python src/data/ingestion.py \
  --api-key YOUR_KEY \
  --duration 2 \
  --interval 600
```

**What happens**:
- ✅ Fetches live weather data from 10 global cities
- ✅ Collects every 10 minutes (2 hours = 12 readings × 10 locations = 120 samples)
- ✅ Engineers 32 features per sample
- ✅ Saves to `data/processed/train_data.parquet`
- ✅ Ready for training!

### Option B: Continuous Collection (Production Mode)

Run forever, collecting hourly:

```bash
# Set API key as environment variable
export OPENWEATHER_API_KEY="YOUR_KEY"

# Start continuous collector
python src/data/scheduler.py
```

Press Ctrl+C after a few collections, or let it run indefinitely!

## Step 4: Train Model (1 minute)

```bash
# Train with collected data
python src/training/train.py

# Or use quick start script
python src/quick_start.py
```

**Output**:
- ✅ Trained Isolation Forest model
- ✅ ONNX exported for fast inference
- ✅ Model saved to `outputs/models/`
- ✅ Metrics logged with MLflow

## Step 5: Test Inference (Optional)

```bash
# Start FastAPI server locally
cd src/serving
python main.py

# In another terminal, test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "machine_001",
    "vibration": 45.2,
    "temperature": 75.5,
    "rotational_speed": 1500.0
  }'
```

---

## 🎯 What You've Built

After these steps, you have:

✅ **Live data pipeline** with hourly updates  
✅ **Trained ML model** for anomaly detection  
✅ **Feature engineering** with 32 features  
✅ **Production-ready inference** service  
✅ **Continuous monitoring** capability  

---

## 🔄 Next Steps

### Deploy to Azure (Full Production)

```bash
# 1. Provision infrastructure
cd infra && terraform apply

# 2. Deploy to Kubernetes
helm install pred-maint ./charts/pred-maint

# 3. Set up CI/CD
# Configure GitHub secrets and push to main branch
```

### Enable Continuous Retraining

```bash
# Set GitHub token for automated retraining
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO_OWNER="your-username"
export GITHUB_REPO_NAME="DriftDetector"

# Scheduler will auto-trigger retraining after 1000 new readings!
python src/data/scheduler.py
```

### Monitor Drift

```bash
# Start drift detection service
cd src/serving
python drift_service.py

# Check drift metrics
curl http://localhost:8001/drift/latest
```

---

## 📊 Understanding the Data

### Locations Being Monitored

Your model is trained on live data from:
- 🗽 New York
- 🇬🇧 London
- 🗼 Tokyo
- 🇮🇳 Mumbai
- 🦘 Sydney
- 🏜️ Dubai
- 🦁 Singapore
- 🇩🇪 Berlin
- 🇨🇦 Toronto
- 🇧🇷 São Paulo

### Features Per Reading (32 total)

**Base Sensors** (4):
- Temperature (°C)
- Pressure (hPa)
- Humidity → Vibration
- Wind Speed → Rotational Speed

**Engineered Features** (28):
- 1-hour rolling: mean, std, min, max (×4 sensors = 16)
- 24-hour rolling: mean, std, trend (×4 sensors = 12)

---

## 🐛 Troubleshooting

### "No module named 'numpy'"

```bash
pip install numpy pandas scikit-learn
```

### "API key invalid"

Make sure you:
1. Activated your API key (check email)
2. Copied it correctly (no spaces)
3. Waited a few minutes for activation

### "Not enough data for training"

Collect more samples:
- Reduce interval: `--interval 300` (every 5 min)
- Increase duration: `--duration 4` (4 hours)
- Or wait for scheduler to collect more

---

## 💡 Tips

### Free Tier Limits

- **OpenWeatherMap**: 1,000 calls/day
- **10 locations × 24 hours = 240 calls/day**
- You have plenty of headroom!

### Faster Collection for Testing

```bash
# Collect every 5 minutes instead of hourly
python src/data/ingestion.py \
  --api-key YOUR_KEY \
  --duration 1 \
  --interval 300
```

### Check Your Data

```bash
# Verify collected data
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/train_data.parquet')
print(f'Samples: {len(df)}')
print(f'Features: {list(df.columns)}')
print(df.head())
"
```

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Get API key | 30 seconds |
| Install deps | 2 minutes |
| Collect demo data | 10 minutes |
| Train model | 1 minute |
| **Total** | **~15 minutes** |

---

**You're all set!** You now have a fully functional MLOps system with live data. 🎉

For production deployment, see the main [README.md](../README.md).

# Live and Continuous Data Sources

## 🌐 Real-Time Data Integration

This project uses **live, continuously updating data sources** instead of static datasets!

### ✅ Available Live Data Sources

#### 1. OpenWeatherMap API (Defaultand Recommended)

**FREE** - 1,000 API calls/day  
**Updates**: Every hour  
**Global Coverage**: 200,000+ cities  

**Sensor Mappings**:
- `temperature` → Temperature (°C)
- `pressure` → Atmospheric pressure (hPa)
- `vibration` → Humidity % (environmental stress indicator)
- `rotational_speed` → Wind speed (m/s)

**Get API Key**: https://openweathermap.org/api
1. Sign up for free account
2. Get API key instantly
3. 1,000 free calls/day (enough for 100 locations hourly)

#### 2. CoinGecko Crypto API

**FREE** - Unlimited with rate limiting  
**Updates**: Real-time (minute-by-minute)  
**Coverage**: 13,000+ cryptocurrencies  

**Sensor Mappings**:
- `temperature` → Price change %
- `vibration` → Volatility (24h)
- `pressure` → Trading volume
- `rotational_speed` → Current price

---

## 🚀 Quick Start - Live Data

### Option 1: Hourly Continuous Collection

```bash
# Set your API key
export OPENWEATHER_API_KEY="your_api_key_here"

# Start continuous hourly collector
python src/data/scheduler.py
```

This runs indefinitely:
- ✅ Collects data every hour from 10 global locations
- ✅ Stores to `data/live/sensor_data_latest.parquet`
- ✅ Auto-triggers retraining after 1000 readings
- ✅ Perfect for production MLOps!

### Option 2: Collect Data Once

```bash
# Collect 24 hours of data (one reading per hour)
python src/data/ingestion.py \
  --api-key YOUR_KEY \
  --duration 24 \
  --interval 3600
```

### Option 3: Quick Demo (2 hours)

```bash
#Collect 2 hours of data quickly (every 10 minutes)
python -c "
from src.data.ingestion import LiveDataPipeline

pipeline = LiveDataPipeline(api_key='YOUR_KEY')
df = pipeline.collect_live_data(duration_hours=2, interval_seconds=600)
pipeline.prepare_training_data()
"
```

---

## 📊 Data Flow Architecture

```
┌─────────────────────┐
│  OpenWeatherMap API │─── Hourly updates
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Live Data Pipeline │─── Fetch, process, engineer features
└──────────┬──────────┘
           │
           ├─► data/live/sensor_data_latest.parquet
           ├─► data/processed/train_data.parquet
           └─► data/processed/reference.parquet
                          │
                          ▼
                ┌──────────────────┐
                │  Training Script │
                └─────────┬────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Drift Detection  │───► Triggers retraining
                └──────────────────┘
```

---

## 🗺️ Default Monitoring Locations

The system monitors 10 global locations by default:

| Machine ID | Location | Latitude | Longitude |
|------------|----------|----------|-----------|
| machine_001 | New York | 40.71 | -74.01 |
| machine_002 | London | 51.51 | -0.13 |
| machine_003 | Tokyo | 35.68 | 139.65 |
| machine_004 | Mumbai | 19.08 | 72.88 |
| machine_005 | Sydney | -33.87 | 151.21 |
| machine_006 | Dubai | 25.20 | 55.27 |
| machine_007 | Singapore | 1.35 | 103.82 |
| machine_008 | Berlin | 52.52 | 13.41 |
| machine_009 | Toronto | 43.65 | -79.38 |
| machine_010 | São Paulo | -23.55 | -46.63 |

**Customize**: Edit `DEFAULT_LOCATIONS` in `src/data/ingestion.py`

---

## 🔄 Continuous Retraining

The scheduler automatically triggers model retraining:

**Triggers**:
1. ✅ Every 1,000 new readings
2. ✅ Every 24 hours
3. ✅ When drift detected (threshold: 0.3)

**GitHub Actions Integration**:
```bash
# Set GitHub token for automated retraining
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO_OWNER="your-username"
export GITHUB_REPO_NAME="DriftDetector"

# Scheduler will now trigger GitHub Actions automatically!
python src/data/scheduler.py
```

---

## 📈 Data Statistics

### Typical Collection Rates

| Interval | Locations | Readings/Day | Readings/Month |
|----------|-----------|--------------|----------------|
| 1 hour | 10 | 240 | 7,200 |
| 30 min | 10 | 480 | 14,400 |
| 15 min | 10 | 960 | 28,800 |

### Features Per Reading

- **Base**: 4 (temp, pressure, humidity, wind)
- **1-hour rolling**: 16 (mean, std, min, max × 4)
- **24-hour rolling**: 12 (mean, std, trend × 4)
- **Total**: 32 features

---

## 🎯 Use Cases

### 1. Environmental Equipment Monitoring

Monitor equipment performance based on environmental conditions:
- Temperature affects machine efficiency
- Pressure indicates altitude/weather changes
- Humidity shows environmental stress
- Wind indicates exposure conditions

### 2. Global Infrastructure Health

Track infrastructure across multiple time zones:
- Detect regional patterns
- Compare performance across locations
- Identify location-specific anomalies

### 3. MLOps Learning

Perfect for learning production MLOps:
- Real-time data pipelines
- Continuous model retraining
- Drift detection in practice
- Automated CI/CD with live data

---

## 🔧 Customization

### Add Custom Locations

Edit `src/data/ingestion.py`:

```python
CUSTOM_LOCATIONS = [
    {
        "name": "Your City",
        "lat": 12.34,
        "lon": 56.78,
        "machine_id": "machine_custom_001"
    },
    # Add more...
]

pipeline = LiveDataPipeline()
df = pipeline.collect_live_data(locations=CUSTOM_LOCATIONS)
```

### Switch to Crypto Data

```bash
python src/data/ingestion.py --source crypto --duration 24
```

### Custom Collection Schedule

Edit `scheduler.py`:

```python
# Collect every 30 minutes
schedule.every(30).minutes.do(collector.collect_hourly_data)

# Collect every day at 2 AM
schedule.every().day.at("02:00").do(collector.collect_hourly_data)
```

---

## 💡 API Key Best Practices

### Get OpenWeatherMap API Key

1. Visit https://openweathermap.org/api
2. Sign up for free account
3. Navigate to API keys section
4. Copy your key
5. **Free tier**: 1,000 calls/day

### Secure Storage

```bash
# Option 1: Environment variable
export OPENWEATHER_API_KEY="your_key_here"

# Option 2: .env file (gitignored)
echo "OPENWEATHER_API_KEY=your_key_here" >> .env

# Option 3: Azure Key Vault (production)
az keyvault secret set \
  --vault-name your-keyvault \
  --name openweather-api-key \
  --value your_key_here
```

### Monitor Usage

```python
# Check remaining quota
import requests

key = "your_key"
response = requests.get(
    f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={key}"
)
print(f"Calls remaining: {response.headers.get('X-RateLimit-Remaining')}")
```

---

## 🐛 Troubleshooting

### API Rate Limits

If you hit rate limits:

```python
# Reduce collection frequency
pipeline.collect_live_data(
    duration_hours=24,
    interval_seconds=7200  # Every 2 hours instead of 1
)

# Or reduce locations
locations = DEFAULT_LOCATIONS[:5]  # Only 5 locations
```

### Network Errors

Automatic fallback to synthetic data:

```python
# Pipeline automatically generates synthetic data if API fails
# Check logs for: "⚠️ Error fetching weather data"
```

### Large Storage

Manage data size:

```bash
# Delete old checkpoints
rm data/live/checkpoint.parquet

# Keep only latest dataset
rm data/live/sensor_data_2024*.parquet
```

---

## ✅ Advantages Over Static Datasets

| Feature | Static Dataset | Live API |
|---------|----------------|----------|
| Updates | Never | Hourly ✅ |
| Drift Detection | Simulated | Real ✅ |
| Retraining | Manual | Automatic ✅ |
| Data Size | Fixed | Growing ✅ |
| Realism | Synthetic | Real-world ✅ |
| MLOps Practice | Limited | Full pipeline ✅ |

---

**Start collecting live data now!** 🚀

```bash
python src/data/scheduler.py --api-key YOUR_KEY
```

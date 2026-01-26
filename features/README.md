# Feast Feature Store

This directory contains the Feast feature store configuration for the predictive maintenance system.

## Overview

The feature store provides:
- **Online Store**: Redis cache for low-latency feature serving (<10ms)
- **Offline Store**: File-based storage for historical features and training
- **Feature Views**: Aggregated sensor metrics at different time windows

## Features

### Entities
- `machine_id`: Unique identifier for each machine

### Feature Views

#### 1. `sensor_stats_1h` (1-hour rolling window)
- Vibration: mean, std, min, max
- Temperature: mean, std, min, max
- Rotational Speed: mean, std, min, max
- **TTL**: 24 hours
- **Use case**: Short-term anomaly detection

#### 2. `sensor_stats_24h` (24-hour rolling window)
- Vibration: mean, std, trend
- Temperature: mean, std, trend
- Rotational Speed: mean, std, trend
- Anomaly count
- **TTL**: 7 days
- **Use case**: Long-term trend analysis

#### 3. `sensor_realtime` (Real-time readings)
- Current sensor values (vibration, temperature, speed, pressure, power)
- **TTL**: 15 minutes
- **Use case**: Real-time inference

## Setup

### 1. Install Feast

```bash
pip install feast[redis]
```

### 2. Configure Environment

Set the Redis connection string:

```bash
export FEAST_REDIS_CONNECTION_STRING="rediss://:PASSWORD@HOST:PORT/0"
```

### 3. Apply Feature Definitions

```bash
cd features
feast apply
```

This will:
- Create the feature registry
- Configure online and offline stores
- Register all feature views

### 4. Materialize Features

To populate the online store from historical data:

```bash
# Materialize features for the last 7 days
feast materialize-incremental $(date -u -d '7 days ago' +"%Y-%m-%dT%H:%M:%S")
```

## Usage

### Offline Features (Training)

```python
from feast import FeatureStore
import pandas as pd

store = FeatureStore(repo_path="features")

# Get historical features for training
entity_df = pd.DataFrame({
    "machine_id": ["machine_001", "machine_002"],
    "event_timestamp": [
        pd.Timestamp("2024-01-01 12:00:00"),
        pd.Timestamp("2024-01-01 12:00:00"),
    ]
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "sensor_stats_1h:vibration_mean_1h",
        "sensor_stats_1h:temperature_mean_1h",
        "sensor_stats_24h:vibration_trend_24h",
    ],
).to_df()
```

### Online Features (Inference)

```python
from feast import FeatureStore
from datetime import datetime

store = FeatureStore(repo_path="features")

# Get real-time features for inference
features = store.get_online_features(
    features=[
        "sensor_stats_1h:vibration_mean_1h",
        "sensor_stats_1h:temperature_mean_1h",
        "sensor_realtime:vibration_current",
    ],
    entity_rows=[{"machine_id": "machine_001"}],
).to_dict()
```

## Data Schema

Historical data should be in Parquet format with the following schema:

```
event_timestamp (datetime64[ns]): Event time
created_timestamp (datetime64[ns]): Creation time
machine_id (string): Machine identifier
vibration_mean_1h (float32): ...
temperature_mean_1h (float32): ...
...
```

## Monitoring

Monitor feature freshness and availability:

```bash
# Check feature registry
feast registry-dump

# Validate feature views
feast validate
```

## Production Considerations

1. **Redis Sizing**: Premium P1 tier supports ~25GB memory, 20K ops/sec
2. **Materialization**: Schedule regular materialization jobs (hourly/daily)
3. **Monitoring**: Track feature freshness, latency, and availability
4. **Backup**: Enable Redis persistence and Azure Blob backup

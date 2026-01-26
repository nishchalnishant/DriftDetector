# Automated Data Setup Guide

## 🎯 Overview

This project includes **automated data ingestion** - no manual data downloads or uploads required!

## 🚀 Quick Start (Recommended)

### Option 1: Complete Automation

```bash
# Install dependencies
pip install -r src/training/requirements.txt

# Run complete pipeline (downloads data + trains model)
python src/quick_start.py
```

**This single command**:
- ✅ Downloads 876K+ sensor readings from Microsoft Azure
- ✅ Processes and engineers 32 features
- ✅ Trains Isolation Forest model
- ✅ Exports to ONNX format
- ✅ Ready for deployment!

### Option 2: Step-by-Step

#### 1. Install Dependencies

```bash
pip install -r src/training/requirements.txt
```

#### 2. Download and Prepare Data

```bash
cd src
python -c "
from data.ingestion import DataIngestionPipeline

pipeline = DataIngestionPipeline()
train_df, test_df = pipeline.prepare_training_data()
print(f'✅ Ready! Training: {len(train_df):,} samples')
"
```

#### 3. Train Model

```bash
python training/train.py
```

---

## 📊 Dataset Details

### Microsoft Azure Predictive Maintenance Dataset

**Source**: Azure ML Sample Experiments (Public)  
**License**: Open source, free to use  
**Download**: Automatic via HTTPS  

**Specifications**:
- **Records**: 876,000+ telemetry readings
- **Machines**: 100 industrial machines
- **Duration**: January 2015 - January 2016 (1 year)
- **Frequency**: Hourly sensor readings
- **Failures**: 761 failure events
- **Size**: ~50MB (compressed)

**Sensors**:
1. **Voltage** - Operating voltage levels
2. **Rotational Speed** - RPM measurements
3. **Pressure** - Operating pressure
4. **Vibration** - Vibration amplitude

**Machine Metadata**:
- Model type (4 models)
- Age in months
- Operating history

**Labels**:
- Normal operation: 90-95%
- Pre-failure (24h window): 5-10%

---

## 📁 Generated Files

After running data ingestion:

```
data/
├── raw/                         # Downloaded CSV files
│   ├── telemetry.csv           # ~60MB - Sensor readings
│   ├── errors.csv              # Error logs
│   ├── maint.csv               # Maintenance records
│   ├── machines.csv            # Machine metadata
│   └── failures.csv            # Failure events
│
└── processed/                   # Ready for training
    ├── train_data.parquet      # 80% train split
    ├── test_data.parquet       # 20% test split
    ├── sensor_data.parquet     # Complete dataset
    └── reference.parquet       # Drift detection baseline
```

---

## 🔧 Features Generated

### Base Features (4)
- `voltage`
- `rotational_speed`
- `pressure`
- `vibration`

### Rolling 1-Hour Features (16)
For each sensor:
- `{sensor}_mean_1h`
- `{sensor}_std_1h`
- `{sensor}_min_1h`
- `{sensor}_max_1h`

### Rolling 24-Hour Features (12)
For each sensor:
- `{sensor}_mean_24h`
- `{sensor}_std_24h`
- `{sensor}_trend_24h`

**Total: 32 features**

---

## 🎓 Usage Examples

### Basic Usage

```python
from src.data.ingestion import DataIngestionPipeline

# Initialize
pipeline = DataIngestionPipeline(
    data_dir="data/raw",
    processed_dir="data/processed"
)

# Download and process
train_df, test_df = pipeline.prepare_training_data(
    test_size=0.2,
    save_to_disk=True
)

print(f"Training samples: {len(train_df):,}")
print(f"Features: {train_df.shape[1]}")
print(f"Anomaly rate: {train_df['is_anomaly'].mean():.2%}")
```

### Get Feature Names

```python
features = pipeline.get_feature_names()
print(f"Total features: {len(features)}")
print(features)
```

### Custom Processing

```python
# Fetch raw data
telemetry = pipeline.fetch_azure_predictive_maintenance_data()

# Apply custom transformations
telemetry['power'] = telemetry['voltage'] * telemetry['rotational_speed']

# Create rolling features
df = pipeline.create_rolling_features(telemetry)
```

---

## 🔄 Alternative Datasets

The ingestion module supports multiple datasets. To switch:

### Option 1: Modify Source

Edit `src/data/ingestion.py`:

```python
class DataIngestionPipeline:
    # Change to your preferred dataset
    CUSTOM_URL = "https://your-dataset-url.com/data.csv"
    
    def fetch_custom_data(self):
        # Add your custom logic
        pass
```

### Option 2: Provide Custom Data

```bash
# Skip auto-download, use your own data
python training/train.py --data_path /path/to/your/data.parquet
```

**Required columns**:
- `machine_id` (string)
- `event_timestamp` (datetime)
- Sensor columns (float)
- `is_anomaly` (int, 0 or 1) - optional

---

## 🐛 Troubleshooting

### Issue: Download Fails

```bash
# Check internet connection
ping azuremlsampleexperiments.blob.core.windows.net

# Retry with verbose output
python -c "
from src.data.ingestion import DataIngestionPipeline
import logging
logging.basicConfig(level=logging.DEBUG)

pipeline = DataIngestionPipeline()
pipeline.prepare_training_data()
"
```

### Issue: Out of Memory

```python
# Process in smaller batches
pipeline = DataIngestionPipeline()

# Reduce window size
DRIFT_WINDOW_SIZE = 500  # Instead of 1000
```

### Issue: Slow Processing

```bash
# Check available resources
python -c "
import psutil
print(f'CPU cores: {psutil.cpu_count()}')
print(f'RAM: {psutil.virtual_memory().total / 1e9:.1f} GB')
"

# Processing 876K records typically takes 2-5 minutes
```

---

## ✅ Verification

After data ingestion, verify:

```bash
# Check files exist
ls -lh data/processed/

# Validate data
python -c "
import pandas as pd

train = pd.read_parquet('data/processed/train_data.parquet')
print(f'✓ Training samples: {len(train):,}')
print(f'✓ Features: {len(train.columns)}')
print(f'✓ Anomalies: {train[\"is_anomaly\"].sum():,}')
print(f'✓ Time range: {train[\"event_timestamp\"].min()} to {train[\"event_timestamp\"].max()}')
"
```

Expected output:
```
✓ Training samples: 700,000+
✓ Features: 35+
✓ Anomalies: 40,000+
✓ Time range: 2015-01-01 to 2015-10-01
```

---

## 💡 Benefits

✅ **Zero manual work** - Fully automated  
✅ **Real-world data** - Not synthetic  
✅ **Production-ready** - Same format as deployed system  
✅ **Reproducible** - Same data every time  
✅ **Well-documented** - Clear feature engineering  
✅ **Scalable** - Handles large datasets efficiently  

---

## 📚 References

- [Microsoft Azure ML Samples](https://github.com/Azure/MachineLearningNotebooks)
- [Predictive Maintenance Overview](https://learn.microsoft.com/en-us/azure/architecture/industries/manufacturing/predictive-maintenance-overview)
- [Dataset Documentation](https://gallery.azure.ai/Experiment/Predictive-Maintenance-Step-1-of-3-data-preparation-and-feature-engineering-2)

---

**Ready to train? Just run `python src/quick_start.py` 🚀**

"""
Generate synthetic sensor data for training
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

print('🔧 Generating synthetic sensor data for training...')

# Create data directories
Path('data/processed').mkdir(parents=True, exist_ok=True)
Path('outputs/models').mkdir(parents=True, exist_ok=True)

# Generate synthetic sensor data (simulation of 10 machines, 1000 readings each)
np.random.seed(42)
n_samples = 10000
n_machines = 10

data = []
for machine_id in range(1, n_machines + 1):
    for i in range(n_samples // n_machines):
        # Normal operating conditions
        is_anomaly = np.random.random() < 0.1  # 10% anomaly rate
        
        if is_anomaly:
            temp = np.random.normal(80, 15)  # High temperature
            pressure = np.random.normal(1050, 20)  # High pressure
            vibration = np.random.normal(80, 10)  # High vibration
        else:
            temp = np.random.normal(25, 5)  # Normal temperature
            pressure = np.random.normal(1013, 10)  # Normal pressure  
            vibration = np.random.normal(45, 10)  # Normal vibration
        
        reading = {
            'machine_id': f'machine_{machine_id:03d}',
            'event_timestamp': datetime.now() - timedelta(hours=i),
            'temperature': temp,
            'pressure': pressure,
            'vibration': vibration,
            'rotational_speed': np.random.normal(1500, 100),
            'is_anomaly': int(is_anomaly)
        }
        data.append(reading)

df = pd.DataFrame(data)

# Add rolling features (required for model)
for machine_id in df['machine_id'].unique():
    mask = df['machine_id'] == machine_id
    machine_data = df[mask].copy()
    
    for col in ['temperature', 'pressure', 'vibration', 'rotational_speed']:
        df.loc[mask, f'{col}_mean_1h'] = machine_data[col].rolling(1, min_periods=1).mean()
        df.loc[mask, f'{col}_std_1h'] = machine_data[col].rolling(1, min_periods=1).std().fillna(0)
        df.loc[mask, f'{col}_mean_24h'] = machine_data[col].rolling(24, min_periods=1).mean()
        df.loc[mask, f'{col}_std_24h'] = machine_data[col].rolling(24, min_periods=1).std().fillna(0)
        df.loc[mask, f'{col}_trend_24h'] = machine_data[col] - df.loc[mask, f'{col}_mean_24h']
        df.loc[mask, f'{col}_min_1h'] = machine_data[col]
        df.loc[mask, f'{col}_max_1h'] = machine_data[col]

# Split data
train_size = int(len(df) * 0.8)
train_df = df[:train_size]
test_df = df[train_size:]

# Save datasets
train_df.to_parquet('data/processed/train_data.parquet', index=False)
test_df.to_parquet('data/processed/test_data.parquet', index=False)
df.to_parquet('data/processed/sensor_data.parquet', index=False)
train_df.head(1000).to_parquet('data/processed/reference.parquet', index=False)

print(f'✅ Dataset created successfully!')
print(f'   Total samples: {len(df):,}')
print(f'   Training: {len(train_df):,}')
print(f'   Testing: {len(test_df):,}')
print(f'   Machines: {df["machine_id"].nunique()}')
print(f'   Anomaly rate: {df["is_anomaly"].mean():.2%}')
print(f'   Features: {len([c for c in df.columns if "_" in c and c != "machine_id"])}')

"""
Feast Feature Definitions for Predictive Maintenance

This module defines:
- Entities: machine_id
- Feature views: sensor statistics at different time windows
- Data sources: historical sensor data
"""

from datetime import timedelta
from feast import Entity, Feature, FeatureView, FileSource, ValueType
from feast.types import Float32, Float64, Int64, String


# ===========================
# Entities
# ===========================

machine_entity = Entity(
    name="machine_id",
    description="Unique identifier for each machine/equipment",
    value_type=ValueType.STRING,
)


# ===========================
# Data Sources
# ===========================

# Historical sensor data source
sensor_data_source = FileSource(
    name="sensor_data",
    path="data/offline/sensor_data.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)


# ===========================
# Feature Views
# ===========================

# 1-hour rolling window aggregations
sensor_stats_1h = FeatureView(
    name="sensor_stats_1h",
    entities=[machine_entity],
    ttl=timedelta(hours=24),
    schema=[
        Feature(name="vibration_mean_1h", dtype=Float32),
        Feature(name="vibration_std_1h", dtype=Float32),
        Feature(name="vibration_min_1h", dtype=Float32),
        Feature(name="vibration_max_1h", dtype=Float32),
        Feature(name="temperature_mean_1h", dtype=Float32),
        Feature(name="temperature_std_1h", dtype=Float32),
        Feature(name="temperature_min_1h", dtype=Float32),
        Feature(name="temperature_max_1h", dtype=Float32),
        Feature(name="rotational_speed_mean_1h", dtype=Float32),
        Feature(name="rotational_speed_std_1h", dtype=Float32),
        Feature(name="rotational_speed_min_1h", dtype=Float32),
        Feature(name="rotational_speed_max_1h", dtype=Float32),
    ],
    online=True,
    source=sensor_data_source,
    tags={"team": "ml-ops", "use_case": "predictive_maintenance"},
)

# 24-hour rolling window aggregations for trend analysis
sensor_stats_24h = FeatureView(
    name="sensor_stats_24h",
    entities=[machine_entity],
    ttl=timedelta(days=7),
    schema=[
        Feature(name="vibration_mean_24h", dtype=Float32),
        Feature(name="vibration_std_24h", dtype=Float32),
        Feature(name="vibration_trend_24h", dtype=Float32),
        Feature(name="temperature_mean_24h", dtype=Float32),
        Feature(name="temperature_std_24h", dtype=Float32),
        Feature(name="temperature_trend_24h", dtype=Float32),
        Feature(name="rotational_speed_mean_24h", dtype=Float32),
        Feature(name="rotational_speed_std_24h", dtype=Float32),
        Feature(name="rotational_speed_trend_24h", dtype=Float32),
        Feature(name="anomaly_count_24h", dtype=Int64),
    ],
    online=True,
    source=sensor_data_source,
    tags={"team": "ml-ops", "use_case": "predictive_maintenance"},
)

# Real-time sensor readings
sensor_realtime = FeatureView(
    name="sensor_realtime",
    entities=[machine_entity],
    ttl=timedelta(minutes=15),
    schema=[
        Feature(name="vibration_current", dtype=Float32),
        Feature(name="temperature_current", dtype=Float32),
        Feature(name="rotational_speed_current", dtype=Float32),
        Feature(name="pressure_current", dtype=Float32),
        Feature(name="power_consumption_current", dtype=Float32),
    ],
    online=True,
    source=sensor_data_source,
    tags={"team": "ml-ops", "use_case": "predictive_maintenance", "latency": "realtime"},
)

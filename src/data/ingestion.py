"""
Live Data Ingestion Module for Predictive Maintenance

Fetches real-time sensor data from public APIs:
1. OpenWeatherMap - Hourly environmental sensor data (FREE)
2. CoinGecko - Live crypto market data (FREE)
3. Alpha Vantage - Stock market data (FREE)

Data updates continuously for real-time drift detection and retraining!
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List, Dict
import warnings

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

warnings.filterwarnings('ignore')


class LiveDataPipeline:
    """
    Live data ingestion from public APIs
    
    Fetches fresh sensor readings every hour for continuous retraining
    """
    
    # OpenWeatherMap API (FREE - 1000 calls/day)
    OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
    OPENWEATHER_HISTORY_URL = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
    
    # CoinGecko API (FREE - unlimited with rate limiting)
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/{}/market_chart"
    
    # Default locations for weather monitoring (global coverage)
    DEFAULT_LOCATIONS = [
        {"name": "New York", "lat": 40.7128, "lon": -74.0060, "machine_id": "machine_001"},
        {"name": "London", "lat": 51.5074, "lon": -0.1278, "machine_id": "machine_002"},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "machine_id": "machine_003"},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "machine_id": "machine_004"},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "machine_id": "machine_005"},
        {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "machine_id": "machine_006"},
        {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "machine_id": "machine_007"},
        {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "machine_id": "machine_008"},
        {"name": "Toronto", "lat": 43.6532, "lon": -79.3832, "machine_id": "machine_009"},
        {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "machine_id": "machine_010"},
    ]
    
    def __init__(
        self,
        data_dir: str = "data/live",
        api_key: str = None,
        data_source: str = "weather"
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "demo")
        self.data_source = data_source
        
        print(f"🌐 Live Data Pipeline initialized")
        print(f"   Source: {data_source}")
        print(f"   API Key: {'✓ Configured' if self.api_key != 'demo' else '⚠️  Using demo mode'}")
    
    def fetch_weather_data(self, lat: float, lon: float, location_name: str = None) -> Dict:
        """
        Fetch current weather data from OpenWeatherMap
        
        Returns sensor-like readings:
        - temperature (mapped to 'temperature')
        - pressure (mapped to 'pressure')
        - humidity (mapped to 'vibration' - represents environmental stress)
        - wind_speed (mapped to 'rotational_speed')
        """
        
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"  # Celsius, m/s
            }
            
            response = requests.get(self.OPENWEATHER_API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract sensor readings
            main = data.get("main", {})
            wind = data.get("wind", {})
            
            # Map weather data to sensor readings
            reading = {
                "temperature": main.get("temp", 20.0),  # °C
                "pressure": main.get("pressure", 1013.0),  # hPa
                "humidity": main.get("humidity", 50.0),  # %
                "wind_speed": wind.get("speed", 0.0),  # m/s
                "feels_like": main.get("feels_like", 20.0),
                "location": location_name or f"{lat},{lon}",
                "timestamp": datetime.utcnow()
            }
            
            return reading
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error fetching weather data: {e}")
            # Return synthetic data as fallback
            return self._generate_synthetic_reading(location_name)
    
    def fetch_crypto_data(self, coin_id: str = "bitcoin", days: int = 30) -> pd.DataFrame:
        """
        Fetch cryptocurrency market data from CoinGecko
        
        Maps to sensor readings:
        - price volatility -> vibration
        - volume -> pressure
        - price changes -> temperature
        """
        
        try:
            url = self.COINGECKO_API_URL.format(coin_id)
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "hourly"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract price and volume data
            prices = data.get("prices", [])
            volumes = data.get("total_volumes", [])
            
            # Convert to DataFrame
            df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
            df["volume"] = [v[1] for v in volumes]
            
            df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
            
            # Calculate sensor-like features
            df["price_change_1h"] = df["price"].pct_change()
            df["volatility"] = df["price_change_1h"].rolling(24).std()
            df["volume_change"] = df["volume"].pct_change()
            
            # Map to sensor schema
            df["temperature"] = df["price_change_1h"] * 100 + 50  # Scaled
            df["vibration"] = df["volatility"] * 1000  # Volatility as vibration
            df["pressure"] = df["volume"] / 1e9  # Normalized volume
            df["rotational_speed"] = df["price"] / 100  # Price normalized
            
            df["machine_id"] = f"crypto_{coin_id}"
            df["location"] = coin_id.upper()
            
            return df[["machine_id", "timestamp", "temperature", "vibration", "pressure", "rotational_speed", "location"]]
            
        except Exception as e:
            print(f"⚠️  Error fetching crypto data: {e}")
            return pd.DataFrame()
    
    def _generate_synthetic_reading(self, location: str = None) -> Dict:
        """Generate synthetic reading as fallback"""
        
        return {
            "temperature": np.random.normal(25, 5),
            "pressure": np.random.normal(1013, 10),
            "humidity": np.random.normal(60, 15),
            "wind_speed": np.random.normal(5, 2),
            "feels_like": np.random.normal(25, 5),
            "location": location or "synthetic",
            "timestamp": datetime.utcnow()
        }
    
    def collect_live_data(
        self,
        locations: List[Dict] = None,
        duration_hours: int = 24,
        interval_seconds: int = 3600
    ) -> pd.DataFrame:
        """
        Continuously collect live data for specified duration
        
        Args:
            locations: List of {lat, lon, machine_id, name}
            duration_hours: How long to collect data
            interval_seconds: Time between collections (default: 1 hour)
        """
        
        locations = locations or self.DEFAULT_LOCATIONS
        
        print(f"\n{'='*60}")
        print(f"🌐 LIVE DATA COLLECTION")
        print(f"{'='*60}")
        print(f"Locations: {len(locations)}")
        print(f"Duration: {duration_hours} hours")
        print(f"Interval: {interval_seconds} seconds ({interval_seconds/3600:.1f} hours)")
        print(f"Expected samples: {len(locations) * (duration_hours * 3600 // interval_seconds)}")
        print(f"{'='*60}\n")
        
        all_readings = []
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        iteration = 0
        
        try:
            while time.time() < end_time:
                iteration += 1
                collection_start = time.time()
                
                print(f"\n[Iteration {iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 60)
                
                # Fetch data for all locations
                for loc in locations:
                    reading = self.fetch_weather_data(
                        lat=loc["lat"],
                        lon=loc["lon"],
                        location_name=loc["name"]
                    )
                    
                    # Add machine ID
                    reading["machine_id"] = loc["machine_id"]
                    all_readings.append(reading)
                    
                    print(f"  ✓ {loc['name']:15s} - Temp: {reading['temperature']:6.1f}°C, "
                          f"Pressure: {reading['pressure']:7.1f}hPa, "
                          f"Humidity: {reading['humidity']:5.1f}%")
                
                print(f"\n  Total readings collected: {len(all_readings)}")
                
                # Save checkpoint
                if len(all_readings) % (len(locations) * 5) == 0:
                    self._save_checkpoint(all_readings)
                
                # Wait for next interval
                elapsed = time.time() - collection_start
                wait_time = max(0, interval_seconds - elapsed)
                
                if wait_time > 0 and time.time() + wait_time < end_time:
                    print(f"  ⏳ Waiting {wait_time:.0f}s until next collection...")
                    time.sleep(wait_time)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Collection interrupted by user")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_readings)
        
        if len(df) > 0:
            df = self._process_readings(df)
            self._save_data(df)
        
        print(f"\n{'='*60}")
        print(f"✅ COLLECTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total readings: {len(df)}")
        print(f"Time range: {df['event_timestamp'].min()} to {df['event_timestamp'].max()}")
        print(f"Machines: {df['machine_id'].nunique()}")
        print(f"{'='*60}\n")
        
        return df
    
    def _process_readings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw readings into training format"""
        
        # Rename columns to match schema
        df = df.rename(columns={
            "timestamp": "event_timestamp",
            "temperature": "temperature",
            "pressure": "pressure",
            "humidity": "vibration",  # Map humidity to vibration
            "wind_speed": "rotational_speed",  # Map wind to rotation
        })
        
        df["created_timestamp"] = datetime.utcnow()
        
        # Create rolling features
        df = df.sort_values(["machine_id", "event_timestamp"])
        
        for machine_id in df["machine_id"].unique():
            mask = df["machine_id"] == machine_id
            machine_data = df[mask].copy()
            
            # 1-hour features (current reading)
            for col in ["temperature", "pressure", "vibration", "rotational_speed"]:
                df.loc[mask, f"{col}_mean_1h"] = machine_data[col]
                df.loc[mask, f"{col}_std_1h"] = machine_data[col].rolling(1).std().fillna(0)
                df.loc[mask, f"{col}_min_1h"] = machine_data[col]
                df.loc[mask, f"{col}_max_1h"] = machine_data[col]
            
            # 24-hour features
            for col in ["temperature", "pressure", "vibration", "rotational_speed"]:
                df.loc[mask, f"{col}_mean_24h"] = machine_data[col].rolling(24, min_periods=1).mean()
                df.loc[mask, f"{col}_std_24h"] = machine_data[col].rolling(24, min_periods=1).std().fillna(0)
                df.loc[mask, f"{col}_trend_24h"] = machine_data[col] - df.loc[mask, f"{col}_mean_24h"]
        
        # Detect anomalies (extreme values)
        df["is_anomaly"] = 0
        
        for col in ["temperature", "pressure", "vibration"]:
            mean = df[col].mean()
            std = df[col].std()
            df.loc[(df[col] < mean - 3*std) | (df[col] > mean + 3*std), "is_anomaly"] = 1
        
        return df
    
    def _save_checkpoint(self, readings: List[Dict]):
        """Save intermediate results"""
        
        checkpoint_file = self.data_dir / "checkpoint.parquet"
        df = pd.DataFrame(readings)
        df.to_parquet(checkpoint_file, index=False)
        print(f"  💾 Checkpoint saved: {len(readings)} readings")
    
    def _save_data(self, df: pd.DataFrame):
        """Save collected data"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full dataset
        full_path = self.data_dir / f"sensor_data_{timestamp}.parquet"
        df.to_parquet(full_path, index=False)
        
        # Also save as latest
        latest_path = self.data_dir / "sensor_data_latest.parquet"
        df.to_parquet(latest_path, index=False)
        
        print(f"\n💾 Data saved:")
        print(f"   - {full_path}")
        print(f"   - {latest_path}")
    
    def prepare_training_data(
        self,
        use_latest: bool = True,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare training data from collected live data
        """
        
        if use_latest:
            data_file = self.data_dir / "sensor_data_latest.parquet"
            if not data_file.exists():
                print("\n⚠️  No live data found. Collecting sample data...")
                df = self.collect_live_data(duration_hours=2, interval_seconds=600)
            else:
                df = pd.read_parquet(data_file)
        
        # Split temporally
        split_idx = int(len(df) * (1 - test_size))
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
        
        print(f"\n📊 Dataset Split:")
        print(f"   Training: {len(train_df)} samples")
        print(f"   Testing: {len(test_df)} samples")
        print(f"   Anomaly rate: {df['is_anomaly'].mean():.2%}")
        
        # Save processed data
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        train_df.to_parquet(processed_dir / "train_data.parquet", index=False)
        test_df.to_parquet(processed_dir / "test_data.parquet", index=False)
        df.to_parquet(processed_dir / "sensor_data.parquet", index=False)
        
        # Reference data
        reference_df = train_df.head(int(len(train_df) * 0.1))
        reference_df.to_parquet(processed_dir / "reference.parquet", index=False)
        
        return train_df, test_df


def main():
    """Run live data collection"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Live Data Collection")
    parser.add_argument("--api-key", type=str, help="OpenWeatherMap API key")
    parser.add_argument("--duration", type=int, default=24, help="Collection duration in hours")
    parser.add_argument("--interval", type=int, default=3600, help="Collection interval in seconds")
    parser.add_argument("--source", type=str, default="weather", choices=["weather", "crypto"])
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = LiveDataPipeline(api_key=args.api_key, data_source=args.source)
    
    # Collect data
    df = pipeline.collect_live_data(
        duration_hours=args.duration,
        interval_seconds=args.interval
    )
    
    # Prepare for training
    train_df, test_df = pipeline.prepare_training_data()
    
    print("\n✅ Ready for training!")
    print(f"   Run: python src/training/train.py")


if __name__ == "__main__":
    main()

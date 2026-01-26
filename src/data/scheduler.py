"""
Live Data Scheduler - Continuous Collection and Retraining

Runs as a background service to:
1. Collect live sensor data hourly
2. Detect drift automatically
3. Trigger model retraining when needed

Perfect for production MLOps with continuous learning!
"""

import os
import time
import schedule
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.ingestion import LiveDataPipeline


class ContinuousDataCollector:
    """Background service for continuous data collection"""
    
    def __init__(self, api_key: str = None):
        self.pipeline = LiveDataPipeline(api_key=api_key)
        self.last_collection = None
        self.total_readings = 0
    
    def collect_hourly_data(self):
        """Collect data from all locations (runs every hour)"""
        
        print(f"\n{'='*60}")
        print(f"⏰ HOURLY DATA COLLECTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        try:
            # Collect one round of data
            df = self.pipeline.collect_live_data(
                duration_hours=0.02,  # Just collect once
                interval_seconds=1
            )
            
            self.total_readings += len(df)
            self.last_collection = datetime.now()
            
            # Prepare training data
            train_df, test_df = self.pipeline.prepare_training_data()
            
            print(f"\n✅ Collection complete!")
            print(f"   Readings this hour: {len(df)}")
            print(f"   Total readings: {self.total_readings}")
            print(f"   Training samples: {len(train_df)}")
            
            # Check if retraining is needed (every 24 hours or 1000+ new readings)
            if self.total_readings >= 1000:
                print("\n🔄 Triggering model retraining...")
                self.trigger_retraining()
                self.total_readings = 0  # Reset counter
        
        except Exception as e:
            print(f"❌ Error during collection: {e}")
    
    def trigger_retraining(self):
        """Trigger model retraining via GitHub Actions webhook"""
        
        import requests
        
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("GITHUB_REPO_OWNER", "your-username")
        repo_name = os.getenv("GITHUB_REPO_NAME", "DriftDetector")
        
        if not github_token:
            print("⚠️  GITHUB_TOKEN not set. Skipping automated retraining.")
            print("   Set GITHUB_TOKEN to enable automatic retraining.")
            return
        
        # Trigger GitHub Actions workflow
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "event_type": "drift-detected",
            "client_payload": {
                "reason": "continuous_data_collection",
                "readings_count": self.total_readings,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            print("✅ Retraining workflow triggered successfully!")
        except Exception as e:
            print(f"❌ Failed to trigger retraining: {e}")
    
    def run_scheduler(self):
        """Run continuous collection scheduler"""
        
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║  CONTINUOUS DATA COLLECTION SCHEDULER                    ║
        ╚══════════════════════════════════════════════════════════╝
        
        📊 Schedule:
           - Hourly data collection from 10 global locations
           - Automatic drift detection
           - Model retraining every 1000 readings or 24 hours
        
        🌐 Data Sources:
           - OpenWeatherMap API (environmental sensors)
           - Real-time updates every hour
           - Persistent storage for historical analysis
        
        Press Ctrl+C to stop...
        """)
        
        # Schedule hourly collection
        schedule.every().hour.at(":00").do(self.collect_hourly_data)
        
        # Also run immediately on start
        print("\n🚀 Running initial collection...")
        self.collect_hourly_data()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n🛑 Scheduler stopped by user")
            print(f"   Total readings collected: {self.total_readings}")


def main():
    """Start continuous data collector"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Data Collection Scheduler")
    parser.add_argument("--api-key", type=str, help="OpenWeatherMap API key (or set OPENWEATHER_API_KEY env var)")
    parser.add_argument("--once", action="store_true", help="Collect data once and exit")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        print("\n⚠️  WARNING: No API key provided!")
        print("   Get free API key: https://openweathermap.org/api")
        print("   Usage:")
        print("     python scheduler.py --api-key YOUR_KEY")
        print("     OR export OPENWEATHER_API_KEY=YOUR_KEY\n")
        
        response = input("Continue with demo mode? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Create collector
    collector = ContinuousDataCollector(api_key=api_key)
    
    if args.once:
        # Run once and exit
        collector.collect_hourly_data()
    else:
        # Run continuous scheduler
        collector.run_scheduler()


if __name__ == "__main__":
    main()

"""
IoT Sensor Data Simulator for Predictive Maintenance

Generates realistic sensor data with:
- Normal operating conditions
- Gradual degradation patterns
- Sudden failures
- Configurable drift injection
"""

import argparse
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import random

import numpy as np
import pandas as pd
import requests


class SensorSimulator:
    """Simulate IoT sensor data for industrial equipment"""
    
    def __init__(
        self,
        num_machines: int = 10,
        failure_probability: float = 0.01,
        drift_enabled: bool = False,
        drift_start_time: int = 3600
    ):
        self.num_machines = num_machines
        self.failure_probability = failure_probability
        self.drift_enabled = drift_enabled
        self.drift_start_time = drift_start_time
        self.start_time = time.time()
        
        # Baseline operating parameters
        self.baselines = {
            "vibration": {"mean": 45.0, "std": 5.0},
            "temperature": {"mean": 75.0, "std": 3.0},
            "rotational_speed": {"mean": 1500.0, "std": 50.0},
            "pressure": {"mean": 2.5, "std": 0.2},
            "power_consumption": {"mean": 15.0, "std": 1.5},
        }
        
        # Machine states
        self.machine_states = {
            f"machine_{i:03d}": {"status": "normal", "degradation": 0.0}
            for i in range(num_machines)
        }
    
    def generate_reading(self, machine_id: str) -> Dict:
        """Generate a single sensor reading for a machine"""
        
        state = self.machine_states[machine_id]
        elapsed_time = time.time() - self.start_time
        
        # Check for drift injection
        drift_factor = 0.0
        if self.drift_enabled and elapsed_time > self.drift_start_time:
            # Gradual drift over time
            drift_factor = min((elapsed_time - self.drift_start_time) / 3600, 0.5)
        
        # Base values with noise
        vibration = np.random.normal(
            self.baselines["vibration"]["mean"] * (1 + state["degradation"] + drift_factor),
            self.baselines["vibration"]["std"] * (1 + state["degradation"])
        )
        
        temperature = np.random.normal(
            self.baselines["temperature"]["mean"] * (1 + state["degradation"] * 0.5 + drift_factor),
            self.baselines["temperature"]["std"]
        )
        
        rotational_speed = np.random.normal(
            self.baselines["rotational_speed"]["mean"] * (1 - state["degradation"] * 0.2),
            self.baselines["rotational_speed"]["std"] * (1 + state["degradation"])
        )
        
        pressure = np.random.normal(
            self.baselines["pressure"]["mean"] * (1 - state["degradation"] * 0.1),
            self.baselines["pressure"]["std"]
        )
        
        power_consumption = np.random.normal(
            self.baselines["power_consumption"]["mean"] * (1 + state["degradation"] * 0.3),
            self.baselines["power_consumption"]["std"]
        )
        
        # Detect if machine is in failure state
        is_anomaly = state["status"] != "normal" or state["degradation"] > 0.3
        
        return {
            "machine_id": machine_id,
            "vibration": max(0, vibration),
            "temperature": temperature,
            "rotational_speed": max(0, rotational_speed),
            "pressure": max(0, pressure),
            "power_consumption": max(0, power_consumption),
            "is_anomaly": is_anomaly,
            "event_timestamp": datetime.utcnow().isoformat(),
            "created_timestamp": datetime.utcnow().isoformat(),
        }
    
    def update_machine_states(self):
        """Update machine degradation and failure states"""
        
        for machine_id, state in self.machine_states.items():
            # Normal degradation
            if state["status"] == "normal":
                state["degradation"] += random.uniform(0, 0.001)
                
                # Random failure
                if random.random() < self.failure_probability:
                    state["status"] = "failing"
                    state["degradation"] = random.uniform(0.5, 0.8)
                    print(f"⚠️  {machine_id} entering failure state")
            
            # Recovery from failure
            elif state["status"] == "failing":
                if random.random() < 0.05:  # 5% chance of recovery
                    state["status"] = "normal"
                    state["degradation"] = 0.0
                    print(f"✅ {machine_id} recovered to normal state")
    
    def generate_batch(self) -> List[Dict]:
        """Generate readings for all machines"""
        
        self.update_machine_states()
        
        readings = []
        for machine_id in self.machine_states.keys():
            reading = self.generate_reading(machine_id)
            readings.append(reading)
        
        return readings
    
    def save_to_file(self, readings: List[Dict], filepath: str):
        """Save readings to file"""
        
        df = pd.DataFrame(readings)
        
        if filepath.endswith('.parquet'):
            df.to_parquet(filepath, index=False)
        elif filepath.endswith('.csv'):
            df.to_csv(filepath, index=False)
        else:
            with open(filepath, 'a') as f:
                for reading in readings:
                    f.write(json.dumps(reading) + '\n')
    
    def send_to_endpoint(self, readings: List[Dict], endpoint: str):
        """Send readings to HTTP endpoint"""
        
        try:
            for reading in readings:
                response = requests.post(
                    f"{endpoint}/predict",
                    json=reading,
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("is_anomaly"):
                        print(f"🚨 Anomaly detected for {reading['machine_id']}: score={result['anomaly_score']:.3f}")
                else:
                    print(f"❌ Request failed: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")


def main():
    parser = argparse.ArgumentParser(description="IoT Sensor Data Simulator")
    parser.add_argument("--num-machines", type=int, default=10, help="Number of machines")
    parser.add_argument("--interval", type=int, default=60, help="Generation interval in seconds")
    parser.add_argument("--duration", type=int, default=3600, help="Total duration in seconds")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--endpoint", type=str, help="HTTP endpoint URL")
    parser.add_argument("--drift", action="store_true", help="Enable drift injection")
    parser.add_argument("--drift-after", type=int, default=1800, help="Start drift after N seconds")
    
    args = parser.parse_args()
    
    print(f"Starting sensor simulator:")
    print(f"  Machines: {args.num_machines}")
    print(f"  Interval: {args.interval}s")
    print(f"  Duration: {args.duration}s")
    print(f"  Drift enabled: {args.drift}")
    
    simulator = SensorSimulator(
        num_machines=args.num_machines,
        drift_enabled=args.drift,
        drift_start_time=args.drift_after
    )
    
    start_time = time.time()
    iteration = 0
    
    try:
        while time.time() - start_time < args.duration:
            iteration += 1
            print(f"\n[Iteration {iteration}] Generating readings...")
            
            readings = simulator.generate_batch()
            
            # Save to file if specified
            if args.output:
                simulator.save_to_file(readings, args.output)
                print(f"📝 Saved {len(readings)} readings to {args.output}")
            
            # Send to endpoint if specified
            if args.endpoint:
                simulator.send_to_endpoint(readings, args.endpoint)
            
            # Display summary
            anomalies = sum(1 for r in readings if r["is_anomaly"])
            print(f"📊 Summary: {len(readings)} readings, {anomalies} anomalies")
            
            # Wait for next iteration
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user")
    
    print(f"\n✅ Simulation complete. Generated {iteration} batches.")


if __name__ == "__main__":
    main()

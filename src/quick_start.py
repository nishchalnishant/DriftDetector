"""
Quick Start Script - Train Model with Real Data

This script automatically:
1. Downloads public predictive maintenance dataset
2. Prepares and engineers features
3. Trains Isolation Forest model
4. Exports to ONNX for deployment

No manual data required!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data.ingestion import DataIngestionPipeline
from training.train import main as train_main


def quick_start():
    """One-command training pipeline"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  PREDICTIVE MAINTENANCE - AUTOMATED TRAINING PIPELINE    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Data Ingestion
    print("\n📥 STEP 1: Automated Data Ingestion")
    print("-" * 60)
    
    pipeline = DataIngestionPipeline()
    train_df, test_df = pipeline.prepare_training_data(save_to_disk=True)
    
    print(f"""
    ✅ Data Ready:
       - Training samples: {len(train_df):,}
       - Testing samples: {len(test_df):,}
       - Features: {len(pipeline.get_feature_names())}
       - Anomaly rate: {train_df['is_anomaly'].mean():.2%}
    """)
    
    # Step 2: Model Training
    print("\n🤖 STEP 2: Model Training")
    print("-" * 60)
    
    # Train model using the prepared data
    import argparse
    
    # Override sys.argv for training script
    sys.argv = [
        'train.py',
        '--contamination', '0.1',
        '--n_estimators', '100',
        '--max_samples', '256',
        '--output_dir', 'outputs/models'
    ]
    
    # Run training
    train_main()
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✅ TRAINING COMPLETE!                                   ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Next Steps:                                             ║
    ║  1. Check outputs/models/ for trained model             ║
    ║  2. Deploy using: helm install pred-maint ./charts      ║
    ║  3. Test with simulator: python scripts/simulator.py    ║
    ╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    quick_start()

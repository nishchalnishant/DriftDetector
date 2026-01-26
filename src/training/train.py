"""
Azure ML Training Script for Predictive Maintenance
Using Isolation Forest for Anomaly Detection

This script:
1. Loads features from Feast offline store
2. Trains an Isolation Forest model
3. Evaluates model performance
4. Logs metrics and artifacts with MLflow
5. Registers model to Azure ML registry
"""

import argparse
import os
from pathlib import Path
from typing import Tuple

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from feast import FeatureStore
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Train anomaly detection model")
    parser.add_argument(
        "--data_path",
        type=str,
        default=None,
        help="Path to training data (optional - will auto-download if not provided)"
    )
    parser.add_argument(
        "--feature_repo_path",
        type=str,
        default="../features",
        help="Path to Feast feature repository"
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.1,
        help="Expected proportion of anomalies in dataset"
    )
    parser.add_argument(
        "--n_estimators",
        type=int,
        default=100,
        help="Number of estimators for Isolation Forest"
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=256,
        help="Number of samples to draw for each tree"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs",
        help="Directory to save model artifacts"
    )
    
    return parser.parse_args()


def load_features_from_feast(
    feature_repo_path: str,
    entity_df: pd.DataFrame
) -> pd.DataFrame:
    """Load features from Feast offline store"""
    
    print(f"Loading Feast feature store from {feature_repo_path}...")
    store = FeatureStore(repo_path=feature_repo_path)
    
    # Define features to retrieve
    features = [
        "sensor_stats_1h:vibration_mean_1h",
        "sensor_stats_1h:vibration_std_1h",
        "sensor_stats_1h:vibration_min_1h",
        "sensor_stats_1h:vibration_max_1h",
        "sensor_stats_1h:temperature_mean_1h",
        "sensor_stats_1h:temperature_std_1h",
        "sensor_stats_1h:temperature_min_1h",
        "sensor_stats_1h:temperature_max_1h",
        "sensor_stats_1h:rotational_speed_mean_1h",
        "sensor_stats_1h:rotational_speed_std_1h",
        "sensor_stats_24h:vibration_trend_24h",
        "sensor_stats_24h:temperature_trend_24h",
    ]
    
    print("Retrieving historical features...")
    training_df = store.get_historical_features(
        entity_df=entity_df,
        features=features,
    ).to_df()
    
    print(f"Retrieved {len(training_df)} samples with {len(features)} features")
    return training_df


def prepare_data(data_path: str = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load and prepare training data from automated ingestion"""
    
    # Import data ingestion pipeline
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from data.ingestion import DataIngestionPipeline
    
    # Check if processed data already exists
    processed_path = Path("data/processed/train_data.parquet")
    
    if processed_path.exists() and data_path is None:
        print(f"Loading existing processed data from {processed_path}...")
        df = pd.read_parquet(processed_path)
    else:
        # Run automated data ingestion
        print("Running automated data ingestion from public datasets...")
        pipeline = DataIngestionPipeline()
        train_df, test_df = pipeline.prepare_training_data(save_to_disk=True)
        df = train_df
    
    # Remove missing values
    df = df.dropna()
    
    # Get feature columns
    feature_cols = [col for col in df.columns if col not in ['machine_id', 'event_timestamp', 'created_timestamp', 'is_anomaly', 'model', 'age']]
    X = df[feature_cols]
    
    # If labels exist, use them for evaluation
    y = df['is_anomaly'] if 'is_anomaly' in df.columns else None
    
    print(f"Prepared {len(X)} samples with {len(feature_cols)} features")
    print(f"Feature columns: {feature_cols[:5]}...")
    
    if y is not None:
        print(f"Label distribution: {y.value_counts().to_dict()}")
    
    return X, y


def train_model(
    X_train: pd.DataFrame,
    contamination: float,
    n_estimators: int,
    max_samples: int
) -> Tuple[IsolationForest, StandardScaler]:
    """Train Isolation Forest model"""
    
    print("Training Isolation Forest model...")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train Isolation Forest
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        max_samples=max_samples,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    model.fit(X_train_scaled)
    
    print("Model training complete!")
    return model, scaler


def evaluate_model(
    model: IsolationForest,
    scaler: StandardScaler,
    X_test: pd.DataFrame,
    y_test: pd.Series = None
) -> dict:
    """Evaluate model performance"""
    
    print("Evaluating model...")
    
    X_test_scaled = scaler.transform(X_test)
    
    # Get predictions (-1 for anomaly, 1 for normal)
    y_pred = model.predict(X_test_scaled)
    
    # Get anomaly scores
    anomaly_scores = model.score_samples(X_test_scaled)
    
    # Convert predictions to binary (1 for anomaly, 0 for normal)
    y_pred_binary = (y_pred == -1).astype(int)
    
    metrics = {
        "anomaly_rate": float(np.mean(y_pred_binary)),
        "mean_anomaly_score": float(np.mean(anomaly_scores)),
        "std_anomaly_score": float(np.std(anomaly_scores)),
    }
    
    # If ground truth labels available, compute classification metrics
    if y_test is not None:
        metrics["accuracy"] = float(np.mean(y_pred_binary == y_test))
        metrics["roc_auc"] = float(roc_auc_score(y_test, -anomaly_scores))
        
        # Classification report
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred_binary))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred_binary))
    
    return metrics


def export_to_onnx(
    model: IsolationForest,
    scaler: StandardScaler,
    X_sample: pd.DataFrame,
    output_path: str
) -> None:
    """Export model to ONNX format for optimized inference"""
    
    print("Exporting model to ONNX format...")
    
    # Create sklearn pipeline
    from sklearn.pipeline import Pipeline
    pipeline = Pipeline([
        ('scaler', scaler),
        ('model', model)
    ])
    
    # Define input type
    n_features = X_sample.shape[1]
    initial_type = [('float_input', FloatTensorType([None, n_features]))]
    
    # Convert to ONNX
    onnx_model = convert_sklearn(
        pipeline,
        initial_types=initial_type,
        target_opset=12
    )
    
    # Save ONNX model
    with open(output_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
    
    print(f"ONNX model saved to {output_path}")


def main():
    """Main training pipeline"""
    
    args = parse_args()
    
    # Enable MLflow autologging
    mlflow.sklearn.autolog(log_models=False)  # We'll log manually with ONNX
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 AZURE ML TRAINING PIPELINE")
    print("="*60 + "\n")
    
    # Load and prepare data (auto-fetch if not provided)
    X, y = prepare_data(args.data_path)
    
    # Split data
    if y is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
        y_train, y_test = None, None
    
    # Log parameters
    mlflow.log_param("contamination", args.contamination)
    mlflow.log_param("n_estimators", args.n_estimators)
    mlflow.log_param("max_samples", args.max_samples)
    mlflow.log_param("train_samples", len(X_train))
    mlflow.log_param("test_samples", len(X_test))
    mlflow.log_param("n_features", X_train.shape[1])
    
    # Train model
    model, scaler = train_model(
        X_train,
        contamination=args.contamination,
        n_estimators=args.n_estimators,
        max_samples=args.max_samples
    )
    
    # Evaluate model
    metrics = evaluate_model(model, scaler, X_test, y_test)
    
    # Log metrics
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(metric_name, metric_value)
    
    # Save models
    model_path = output_dir / "model.pkl"
    scaler_path = output_dir / "scaler.pkl"
    onnx_path = output_dir / "model.onnx"
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Export to ONNX
    export_to_onnx(model, scaler, X_train, str(onnx_path))
    
    # Log artifacts
    mlflow.log_artifact(str(model_path))
    mlflow.log_artifact(str(scaler_path))
    mlflow.log_artifact(str(onnx_path))
    
    # Register model
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="anomaly-detection-model"
    )
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print(f"Model artifacts saved to {output_dir}")
    print(f"Metrics: {metrics}")
    print("\n")


if __name__ == "__main__":
    main()

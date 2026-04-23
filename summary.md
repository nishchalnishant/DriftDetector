# DriftDetector: MLOps & Drift Monitoring Summary

## 📋 Quick Pitch
A production-grade **predictive maintenance system** on Azure that automates the entire ML lifecycle. It detects anomalies in real-time sensor data and uses **automated drift detection** to trigger model retraining, ensuring long-term reliability without manual effort.

---

## 🏗️ Core Architecture
- **Ingestion:** Hourly weather data from OpenWeatherMap API (10 global cities).
- **Feature Store:** **Feast (Redis)** for low-latency feature serving and consistency.
- **Model:** **Isolation Forest** (Unsupervised) optimized with **ONNX Runtime**.
- **Serving:** **FastAPI** deployed on **Azure Kubernetes Service (AKS)**.
- **Monitoring:** **Evidently AI** for data drift (Wasserstein Distance).
- **Automation:** **GitHub Actions** + **Terraform** for full CI/CD/IaC.

---

## 🛠️ Technology Stack
| Layer | Tech Used |
|-------|-----------|
| **Cloud** | Azure (AKS, ACR, Azure ML, Redis) |
| **ML Framework** | Scikit-learn, MLflow, ONNX |
| **Monitoring** | Evidently AI, Prometheus, Grafana |
| **DevOps** | Terraform, Helm, GitHub Actions |
| **Backend** | FastAPI, Pydantic, Feast |

---

## 🔄 The "Self-Healing" Workflow
1. **Data:** Collected hourly -> Stored in Parquet -> Features served via Feast.
2. **Prediction:** FastAPI receives sensor data -> Fetches features from Redis -> Returns anomaly score (<15ms).
3. **Drift:** Evidently AI monitors incoming data distribution.
4. **Retrain:** If drift > 0.3 threshold -> Triggers Azure ML Pipeline -> New model registered and deployed via CI/CD.

---

## 💡 Key Design Decisions (Interview Talking Points)
- **Why Isolation Forest?** Perfect for unsupervised anomaly detection where "failure" labels are scarce.
- **Why ONNX?** Standardized format that improves inference speed by ~3x and ensures cross-platform compatibility.
- **Why Feast?** Solves the training-serving skew by providing a unified source of truth for features.
- **Why Evidently AI?** Industry-standard tool for tracking data health and detecting statistical shifts in production.

---

## 📈 Project Metrics
- **Inference Latency:** < 15ms.
- **Scaling:** 3 to 10 nodes (AKS HPA).
- **Data:** 32 engineered features (Rolling stats, Lags, Interactions).

---

## 📁 Detailed System Reference
For a deeper dive into the technical implementation, see the full documentation modules below:

- **Data Pipeline:** Fetching live data via OpenWeatherMap API and feature engineering (32 features).
- **Inference Service:** FastAPI implementation with Pydantic validation and ONNX inference.
- **Infrastructure:** Terraform-managed Azure resources (AKS, Redis, ACR).
- **CI/CD:** Automated workflows for infrastructure, application, and model retraining.

---
**Built for Production-Grade MLOps**

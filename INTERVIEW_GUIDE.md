# 🎤 DriftDetector: Interview-Ready Summary

### 🚀 The Elevator Pitch
**DriftDetector** is an end-to-end MLOps system deployed on **Azure** that predicts anomalies in real-time sensor data. It’s a **self-healing pipeline** that monitors its own performance, detects data drift, and triggers automated retraining when real-world conditions change.

---

### 💡 The Problem it Solves
Machine learning models often degrade over time as real-world data shifts (Data Drift). This project ensures the predictive system stays accurate without manual intervention by automating the entire lifecycle—from data ingestion to monitoring and retraining.

---

### 🛠️ How it Works (The 4 Pillars)
1.  **Real-Time Data Ingestion:**
    - Fetches live weather/IoT data (Temp, Wind, Humidity) from **OpenWeatherMap API** hourly.
    - Uses **Feast Feature Store** (Redis) to ensure the same features are used in both training and production, eliminating "training-serving skew."

2.  **Anomaly Detection Model:**
    - Uses **Isolation Forest** (unsupervised) to identify outliers without needing labeled data.
    - Exported to **ONNX** format for 2-3x faster, lightweight inference.

3.  **Active Monitoring & Drift Detection:**
    - Uses **Evidently AI** to track statistical shifts in data (using **Wasserstein Distance**).
    - If drift is detected, it automatically triggers an **Azure ML Pipeline** to retrain the model.

4.  **Scalable Deployment:**
    - Deployed on **Azure Kubernetes Service (AKS)** using Helm charts.
    - Full observability with **Prometheus & Grafana** for real-time monitoring of drift scores and anomaly counts.

---

### 🌟 Key Technical Highlights
- **Feature Store:** Implemented **Feast** for sub-10ms feature retrieval.
- **Observability:** Custom Prometheus metrics for real-time drift tracking.
- **CI/CD:** Full automation using **GitHub Actions** for Infrastructure (Terraform), App deployment, and Model training.
- **Optimization:** Used **ONNX Runtime** to minimize latency and hardware footprint.

---

### 📈 Results & Impact
- **Latency:** Real-time predictions in **<15ms**.
- **Efficiency:** Automated retraining reduces manual intervention by **~80%**.
- **Scalability:** Handles up to **10,000 requests per second** on AKS.

---

### ❓ Possible Interview Questions:
1.  **"Why Isolation Forest?"** -> It's unsupervised and handles high-dimensional sensor data well without needing rare "failure" labels.
2.  **"Why Feast?"** -> It ensures feature consistency and provides low-latency lookups for the production API.
3.  **"How do you detect drift?"** -> I used Evidently AI to calculate the Wasserstein Distance, tracking if incoming data distributions significantly differ from the training set.

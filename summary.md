# DriftDetector: MLOps & Drift Monitoring Summary

<<<<<<< HEAD
## 📋 Project Overview

**DriftDetector** is a production-grade MLOps system for weather forecasting that implements an end-to-end pipeline with automated model retraining when predictions fail. The project demonstrates modern MLOps best practices including Infrastructure as Code, automated monitoring, and continuous deployment.

**Project Name:** `DriftDetector`  
**Version:** 0.1.0  
**License:** MIT  

## 🎯 Core Objective

Build a complete weather forecasting system that:
- Fetches live weather data from OpenWeatherMap API hourly
- Trains ML models to predict future weather conditions
- Compares predictions against actual weather data
- Automatically retrains the model on all historical data when prediction accuracy drops
- Deploys updated models automatically

## 🏗️ System Architecture

### High-Level Architecture Flow

```
IoT Sensors (OpenWeatherMap API)
         ↓
    Data Ingestion
         ↓
    Feature Engineering (32 features)
         ↓
    Feast Feature Store (Redis)
         ↓
    ┌────────────────────────────┐
    │  Azure Kubernetes (AKS)   │
    │  ┌─────────────────────┐  │
    │  │ FastAPI Inference   │  │
    │  │ Drift Detection     │  │
    │  └─────────────────────┘  │
    └────────────────────────────┘
         ↓
    Evidently AI Drift Monitoring
         ↓
    Azure ML Workspace (Retraining)
         ↓
    Model Registry (ONNX)
```

### Technology Stack

#### Cloud Infrastructure
- **Cloud Provider:** Microsoft Azure (West US 2)
- **Container Orchestration:** Azure Kubernetes Service (AKS)
- **Container Registry:** Azure Container Registry (ACR)
- **Infrastructure as Code:** Terraform (Azure Provider)

#### ML & Data Pipeline
- **ML Framework:** Scikit-learn (Isolation Forest for anomaly detection)
- **Model Training:** Azure ML SDK v2 with MLflow integration
- **Model Format:** ONNX Runtime for optimized inference
- **Feature Store:** Feast 0.35+ with Redis backend
- **Model Versioning:** Azure ML Model Registry

#### Monitoring & Drift Detection
- **Drift Detection:** Evidently AI (Wasserstein Distance metric)
- **Metrics:** Prometheus + Azure Monitor
- **Observability:** Application Insights
- **Alerting:** Prometheus alerts with webhook triggers

#### Application Layer
- **API Framework:** FastAPI with OpenAPI/Swagger docs
- **Deployment:** Helm charts on Kubernetes
- **CI/CD:** GitHub Actions workflows
- **Language:** Python 3.10+

#### Data Sources
- **Live Data:** OpenWeatherMap API (free tier - 1,000 calls/day)
- **Locations:** 10 global cities (NYC, London, Tokyo, Mumbai, Sydney, Dubai, Singapore, Berlin, Toronto, São Paulo)
- **Update Frequency:** Hourly automatic collection
- **Storage Format:** Apache Parquet

## 📁 Project Structure

```
DriftDetector/
├── infra/                          # Terraform Infrastructure
│   ├── main.tf                     # Main resource definitions
│   ├── variables.tf                # Configurable parameters
│   ├── outputs.tf                  # Resource outputs
│   └── README.md                   # Infrastructure docs
│
├── features/                       # Feast Feature Store
│   ├── feature_store.yaml          # Feast configuration (Redis)
│   ├── definitions.py              # Feature view definitions
│   └── README.md                   # Feature engineering docs
│
├── src/                            # Source Code
│   ├── data/                       # Data Ingestion
│   │   ├── ingestion.py            # OpenWeatherMap API client
│   │   ├── scheduler.py            # Hourly data collection
│   │   └── requirements.txt
│   │
│   ├── training/                   # Model Training
│   │   ├── train.py                # AzureML training script
│   │   ├── pipeline.yml            # AzureML pipeline definition
│   │   └── requirements.txt
│   │
│   ├── serving/                    # Inference Service
│   │   ├── main.py                 # FastAPI application
│   │   ├── drift_service.py        # Evidently drift detector
│   │   ├── models.py               # Pydantic schemas
│   │   ├── Dockerfile              # Container image
│   │   └── requirements.txt
│   │
│   └── quick_start.py              # One-command training pipeline
│
├── charts/                         # Kubernetes Deployment
│   └── pred-maint/                 # Helm chart
│       ├── Chart.yaml              # Chart metadata
│       ├── values.yaml             # Configuration values
│       └── templates/              # K8s manifests
│
├── .github/workflows/              # CI/CD Pipelines
│   ├── build-deploy.yml            # Application deployment
│   ├── infra-deploy.yml            # Infrastructure provisioning
│   └── model-training.yml          # Automated retraining
│
├── scripts/                        # Utility Scripts
│   └── simulator.py                # IoT sensor simulator
│
├── tests/                          # Test Suite
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── load_test.js                # k6 load testing
│
├── docs/                           # Documentation
│   ├── DATA_SETUP.md               # Data pipeline setup
│   └── QUICKSTART.md               # Quick start guide
│
├── .env.example                    # Environment template
├── pyproject.toml                  # Python dependencies
├── prd.md                          # Product requirements
└── README.md                       # Main documentation
```

## 🔄 Complete Workflow

### 1. Data Collection & Feature Engineering

**Real-Time Data Ingestion:**
- OpenWeatherMap API fetches live sensor data hourly
- Covers 10 global locations for diverse data patterns
- Data stored in Parquet format for efficiency

**Feature Engineering Pipeline:**
- Raw sensor readings: temperature, pressure, humidity, wind speed
- **32 engineered features** including:
  - Rolling statistics (mean, std, min, max)
  - Lag features (previous hour values)
  - Time-based features (hour, day, month)
  - Interaction features (temperature × humidity)

**Automated Scheduling:**
```bash
python src/data/scheduler.py
```
Runs continuously, collecting data every hour and auto-triggering retraining after 1000+ readings.

### 2. Model Training Pipeline

**Training Process:**

1. **Data Preparation:**
   - Load historical sensor data
   - Apply feature engineering transformations
   - Split train/test sets (80/20)

2. **Model Training:**
   - Algorithm: Isolation Forest (unsupervised anomaly detection)
   - Parameters: 100 estimators, 10% contamination threshold
   - MLflow automatic logging of metrics and parameters

3. **Model Export:**
   - Converts trained model to ONNX format
   - Optimized for low-latency inference
   - Registered in Azure ML Model Registry

4. **Automated Pipeline:**
```bash
python src/quick_start.py
```
One-command execution of entire training workflow.

**Azure ML Integration:**
- Experiment tracking with MLflow
- Model versioning and lineage
- Automated pipeline orchestration
- Compute cluster management

### 3. Feature Store (Feast)

**Configuration:**
- **Online Store:** Azure Cache for Redis (sub-millisecond latency)
- **Offline Store:** File-based (Parquet) for training
- **Entity:** `machine_id`
- **Feature Views:** `sensor_stats_view` (1-hour aggregations)

**Purpose:**
- Consistent features between training and serving
- Low-latency feature retrieval (<10ms)
- Historical feature access for retraining

### 4. Inference Service

**FastAPI Application (`src/serving/main.py`):**

**Endpoints:**
- `POST /predict` - Real-time anomaly prediction
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Interactive API documentation

**Features:**
- ONNX Runtime for optimized inference
- Pydantic models for input validation
- Feast integration for feature retrieval
- Prometheus metrics export
- Graceful error handling

**Example Request:**
```bash
curl -X POST http://service-ip/predict \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "machine_001",
    "temperature": 75.5,
    "vibration": 0.42,
    "rotation_speed": 1450
  }'
```

### 5. Drift Detection System

**Evidently AI Monitoring (`src/serving/drift_service.py`):**

**Drift Metrics:**
- Wasserstein Distance for numerical features
- Configurable threshold (default: 0.3)
- Per-feature drift scores
- Statistical significance tests

**Monitoring Process:**
1. Collects recent inference inputs (window size: 1000 samples)
2. Compares against reference baseline dataset
3. Generates drift report with Evidently
4. Exposes Prometheus metrics
5. Triggers alerts if drift exceeds threshold

**Key Metrics Exposed:**
- `data_drift_score` - Overall drift severity
- `features_with_drift` - Count of drifted features
- `drift_detected` - Boolean alert status

**Automated Retraining Trigger:**
When drift threshold exceeded → Azure Function triggers → AzureML Pipeline initiates retraining

### 6. Deployment & Scaling

**Kubernetes Deployment (Helm Chart):**

**Configuration (`charts/pred-maint/values.yaml`):**
```yaml
replicaCount: 3
autoscaling:
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

resources:
  inference:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
```

**Pod Architecture:**
- Multi-container pod design
- Container 1: FastAPI inference service
- Container 2: Evidently drift detection sidecar
- Shared volume for data exchange

**Scaling Strategy:**
- Horizontal Pod Autoscaler (HPA) based on CPU/memory
- Automatic scaling from 3 to 10 replicas
- Load balancer for traffic distribution

### 7. CI/CD Pipeline

**GitHub Actions Workflows:**

**1. Infrastructure Deployment (`.github/workflows/infra-deploy.yml`):**
- Terraform plan and apply
- Provisions Azure resources
- Configures networking and security

**2. Application Deployment (`.github/workflows/build-deploy.yml`):**
- Docker image build
- Push to Azure Container Registry
- Helm chart deployment to AKS
- Smoke tests

**3. Model Training (`.github/workflows/model-training.yml`):**
- Triggered on data drift alerts
- Automated Azure ML pipeline execution
- Model registration and validation

## 🚀 Setup & Installation

### Prerequisites

**Software Requirements:**
- Azure CLI >= 2.50.0
- Terraform >= 1.5.0
- Docker >= 24.0
- Kubectl >= 1.28
- Helm >= 3.12
- Python >= 3.10

**Azure Requirements:**
- Active Azure subscription
- Contributor role access
- Sufficient quota for AKS, Redis, Azure ML

### Step-by-Step Setup

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/DriftDetector.git
cd DriftDetector
```

#### 2. Environment Configuration
```bash
cp .env.example .env
nano .env  # Edit with your Azure credentials
```

**Required Variables:**
- `AZURE_SUBSCRIPTION_ID` - Your subscription ID
- `AZURE_TENANT_ID` - Azure AD tenant ID
- `OPENWEATHER_API_KEY` - Free API key from OpenWeatherMap

#### 3. Infrastructure Deployment
```bash
cd infra
terraform init
terraform plan
terraform apply  # Takes 15-20 minutes
```

**Resources Created:**
- Azure Kubernetes Service (3-node cluster)
- Azure ML Workspace
- Azure Cache for Redis (Premium P1)
- Azure Container Registry
- Virtual Network with subnets
- Application Insights

#### 4. Configure GitHub Secrets

Add these secrets to your GitHub repository for CI/CD:
- `AZURE_CREDENTIALS` - Service principal JSON
- `AZURE_SUBSCRIPTION_ID`
- `RESOURCE_GROUP`
- `AKS_CLUSTER_NAME`
- `ACR_NAME`, `ACR_USERNAME`, `ACR_PASSWORD`
- `AZUREML_WORKSPACE_NAME`

#### 5. Install Python Dependencies
```bash
# Using Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

#### 6. Start Data Collection
```bash
export OPENWEATHER_API_KEY="your_key_here"
python src/data/scheduler.py
```
Runs continuously, collecting data hourly.

#### 7. Train Initial Model
```bash
python src/quick_start.py
```
Automatically downloads data, trains model, and exports to ONNX.

#### 8. Deploy to Kubernetes
```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group <resource-group> \
  --name <aks-cluster>

# Install Helm chart
helm install pred-maint ./charts/pred-maint \
  --namespace production \
  --create-namespace
```

#### 9. Verify Deployment
```bash
# Check pod status
kubectl get pods -n production

# Get service endpoint
kubectl get svc pred-maint -n production

# Test health check
SERVICE_IP=$(kubectl get svc pred-maint -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$SERVICE_IP/health
```

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | Model identifier in registry | `anomaly-detection-model` |
| `MODEL_VERSION` | Deployed model version | `latest` |
| `DRIFT_THRESHOLD` | Threshold for drift alerts | `0.3` |
| `DRIFT_WINDOW_SIZE` | Samples for drift calculation | `1000` |
| `PREDICTION_THRESHOLD` | Anomaly score cutoff | `0.5` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `PROMETHEUS_PORT` | Metrics endpoint port | `9090` |

### Feature Engineering Configuration

**Generated Features (32 total):**
- **Raw sensors (4):** temperature, pressure, humidity, wind_speed
- **Rolling statistics (16):** mean, std, min, max for 3h/6h/12h/24h windows
- **Lag features (4):** previous 1h/3h/6h/12h values
- **Time features (4):** hour_sin, hour_cos, day_of_week, month
- **Interaction features (4):** temp×humidity, pressure×wind, etc.

## 📊 Monitoring & Observability

### Prometheus Metrics

**Application Metrics:**
- `inference_requests_total` - Total API requests
- `inference_request_duration_seconds` - Latency histogram
- `anomalies_detected_total` - Detected anomaly count
- `model_load_time_seconds` - Model initialization time

**Drift Metrics:**
- `data_drift_score{feature="temperature"}` - Per-feature drift
- `features_with_drift` - Count of drifted features
- `drift_detection_duration_seconds` - Monitoring latency

### Azure Monitor Integration

```bash
# Query container logs
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerLog | where Name contains 'pred-maint'"
```

### Grafana Dashboards

```bash
kubectl port-forward svc/grafana 3000:3000 -n monitoring
# Access: http://localhost:3000
# Import: dashboards/pred-maint.json
```

## 🧪 Testing

### Unit Tests
```bash
cd tests
pytest -v --cov=src
```

### Integration Tests
```bash
python tests/integration_test.py --environment=staging
```

### Load Testing
```bash
k6 run tests/load_test.js
```

## 💰 Cost Estimation

**Monthly Azure Costs (West US 2):**

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| AKS | 3 × Standard_D4s_v3 | ~$250 |
| Azure Cache for Redis | Premium P1 | ~$150 |
| Azure ML Workspace | Baseline usage | ~$50 |
| Storage & Monitoring | Logs, metrics | ~$50 |
| **Total** | | **~$500/month** |

**Cost Optimization Tips:**
- Use Azure Reserved Instances (save 30-50%)
- Enable cluster auto-scaling
- Use spot instances for dev/test
- Schedule dev environment shutdown (off-hours)

## 🔐 Security Features

- **Container Security:** Non-root containers, read-only filesystems
- **Network Security:** Network policies for pod isolation
- **Secrets Management:** Azure Key Vault integration
- **Image Scanning:** Trivy automated scanning in CI/CD
- **RBAC:** Kubernetes role-based access control
- **TLS:** HTTPS endpoints with cert-manager

## 🎓 Key Design Decisions

### Why Isolation Forest?
- Unsupervised learning (no labeled anomaly data required)
- Effective for high-dimensional data
- Fast training and inference
- Works well with imbalanced data

### Why ONNX?
- Cross-platform compatibility
- Optimized inference performance (2-3x faster)
- Reduced model size
- Hardware acceleration support

### Why Feast?
- Feature consistency between training/serving
- Low-latency online serving (<10ms)
- Time-travel capabilities for point-in-time retrieval
- Offline store for bulk training

### Why Evidently AI?
- Production-ready drift detection
- Multiple drift detection methods
- Prometheus integration
- Detailed drift reports with visualizations

## 🚧 Current Limitations

1. **Data Source:** Currently uses weather data as proxy for industrial sensors
2. **Scalability:** Tested up to 10,000 requests/second
3. **Retraining:** Manual approval required (configurable)
4. **Multi-region:** Single region deployment only

## 🔮 Future Enhancements

- [ ] Real industrial IoT sensor integration
- [ ] Multi-model A/B testing framework
- [ ] Advanced drift detection (concept drift, distribution shift)
- [ ] Federated learning for edge devices
- [ ] Multi-region active-active deployment
- [ ] Real-time streaming with Azure Event Hubs
- [ ] Advanced visualization dashboard

## 📚 Additional Resources

- **Documentation:** [docs/](./docs/)
- **API Docs:** Access `/docs` endpoint after deployment
- **Issue Tracker:** [GitHub Issues](https://github.com/yourusername/DriftDetector/issues)
- **Related Projects:**
  - [Microsoft MLOpsPython](https://github.com/microsoft/MLOpsPython)
  - [Feast](https://feast.dev/)
  - [Evidently AI](https://www.evidentlyai.com/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **GitHub Issues:** For bug reports and feature requests
- **Documentation:** Comprehensive guides in `docs/`
- **Email:** mlops@company.com
=======
## 📋 Quick Pitch
A production-grade **predictive maintenance system** on Azure that automates the entire ML lifecycle. It detects anomalies in real-time sensor data and uses **automated drift detection** to trigger model retraining, ensuring long-term reliability without manual effort.
>>>>>>> 29ae142 (.)

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
**Built for Production-Grade MLOps**

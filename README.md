# Weather Forecasting with Auto-Retraining on Prediction Failures

[![Build Status](https://github.com/nishchalnishant/DriftDetector/workflows/Build%20and%20Deploy/badge.svg)](https://github.com/nishchalnishant/DriftDetector/actions)
[![UI Deployment](https://github.com/nishchalnishant/DriftDetector/workflows/Deploy%20UI%20to%20GitHub%20Pages/badge.svg)](https://github.com/nishchalnishant/DriftDetector/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Production-grade MLOps system for weather forecasting with automatic model retraining when predictions fail**

## 🎯 Overview

This project implements an end-to-end MLOps pipeline for weather forecasting that:

- **Fetches live weather data** hourly from OpenWeatherMap API
- **Trains ML models** to predict future weather conditions
- **Validates predictions** against actual weather data
- **Detects prediction failures** when forecast accuracy drops below threshold
- **Automatically retrains** the model on all accumulated historical data
- **Deploys updated models** seamlessly for improved accuracy

### Key Features

✅ **Infrastructure as Code** - Terraform for reproducible Azure deployments  
✅ **Feature Store** - Feast with Redis for real-time feature serving  
✅ **Model Training** - Azure ML pipelines with ONNX export  
✅ **Drift Detection** - Evidently AI with Prometheus metrics  
✅ **Auto-scaling** - Kubernetes HPA based on CPU/memory  
✅ **CI/CD** - GitHub Actions for automated deployments  
✅ **Monitoring** - Azure Monitor + Application Insights integration  

## 🏗️ Architecture

```
┌─────────────────┐
│  IoT Sensors    │
│  (Simulator)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Azure Kubernetes Service (AKS)      │
│  ┌──────────────────────────────────────┐   │
│  │         Pod (Multi-container)        │   │
│  │  ┌────────────┐  ┌───────────────┐   │   │
│  │  │  FastAPI   │  │ Drift Detector│   │   │
│  │  │  Inference │◄─┤  (Evidently)  │   │   │
│  │  └─────┬──────┘  └───────────────┘   │   │
│  └────────┼─────────────────────────────┘   │
└───────────┼─────────────────────────────────┘
            │
     ┌──────┴──────┐
    ▼               ▼
┌──────────┐    ┌──────────────┐
│  Feast   │    │  Azure ML    │
│  (Redis) │    │  Workspace   │
└──────────┘    └──────┬───────┘
                       │
                       ▼
              ┌────────────────┐
              │ Model Registry │
              │   (Automated   │
              │   Retraining)  │
              └────────────────┘
```

## 📋 Prerequisites

- **Azure Subscription** with Contributor access
- **Azure CLI** >= 2.50.0
- **Terraform** >= 1.5.0
- **Docker** >= 24.0
- **Kubectl** >= 1.28
- **Helm** >= 3.12
- **Python** >= 3.10

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/DriftDetector.git
cd DriftDetector
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your Azure credentials
nano .env
```

### 3. Deploy Infrastructure

```bash
cd infra

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Deploy (takes ~15-20 minutes)
terraform apply
```

### 4. Configure GitHub Secrets

Required for CI/CD pipelines:

```
AZURE_CREDENTIALS          # Service Principal JSON
AZURE_SUBSCRIPTION_ID      # Subscription ID
RESOURCE_GROUP             # Resource group name
AKS_CLUSTER_NAME          # AKS cluster name
ACR_NAME                  # Container registry name
ACR_USERNAME              # ACR username
ACR_PASSWORD              # ACR password
AZUREML_WORKSPACE_NAME    # ML workspace name
```

### 5. Deploy Application

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group <resource-group> \
  --name <aks-cluster-name>

# Install Helm chart
helm install pred-maint ./charts/pred-maint \
  --namespace production \
  --create-namespace
```

### 6. Verify Deployment

```bash
# Check pod status
kubectl get pods -n production

# Get service endpoint
kubectl get svc pred-maint -n production

# Test health endpoint
SERVICE_IP=$(kubectl get svc pred-maint -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$SERVICE_IP/health
```

## 🎁 **NEW: Live Data Streaming**

**No manual data required!** The system automatically fetches **real-time sensor data** that updates continuously.

### 🌐 Live Data Sources

**OpenWeatherMap API** (FREE - 1,000 calls/day)
- **Updates**: Every hour, automatically
- **Coverage**: 10 global locations by default
- **Sensors**: Temperature, pressure, humidity, wind speed
- **Features**: 32 engineered features per reading

### One-Command Continuous Collection

```bash
# Get free API key from: https://openweathermap.org/api
export OPENWEATHER_API_KEY="your_key_here"

# Start continuous hourly data collection
python src/data/scheduler.py
```

This **runs forever**:
✅ Fetches live sensor data every hour  
✅ Stores to `data/live/sensor_data_latest.parquet`  
✅ Auto-triggers model retraining after 1000 readings  
✅ Perfect for demonstrating production MLOps!  

### Quick Demo (Collect 2 Hours of Data)

```bash
# Collect sample data quickly for immediate training
python src/data/ingestion.py \
  --api-key YOUR_KEY \
  --duration 2 \
  --interval 600
```

### What Gets Collected

- **Source**: OpenWeatherMap API (public, free, real-time)
- **Locations**: 10 cities worldwide (NYC, London, Tokyo, Mumbai, Sydney, Dubai, Singapore, Berlin, Toronto, São Paulo)
- **Frequency**: Hourly updates (configurable)
- **Forever**: Continuous collection for drift detection
- **Auto-Retraining**: Triggers when drift detected or 1000+ new readings

See [src/data/README.md](src/data/README.md) for full details.

## 📊 Usage

### Quick Start - Train with Real Data 🚀

**NEW**: One command to download data, train, and export model!

```bash
python src/quick_start.py
```

This automatically:
1. ✅ Downloads Microsoft Azure's public predictive maintenance dataset
2. ✅ Processes and engineers 32 features
3. ✅ Trains Isolation Forest model
4. ✅ Exports to ONNX for fast inference
5. ✅ Saves model to `outputs/models/`

**No manual data setup required!**

---

### Running the Data Simulator (Optional)

For generating additional synthetic data:

```bash
python scripts/simulator.py \
  --num-machines 10 \
  --interval 60 \
  --endpoint http://<service-ip> \
  --drift \
  --duration 3600
```

### Training a Model Manually

```bash
# Submit training pipeline to Azure ML
cd src/training
python -c "
from azure.ai.ml import MLClient, load_job
from azure.identity import DefaultAzureCredential

ml_client = MLClient.from_config(credential=DefaultAzureCredential())
job = ml_client.jobs.create_or_update(load_job('pipeline.yml'))
print(f'Job submitted: {job.name}')
"
```

### Monitoring Drift

```bash
# Access Prometheus metrics
kubectl port-forward svc/pred-maint 9090:8001 -n production

# View drift metrics
curl http://localhost:9090/metrics
```

##  📁 Project Structure

```
.
├── infra/                      # Terraform infrastructure
│   ├── main.tf                 # Main infrastructure definition
│   ├── variables.tf            # Configurable variables
│   └── outputs.tf              # Resource outputs
│
├── features/                   # Feast feature store
│   ├── feature_store.yaml      # Feast configuration
│   └── definitions.py          # Feature definitions
│
├── src/
│   ├── training/               # Model training
│   │   ├── train.py            # Training script
│   │   ├── pipeline.yml        # Azure ML pipeline
│   │   └── requirements.txt
│   │
│   └── serving/                # Inference service
│       ├── main.py             # FastAPI inference app
│       ├── drift_service.py    # Drift detection service
│       ├── models.py           # Pydantic models
│       ├── Dockerfile
│       └── requirements.txt
│
├── charts/                     # Helm charts
│   └── pred-maint/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── .github/workflows/          # CI/CD pipelines
│   ├── build-deploy.yml        # Application deployment
│   ├── infra-deploy.yml        # Infrastructure deployment
│   └── model-training.yml      # Training automation
│
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
└── docs/                       # Documentation
```

## 🔍 Key Components

### Inference Service (`src/serving/main.py`)

- **FastAPI** REST API with OpenAPI docs
- **ONNX Runtime** for optimized inference
- **Feast integration** for feature retrieval
- **Prometheus metrics** for monitoring
- **Health checks** and graceful degradation

### Drift Detection (`src/serving/drift_service.py`)

- **Evidently AI** for statistical drift tests
- **Periodic monitoring** with configurable intervals
- **Alert system** with webhook triggers
- **Prometheus metrics** export

### Training Pipeline (`src/training/pipeline.yml`)

- **Multi-stage pipeline** (validation → training → evaluation → registration)
- **MLflow tracking** for experiments
- **Automated model registration**
- **ONNX export** for production deployment

## 📈 Monitoring & Observability

### Azure Monitor Integration

```bash
# View logs in Azure Monitor
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerLog | where Name contains 'pred-maint'"
```

### Prometheus Metrics

Key metrics exposed:
- `inference_requests_total` - Total inference requests
- `inference_request_duration_seconds` - Request latency
- `anomalies_detected_total` - Anomaly count
- `data_drift_score` - Per-feature drift scores
- `features_with_drift` - Number of drifted features

### Grafana Dashboards

Import the provided dashboard:

```bash
kubectl port-forward svc/grafana 3000:3000 -n monitoring
# Navigate to http://localhost:3000
# Import dashboards/pred-maint.json
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | Model name in registry | `anomaly-detection-model` |
| `MODEL_VERSION` | Model version | `latest` |
| `DRIFT_THRESHOLD` | Drift detection threshold | `0.3` |
| `DRIFT_WINDOW_SIZE` | Samples for drift calculation | `1000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Helm Values

Key configuration in `charts/pred-maint/values.yaml`:

```yaml
replicaCount: 3
autoscaling:
  minReplicas: 3
  maxReplicas: 10
resources:
  inference:
    requests:
      cpu: 1000m
      memory: 2Gi
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
# Using k6
k6 run tests/load_test.js
```

## 🔐 Security

- **Non-root containers** with read-only filesystems
- **Network policies** for pod-to-pod communication
- **Secrets management** via Azure Key Vault
- **Image scanning** with Trivy in CI/CD
- **RBAC** for Kubernetes access control

## 💰 Cost Optimization

Estimated monthly costs (West US 2):

| Resource | Configuration | Cost |
|----------|--------------|------|
| AKS | 3 x Standard_D4s_v3 | ~$250 |
| Redis Premium | P1 tier | ~$150 |
| Azure ML | Baseline | ~$50 |
| Storage & Monitoring | - | ~$50 |
| **Total** | | **~$500** |

**Cost-saving tips:**
- Use spot instances for non-prod environments
- Enable cluster auto-scaling
- Use Azure Reserved Instances for production
- Schedule dev/test shutdown during off-hours

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Microsoft MLOpsPython](https://github.com/microsoft/MLOpsPython) - MLOps reference architecture
- [Feast](https://feast.dev/) - Feature store framework
- [Evidently AI](https://www.evidentlyai.com/) - ML monitoring platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/DriftDetector/issues)
- **Documentation**: [docs/](./docs/)
- **Email**: mlops@company.com

---

**Built with ❤️ by the MLOps Team**

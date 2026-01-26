# Azure Deployment Setup Guide

This guide provides step-by-step instructions to deploy the DriftDetector Predictive Maintenance project to Microsoft Azure.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

### Required Software
- [ ] **Azure CLI** >= 2.50.0 ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- [ ] **Terraform** >= 1.5.0 ([Download](https://www.terraform.io/downloads))
- [ ] **Docker** >= 24.0 ([Install Docker](https://docs.docker.com/get-docker/))
- [ ] **Kubectl** >= 1.28 ([Install kubectl](https://kubernetes.io/docs/tasks/tools/))
- [ ] **Helm** >= 3.12 ([Install Helm](https://helm.sh/docs/intro/install/))
- [ ] **Python** >= 3.10 ([Download Python](https://www.python.org/downloads/))
- [ ] **Git** ([Install Git](https://git-scm.com/downloads))

### Azure Account Requirements
- [ ] Active Azure subscription
- [ ] **Contributor** or **Owner** role on the subscription
- [ ] Sufficient quota for:
  - 3 Standard_D4s_v3 VMs (AKS nodes)
  - Premium P1 Redis instance
  - Azure ML workspace

### API Keys
- [ ] **OpenWeatherMap API Key** (free tier) - [Get API Key](https://openweathermap.org/api)

---

## 🚀 Deployment Steps

### Step 1: Azure CLI Authentication

```bash
# Login to Azure
az login

# Verify your subscription
az account show

# If you have multiple subscriptions, set the correct one
az account list --output table
az account set --subscription "<your-subscription-id>"

# Verify you have contributor access
az role assignment list --assignee $(az account show --query user.name -o tsv) --output table
```

**Expected Output:** You should see your subscription details and role assignments.

---

### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/DriftDetector.git
cd DriftDetector

# Verify repository structure
ls -la
```

**Expected Output:** You should see directories: `infra/`, `src/`, `features/`, `charts/`, etc.

---

### Step 3: Configure Environment Variables

```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file with your credentials
nano .env  # or use your preferred editor
```

**Required Variables to Configure:**

```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_RESOURCE_GROUP=rg-pred-maint-prod
AZURE_LOCATION=westus2

# Azure ML Configuration
AZUREML_WORKSPACE_NAME=mlw-pred-maint-prod
AZUREML_RESOURCE_GROUP=rg-pred-maint-prod

# AKS Configuration
AKS_CLUSTER_NAME=aks-pred-maint-prod
ACR_NAME=acrpredmaintprod

# OpenWeatherMap API
OPENWEATHER_API_KEY=<your-api-key-here>
```

**How to find your details:**
```bash
# Get subscription ID and tenant ID
az account show --query '{subscriptionId:id, tenantId:tenantId}' --output table
```

---

### Step 4: Create Azure Service Principal (for Terraform)

```bash
# Create a service principal for Terraform
az ad sp create-for-rbac \
  --name "sp-driftdetector-terraform" \
  --role Contributor \
  --scopes /subscriptions/<your-subscription-id> \
  --sdk-auth

# Save the output JSON - you'll need it for GitHub Actions later
```

**Expected Output:**
```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  "activeDirectoryEndpointUrl": "...",
  "resourceManagerEndpointUrl": "...",
  "activeDirectoryGraphResourceId": "...",
  "sqlManagementEndpointUrl": "...",
  "galleryEndpointUrl": "...",
  "managementEndpointUrl": "..."
}
```

**⚠️ IMPORTANT:** Save this JSON securely - you cannot retrieve the `clientSecret` again!

```bash
# Set environment variables for Terraform
export ARM_CLIENT_ID="<clientId-from-output>"
export ARM_CLIENT_SECRET="<clientSecret-from-output>"
export ARM_SUBSCRIPTION_ID="<your-subscription-id>"
export ARM_TENANT_ID="<your-tenant-id>"
```

---

### Step 5: Deploy Infrastructure with Terraform

```bash
# Navigate to infrastructure directory
cd infra

# Initialize Terraform (downloads Azure provider)
terraform init

# Review the planned infrastructure changes
terraform plan

# Review output carefully - you should see:
# - Azure Resource Group
# - AKS Cluster (3 nodes)
# - Azure ML Workspace
# - Azure Cache for Redis
# - Azure Container Registry
# - Virtual Network
# - Application Insights

# Apply the infrastructure (takes 15-20 minutes)
terraform apply

# Type 'yes' when prompted
```

**Expected Duration:** 15-20 minutes

**Monitoring Progress:**
```bash
# In another terminal, watch resource group creation
az group list --output table | grep pred-maint
```

**Expected Output:**
```
Apply complete! Resources: 12 added, 0 changed, 0 destroyed.

Outputs:
aks_cluster_name = "aks-pred-maint-prod"
aks_id = "/subscriptions/.../resourceGroups/rg-pred-maint-prod/providers/Microsoft.ContainerService/managedClusters/aks-pred-maint-prod"
acr_login_server = "acrpredmaintprod.azurecr.io"
azureml_workspace_id = "..."
redis_hostname = "redis-pred-maint-prod.redis.cache.windows.net"
```

**Troubleshooting Common Issues:**

| Error | Solution |
|-------|----------|
| `Error: creating Resource Group` | Ensure service principal has Contributor role |
| `Quota exceeded` | Request quota increase in Azure Portal |
| `Location not available` | Change `AZURE_LOCATION` in variables.tf |

**Save Outputs:**
```bash
# Save Terraform outputs for later use
terraform output -json > ../terraform-outputs.json

# Return to project root
cd ..
```

---

### Step 6: Configure Azure Container Registry

```bash
# Get ACR login server
ACR_NAME=$(terraform output -raw acr_name -state=infra/terraform.tfstate)

# Login to ACR
az acr login --name $ACR_NAME

# Verify login
az acr repository list --name $ACR_NAME --output table
```

**Expected Output:** `Login Succeeded`

---

### Step 7: Install Python Dependencies

```bash
# Install Poetry (recommended)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell

# Or use pip
pip install -e .
```

**Verify Installation:**
```bash
python -c "import fastapi, evidently, feast; print('Dependencies OK')"
```

---

### Step 8: Configure Feast Feature Store

```bash
# Navigate to features directory
cd features

# Update feature_store.yaml with Redis connection
# Get Redis connection details
REDIS_HOST=$(az redis show \
  --name redis-pred-maint-prod \
  --resource-group rg-pred-maint-prod \
  --query hostName -o tsv)

REDIS_KEY=$(az redis list-keys \
  --name redis-pred-maint-prod \
  --resource-group rg-pred-maint-prod \
  --query primaryKey -o tsv)

# Update feature_store.yaml
cat > feature_store.yaml << EOF
project: pred_maint
provider: local
online_store:
  type: redis
  connection_string: "redis://:${REDIS_KEY}@${REDIS_HOST}:6380/0?ssl=True"
offline_store:
  type: file
  path: /data/feast/offline
entity_key_serialization_version: 2
EOF

# Apply feature definitions
feast apply

# Verify
feast feature-views list
```

**Expected Output:**
```
Registered entity: machine_id
Registered feature view: sensor_stats_view
```

```bash
# Return to project root
cd ..
```

---

### Step 9: Start Data Collection

```bash
# Set OpenWeatherMap API key
export OPENWEATHER_API_KEY="<your-api-key>"

# Option 1: Collect sample data for quick demo (2 hours)
python src/data/ingestion.py \
  --api-key $OPENWEATHER_API_KEY \
  --duration 2 \
  --interval 600

# Option 2: Start continuous hourly collection (runs forever)
python src/data/scheduler.py

# Expected output: Data saved to data/live/sensor_data_latest.parquet
```

**Quick Verification:**
```bash
# Check data file
ls -lh data/live/
python -c "import pandas as pd; df = pd.read_parquet('data/live/sensor_data_latest.parquet'); print(f'Collected {len(df)} samples')"
```

---

### Step 10: Train Initial Model

```bash
# Run automated training pipeline
python src/quick_start.py
```

**Expected Output:**
```
📥 STEP 1: Automated Data Ingestion
✅ Data Ready:
   - Training samples: 8,000
   - Testing samples: 2,000
   - Features: 32
   - Anomaly rate: 10.23%

🤖 STEP 2: Model Training
✅ Model trained successfully
✅ Model exported to ONNX
✅ Model saved to outputs/models/
```

**Verify Model Files:**
```bash
ls -lh outputs/models/
# Expected: anomaly_model.onnx, model_metadata.json
```

---

### Step 11: Connect to AKS Cluster

```bash
# Get AKS credentials
RESOURCE_GROUP="rg-pred-maint-prod"
AKS_CLUSTER_NAME="aks-pred-maint-prod"

az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --overwrite-existing

# Verify connection
kubectl get nodes
```

**Expected Output:**
```
NAME                                STATUS   ROLES   AGE   VERSION
aks-nodepool1-12345678-vmss000000   Ready    agent   10m   v1.28.0
aks-nodepool1-12345678-vmss000001   Ready    agent   10m   v1.28.0
aks-nodepool1-12345678-vmss000002   Ready    agent   10m   v1.28.0
```

---

### Step 12: Build and Push Docker Image

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show \
  --name $ACR_NAME \
  --query loginServer -o tsv)

# Build Docker image
docker build -t ${ACR_LOGIN_SERVER}/pred-maint:latest \
  -f src/serving/Dockerfile \
  ./src/serving

# Push to ACR
docker push ${ACR_LOGIN_SERVER}/pred-maint:latest

# Verify image
az acr repository show \
  --name $ACR_NAME \
  --image pred-maint:latest
```

**Expected Output:** Image details with size and creation time

---

### Step 13: Deploy Application with Helm

```bash
# Update Helm values with ACR details
cat > charts/pred-maint/values-prod.yaml << EOF
image:
  repository: ${ACR_LOGIN_SERVER}/pred-maint
  tag: latest
  pullPolicy: Always

replicaCount: 3

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

env:
  AZUREML_WORKSPACE_NAME: mlw-pred-maint-prod
  AZUREML_RESOURCE_GROUP: rg-pred-maint-prod
  MODEL_NAME: anomaly-detection-model
  DRIFT_THRESHOLD: "0.3"
  DRIFT_WINDOW_SIZE: "1000"
EOF

# Create namespace
kubectl create namespace production

# Deploy with Helm
helm install pred-maint ./charts/pred-maint \
  --namespace production \
  --values charts/pred-maint/values-prod.yaml

# Monitor deployment
kubectl get pods -n production --watch
```

**Expected Output:**
```
NAME                          READY   STATUS    RESTARTS   AGE
pred-maint-xxxxx-yyyyy        2/2     Running   0          2m
pred-maint-xxxxx-zzzzz        2/2     Running   0          2m
pred-maint-xxxxx-aaaaa        2/2     Running   0          2m
```

**Wait for all pods to show `2/2 Running`** (both containers in each pod)

---

### Step 14: Verify Deployment

```bash
# Check pod status
kubectl get pods -n production

# Check logs
kubectl logs -n production deployment/pred-maint -c inference --tail=50

# Get service endpoint
kubectl get svc pred-maint -n production

# Get external IP (may take 2-3 minutes to provision)
SERVICE_IP=$(kubectl get svc pred-maint -n production \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Service IP: $SERVICE_IP"
```

**Test Health Endpoint:**
```bash
curl http://$SERVICE_IP/health

# Expected response:
# {"status":"healthy","model_loaded":true,"timestamp":"..."}
```

**Test Prediction Endpoint:**
```bash
curl -X POST http://$SERVICE_IP/predict \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "machine_001",
    "temperature": 75.5,
    "pressure": 101.3,
    "humidity": 65.0,
    "wind_speed": 12.5
  }'

# Expected response:
# {"is_anomaly":false,"anomaly_score":0.42,"machine_id":"machine_001"}
```

**Test Metrics Endpoint:**
```bash
curl http://$SERVICE_IP/metrics | grep inference_requests_total
```

---

### Step 15: Configure GitHub Actions (CI/CD)

```bash
# Navigate to GitHub repository settings
# Settings > Secrets and variables > Actions > New repository secret

# Add these secrets:
```

**Required GitHub Secrets:**

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `AZURE_CREDENTIALS` | Service principal JSON from Step 4 | Copy entire JSON output |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID | `az account show --query id -o tsv` |
| `RESOURCE_GROUP` | `rg-pred-maint-prod` | From your .env file |
| `AKS_CLUSTER_NAME` | `aks-pred-maint-prod` | From your .env file |
| `ACR_NAME` | ACR name | `$(terraform output -raw acr_name -state=infra/terraform.tfstate)` |
| `ACR_USERNAME` | ACR admin username | `az acr credential show --name $ACR_NAME --query username -o tsv` |
| `ACR_PASSWORD` | ACR admin password | `az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv` |
| `AZUREML_WORKSPACE_NAME` | `mlw-pred-maint-prod` | From your .env file |
| `OPENWEATHER_API_KEY` | Your API key | From .env file |

**Add secrets via CLI (optional):**
```bash
# Requires GitHub CLI (gh)
gh secret set AZURE_SUBSCRIPTION_ID --body "$(az account show --query id -o tsv)"
gh secret set RESOURCE_GROUP --body "rg-pred-maint-prod"
# ... repeat for other secrets
```

---

### Step 16: Test CI/CD Pipeline

```bash
# Make a small change to trigger workflow
echo "# Build $(date)" >> .github/workflows/README.md

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main

# Monitor workflow
# Go to: https://github.com/yourusername/DriftDetector/actions
```

**Expected:** Build and Deploy workflow runs successfully

---

### Step 17: Configure Monitoring

```bash
# Deploy Prometheus (optional but recommended)
kubectl create namespace monitoring

# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring

# Access Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open browser: http://localhost:9090
```

**Useful Prometheus Queries:**
- `inference_requests_total` - Total requests
- `rate(inference_requests_total[5m])` - Request rate
- `data_drift_score` - Drift scores by feature

---

### Step 18: Set Up Drift Monitoring Alerts

```bash
# Configure Azure Monitor Alert Rule
az monitor metrics alert create \
  --name "high-drift-detected" \
  --resource-group rg-pred-maint-prod \
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-pred-maint-prod \
  --condition "avg features_with_drift > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group <action-group-id>
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Infrastructure deployed successfully (12 Azure resources)
- [ ] AKS cluster running with 3 nodes
- [ ] Docker image pushed to ACR
- [ ] Helm deployment successful (3 pods running)
- [ ] Health endpoint returns `200 OK`
- [ ] Prediction endpoint returns valid responses
- [ ] Metrics endpoint exposing Prometheus metrics
- [ ] Data collection running (hourly updates)
- [ ] GitHub Actions workflows configured
- [ ] Prometheus monitoring active

---

## 🔧 Common Issues and Solutions

### Issue 1: Terraform Apply Fails with "Quota Exceeded"

**Solution:**
```bash
# Request quota increase
az vm list-usage --location westus2 --output table | grep "Standard DSv3 Family"

# Or change VM size in infra/variables.tf
```

### Issue 2: Cannot Connect to AKS

**Solution:**
```bash
# Reset credentials
az aks get-credentials --resource-group rg-pred-maint-prod --name aks-pred-maint-prod --admin --overwrite-existing

# Verify Azure AD permissions
az ad signed-in-user show
```

### Issue 3: Pods Stuck in "ImagePullBackOff"

**Solution:**
```bash
# Attach ACR to AKS
az aks update \
  --name aks-pred-maint-prod \
  --resource-group rg-pred-maint-prod \
  --attach-acr $ACR_NAME
```

### Issue 4: External IP "Pending"

**Solution:**
```bash
# Check service type
kubectl get svc pred-maint -n production -o yaml | grep type

# Wait 3-5 minutes for Azure Load Balancer provisioning
kubectl get svc -n production --watch
```

### Issue 5: Data Collection Fails

**Solution:**
```bash
# Verify API key
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=$OPENWEATHER_API_KEY"

# Check rate limits (1000 calls/day for free tier)
```

---

## 💰 Cost Management

**Monitor Costs:**
```bash
# Check current costs
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --output table
```

**Set Budget Alert:**
```bash
az consumption budget create \
  --resource-group rg-pred-maint-prod \
  --budget-name monthly-budget \
  --amount 600 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31
```

---

## 🧹 Cleanup (Tear Down)

**To remove all Azure resources:**

```bash
# Destroy Terraform infrastructure
cd infra
terraform destroy

# Type 'yes' when prompted

# Verify resource group deleted
az group list --output table | grep pred-maint

# Delete service principal
az ad sp delete --id <service-principal-id>
```

**⚠️ WARNING:** This will delete ALL resources and data. Cannot be undone!

---

## 📞 Support

If you encounter issues:

1. **Check logs:** `kubectl logs -n production deployment/pred-maint -c inference`
2. **Review events:** `kubectl get events -n production --sort-by='.lastTimestamp'`
3. **GitHub Issues:** [Create an issue](https://github.com/yourusername/DriftDetector/issues)
4. **Documentation:** See [docs/](./docs/) for detailed guides

---

## 🎯 Next Steps

After successful deployment:

1. **Load Testing:** Run `k6 run tests/load_test.js`
2. **Custom Models:** Train with your own sensor data
3. **Multi-Region:** Deploy to additional Azure regions
4. **Advanced Monitoring:** Configure Grafana dashboards
5. **Production Hardening:** Enable TLS, network policies, pod security

---

**Deployment Complete! 🎉**

Your predictive maintenance system is now running on Azure with automated drift detection and model retraining capabilities.

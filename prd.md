### **Project Spec: Predictive Maintenance w/ Drift Detection (AzureML + Feast + Evidently)**

**Project Name:** `azure-pred-maint-ops`
**Role:** Senior MLOps Engineer
**Objective:** Build an end-to-end Predictive Maintenance system that detects data drift on live sensor data and triggers automated retraining in AzureML.

---

### **1. Core Architecture**

* **Cloud Provider:** Microsoft Azure (West US 2)
* **Data Flow:**
1. **Ingest:** Simulated IoT sensor data (Vibration, Temperature, Rotational Speed) pushes to an Event Hub (simulated via Kafka or simple HTTP endpoint for this MVP).
2. **Feature Store:** **Feast** (running on Azure Cache for Redis) serves features to the model.
3. **Inference:** A Dockerized **FastAPI** container running an ONNX model, deployed on **AKS** (Azure Kubernetes Service).
4. **Observability:** A "Sidecar" container running **Evidently AI** scrapes inference logs, calculates drift (Wasserstein Distance), and pushes metrics to Azure Monitor.
5. **Feedback Loop:** If Drift > Threshold, an Azure Function triggers an **AzureML Pipeline** to retrain the model.



### **2. Tech Stack Constraints (Strict)**

* **Infrastructure:** Terraform (Azure Provider)
* **Orchestration:** Kubernetes (AKS) + Helm Charts
* **Model Training:** AzureML SDK v2 (Python)
* **Feature Store:** Feast (0.35+)
* **Monitoring:** Evidently AI + Prometheus
* **CI/CD:** GitHub Actions (generate the `.github/workflows` YAMLs)

---

### **3. Implementation Plan (Agent Instructions)**

#### **Phase 1: Infrastructure as Code (IaC)**

* Create a `infra/` directory.
* Generate Terraform HCL code to provision:
* `azurerm_resource_group`
* `azurerm_kubernetes_cluster` (AKS)
* `azurerm_machine_learning_workspace`
* `azurerm_redis_cache` (For Feast)
* `azurerm_container_registry` (ACR)



#### **Phase 2: Feature Store Setup**

* Create a `features/` directory.
* Initialize a Feast repository (`feature_store.yaml` configured for Azure Redis).
* Define a `definitions.py` containing:
* **Entity:** `machine_id`
* **Feature View:** `sensor_stats_view` (aggregation of vibration/temp over 1hr windows).



#### **Phase 3: Model Development (Inner Loop)**

* Create `src/training/`.
* Write a Python script `train.py` using **AzureML SDK v2**:
* Load data from Feast (offline store).
* Train an `IsolationForest` (unsupervised anomaly detection).
* Log metrics and register the model to AzureML Model Registry using MLflow.


* Create an `azureml_pipeline.yml` to define this job.

#### **Phase 4: Deployment & Monitoring (Outer Loop)**

* Create `src/serving/`.
* **App Container:** Write a `main.py` (FastAPI) that loads the model from AzureML and serves an `/predict` endpoint.
* **Drift Container:** Write a `drift_service.py` using **Evidently**.
* It should accept a batch of recent inference inputs.
* Run `Report(metrics=[DataDriftPreset()])`.
* Expose a `/metrics` endpoint for Prometheus to scrape.


* **Helm Chart:** Create `charts/pred-maint/` deploying both containers in a single Pod.

---

### **4. Required File Structure**

Generate the following file tree. Do not create empty files; fill them with functional boilerplate code.

```text
/
├── infra/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── features/
│   ├── feature_store.yaml
│   └── definitions.py
├── src/
│   ├── training/
│   │   ├── train.py          # AzureML training script
│   │   └── pipeline.yml      # AzureML Pipeline definition
│   ├── serving/
│   │   ├── main.py           # FastAPI inference app
│   │   ├── drift_service.py  # Evidently AI drift calculator
│   │   └── Dockerfile
├── charts/
│   └── pred-maint/           # Helm chart for AKS deployment
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD pipeline
└── README.md                 # Documentation for the project

```

---

### **5. Acceptance Criteria**

1. The Terraform code must validly `plan` without circular dependencies.
2. The `train.py` must use `mlflow.autolog()`.
3. The FastAPI app must include a Pydantic model for input validation.
4. The Drift Service must return a JSON response indicating if `drift_detected` is True/False.

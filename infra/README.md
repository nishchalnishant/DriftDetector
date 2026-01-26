# Terraform Infrastructure Deployment

This directory contains Terraform configuration for provisioning Azure infrastructure.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.5.0
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Azure subscription with appropriate permissions

## Resources Provisioned

- **Azure Kubernetes Service (AKS)**: Managed Kubernetes cluster with auto-scaling
- **Azure Container Registry (ACR)**: Private container registry
- **Azure Machine Learning Workspace**: ML workspace with compute clusters
- **Azure Redis Cache**: Feature store online storage (Premium tier)
- **Storage Accounts**: For Azure ML and Feast offline store
- **Key Vault**: Secrets management
- **Log Analytics & Application Insights**: Monitoring and observability

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription <your-subscription-id>
```

### 2. Initialize Terraform

```bash
cd infra
terraform init
```

### 3. Configure Variables

Create a `terraform.tfvars` file:

```hcl
project_name         = "pred-maint"
environment          = "prod"
location             = "westus2"
resource_group_name  = "rg-pred-maint-prod"
aks_node_count       = 3
enable_gpu_nodes     = false
```

### 4. Plan Deployment

```bash
terraform plan -out=tfplan
```

### 5. Apply Configuration

```bash
terraform apply tfplan
```

## State Management

For production deployments, configure remote state in Azure Storage:

```bash
# Create storage account for Terraform state
az storage account create \
  --name tfstatepredmaint \
  --resource-group rg-terraform-state \
  --location westus2 \
  --sku Standard_LRS

# Create container
az storage container create \
  --name tfstate \
  --account-name tfstatepredmaint
```

Then update the backend configuration in `main.tf` or create `backend.hcl`:

```hcl
storage_account_name = "tfstatepredmaint"
container_name       = "tfstate"
key                  = "prod.terraform.tfstate"
```

Initialize with backend:

```bash
terraform init -backend-config=backend.hcl
```

## Outputs

After successful deployment, retrieve important values:

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group $(terraform output -raw resource_group_name) \
  --name $(terraform output -raw aks_cluster_name)

# Get ACR login server
terraform output -raw acr_login_server

# Get Redis connection string (sensitive)
terraform output -raw redis_connection_string
```

## Cost Optimization

- Default configuration uses `Standard_D4s_v3` VMs for AKS
- Redis uses Premium P1 tier (required for Feast performance)
- GPU nodes are disabled by default (set `enable_gpu_nodes = true` if needed)

Estimated monthly cost (West US 2):
- AKS: ~$200-300 (3 nodes)
- Redis Premium P1: ~$150
- Azure ML: ~$50 (baseline)
- Storage & monitoring: ~$50
- **Total: ~$450-550/month**

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources and data. Ensure you have backups.

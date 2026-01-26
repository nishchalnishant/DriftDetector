variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "pred-maint"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "westus2"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-pred-maint-prod"
}

# AKS Configuration
variable "aks_cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "aks-pred-maint-prod"
}

variable "aks_node_count" {
  description = "Initial number of nodes in the AKS cluster"
  type        = number
  default     = 3
}

variable "aks_min_nodes" {
  description = "Minimum number of nodes for auto-scaling"
  type        = number
  default     = 2
}

variable "aks_max_nodes" {
  description = "Maximum number of nodes for auto-scaling"
  type        = number
  default     = 10
}

variable "aks_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "enable_gpu_nodes" {
  description = "Enable GPU node pool"
  type        = bool
  default     = false
}

variable "gpu_vm_size" {
  description = "VM size for GPU nodes"
  type        = string
  default     = "Standard_NC6s_v3"
}

variable "gpu_node_count" {
  description = "Initial number of GPU nodes"
  type        = number
  default     = 1
}

variable "gpu_max_nodes" {
  description = "Maximum number of GPU nodes"
  type        = number
  default     = 3
}

# ACR Configuration
variable "acr_name" {
  description = "Name of the Azure Container Registry"
  type        = string
  default     = "acrpredmaintprod"
}

# Azure ML Configuration
variable "azureml_workspace_name" {
  description = "Name of the Azure ML workspace"
  type        = string
  default     = "mlw-pred-maint-prod"
}

variable "storage_account_name" {
  description = "Name of the storage account for Azure ML"
  type        = string
  default     = "stpredmaintprod"
}

variable "key_vault_name" {
  description = "Name of the Key Vault"
  type        = string
  default     = "kv-pred-maint-prod"
}

# Redis Configuration
variable "redis_cache_name" {
  description = "Name of the Redis cache for Feast"
  type        = string
  default     = "redis-feast-prod"
}

variable "redis_sku" {
  description = "Redis cache SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Premium"
}

variable "redis_family" {
  description = "Redis family (C for Basic/Standard, P for Premium)"
  type        = string
  default     = "P"
}

variable "redis_capacity" {
  description = "Redis cache capacity"
  type        = number
  default     = 1
}

# Feast Storage Configuration
variable "feast_storage_account_name" {
  description = "Name of the storage account for Feast offline store"
  type        = string
  default     = "stfeastprod"
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "PredictiveMaintenance"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Owner       = "MLOpsTeam"
  }
}

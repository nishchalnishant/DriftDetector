# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.main.id
}

# AKS Outputs
output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "aks_cluster_id" {
  description = "ID of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.id
}

output "aks_kube_config" {
  description = "Kubeconfig for AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "aks_host" {
  description = "AKS cluster host"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive   = true
}

# ACR Outputs
output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azurerm_container_registry.acr.name
}

output "acr_login_server" {
  description = "Login server for ACR"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  description = "Admin username for ACR"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Admin password for ACR"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

# Azure ML Outputs
output "azureml_workspace_name" {
  description = "Name of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.main.name
}

output "azureml_workspace_id" {
  description = "ID of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.main.id
}

# Redis Outputs
output "redis_hostname" {
  description = "Hostname of the Redis cache"
  value       = azurerm_redis_cache.feast.hostname
}

output "redis_ssl_port" {
  description = "SSL port of the Redis cache"
  value       = azurerm_redis_cache.feast.ssl_port
}

output "redis_primary_access_key" {
  description = "Primary access key for Redis"
  value       = azurerm_redis_cache.feast.primary_access_key
  sensitive   = true
}

output "redis_connection_string" {
  description = "Connection string for Redis"
  value       = "rediss://:${azurerm_redis_cache.feast.primary_access_key}@${azurerm_redis_cache.feast.hostname}:${azurerm_redis_cache.feast.ssl_port}/0"
  sensitive   = true
}

# Storage Outputs
output "storage_account_name" {
  description = "Name of the storage account for Azure ML"
  value       = azurerm_storage_account.main.name
}

output "feast_storage_account_name" {
  description = "Name of the storage account for Feast"
  value       = azurerm_storage_account.feast.name
}

output "feast_storage_connection_string" {
  description = "Connection string for Feast storage"
  value       = azurerm_storage_account.feast.primary_connection_string
  sensitive   = true
}

# Key Vault Outputs
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# Application Insights
output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

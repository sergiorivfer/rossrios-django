terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "aae3458a-01a1-43be-b868-2f3ab6d5d26a"
  tenant_id       = "e8e0c88a-4b7c-4aba-aaca-e6ba27a8c2e2"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rossrios-rg-tf"
  location = "Central US"
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "rossriosregistrytf"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
}

# PostgreSQL
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "rossrios-db-tf"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  administrator_login    = "rossriosadmin"
  administrator_password = "RossRios2026!"
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
  zone                   = "1"
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "rossrios"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "postgres_host" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}
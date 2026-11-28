# Day 4: Azure AI Foundry resource + one pay-per-token mini model deployment.
# terraform init && terraform apply
# Teardown at the end of the workshop: az group delete -n rg-ai-lab --yes

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  # subscription_id comes from the ARM_SUBSCRIPTION_ID environment variable,
  # so it is not committed to this public repo. Set it once per terminal:
  #   $env:ARM_SUBSCRIPTION_ID = (az account show --query id -o tsv)
}

data "azurerm_resource_group" "lab" {
  name = "rg-ai-lab"
}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_cognitive_account" "ai" {
  name                  = "ai-lab-${random_string.suffix.result}"
  location              = data.azurerm_resource_group.lab.location
  resource_group_name   = data.azurerm_resource_group.lab.name
  kind                  = "AIServices"
  sku_name              = "S0"
  custom_subdomain_name = "ai-lab-${random_string.suffix.result}"   # globally unique endpoint
}

resource "azurerm_cognitive_deployment" "mini" {
  name                 = "gpt-4.1-mini"   # becomes MODEL_NAME in .env
  cognitive_account_id = azurerm_cognitive_account.ai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4.1-mini"
    version = "2025-04-14"
  }

  sku {
    name     = "Standard"   # pay-per-token; data processed in South India
    capacity = 10           # 10K tokens per minute: caps a runaway loop
  }
}

output "endpoint" {
  value = "${azurerm_cognitive_account.ai.endpoint}openai/v1/"
}

output "deployment_name" {
  value = azurerm_cognitive_deployment.mini.name
}
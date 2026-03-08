terraform {
  required_version = ">= 1.8.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.32"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig
}

resource "kubernetes_namespace" "qcp" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "quantum-control-plane"
    }
  }
}

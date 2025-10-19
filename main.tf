terraform {
  backend "http" {}

  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
      version = "4.18.0"
    }
    local = {
      source = "hashicorp/local"
      version = "2.4.1"
    }
    http = {
      source = "hashicorp/http"
      version = "3.4.1"
    }
  }
}

variable "cf_api_key" {
  description = "Cloudflare API key."
  type        = string
}

variable "cf_acct_id" {
  description = "Cloudflare account ID."
  type        = string
}

variable "TF_ROOT" {
  description = "Terraform root directory."
  type        = string
}

provider "cloudflare" {
  api_token = var.cf_api_key
}

data "local_file" "output_txt" {
    filename = "${var.TF_ROOT}/output.txt"
}

locals {
    cloudflare_account_id = var.cf_acct_id
    master_combined_lists = data.local_file.output_txt.content
}

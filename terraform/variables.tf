variable "aws_region" {
  description = "AWS region to deploy into"
  type = string
  default = "eu-west-2"
}

variable "aws_profile" {
  description = "AWS CLI profile name"
  type = string
  default = "plate-tracker"
}

variable "project" {
  description = "Project name used for resource naming"
  type = string
  default = "plate-tracker"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type = string
  default = "plate_tracker"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type = string
  sensitive = true
}

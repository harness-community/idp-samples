variable "project_name" {
  description = "The new application name you are onboarding"
  type        = string
  default     = "Lambda Boilerplate"
}

locals {
  sanitized_input = trimspace(lower(replace(replace(var.project_name, " ", ""), "[^a-z0-9_]", "")))
  first_char      = substr(local.sanitized_input, 0, 1)
  last_char       = substr(local.sanitized_input, -1, 1)
  final_input     = local.sanitized_input != "" ? local.sanitized_input : format("%s%s%s", local.first_char, local.sanitized_input, local.last_char)
}


output "sanitized_input" {
  value = local.sanitized_input
}

output "first_char" {
  value = local.first_char
}

output "last_char" {
  value = local.last_char
}

output "final_input" {
  value = local.final_input
}


variable "repo_name" {
  description = "The new repo name you are onboarding"
  type        = string
  default     = "python-lambda-starter"
}

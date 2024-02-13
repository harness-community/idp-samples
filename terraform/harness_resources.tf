resource "harness_platform_project" "project" {  
    name      = var.project_name 
    identifier = local.final_input  
    org_id    = "ORG_ID"  
}

resource "harness_platform_service" "lambda_service" {
  identifier  = local.final_input
  name        = var.project_name
  depends_on = [
    harness_platform_project.project,
  ]
  description = "Lambda"
  org_id      = "SE_Sandbox"
  project_id  = local.final_input
  yaml = <<-EOT
                service:
                  name: ${var.project_name}
                  identifier: ${local.final_input}
                  serviceDefinition:
                    type: AwsLambda
                    spec:
                      manifests:
                        - manifest:
                            identifier: manifest
                            type: AwsLambdaFunctionDefinition
                            spec:
                              store:
                                type: Github
                                spec:
                                  connectorRef: account.Onboarding_Storz
                                  gitFetchType: Branch
                                  paths:
                                    - manifests/serverless.yaml
                                  repoName: ${var.repo_name}
                                  branch: main
                      artifacts:
                        primary:
                          primaryArtifactRef: <+input>
                          sources:
                            - spec:
                                connectorRef: account.AWS_Sales_Account
                                bucketName: storzccm
                                region: us-east-1
                                filePath: release-<+pipeline.executionId>.zip
                              identifier: artifact
                              type: AmazonS3
                  gitOpsEnabled: false

              EOT
}


resource "harness_platform_environment" "example" {
  identifier = "preprod"
  name       = "Pre-Production"
  org_id     = "SE_Sandbox"
  depends_on = [
    harness_platform_project.project,
  ]
  project_id  = local.final_input
  tags       = ["env:nonprod"]
  type       = "PreProduction"
  description = "My non-production environment"
}


resource "harness_platform_infrastructure" "infra" {
  identifier      = "AWS"
  name            = "AWS"
  org_id          = "SE_Sandbox"
  depends_on = [
    harness_platform_environment.example,
  ]
  project_id      = local.final_input
  env_id          = "preprod"
  type            = "AwsLambda"
  deployment_type = "AwsLambda"
  yaml            = <<-EOT
        infrastructureDefinition:
          name: AWS
          identifier: AWS
          description: ""
          orgIdentifier: SE_Sandbox
          projectIdentifier: ${local.final_input}
          environmentRef: preprod
          deploymentType: AwsLambda
          type: AwsLambda
          spec:
            connectorRef: account.AWS_Sales_Account
            region: us-east-2
          allowSimultaneousDeployments: false
      EOT
}


resource "harness_platform_pipeline" "build_and_deploy" {
  identifier = "build_and_deploy"
  org_id     = "SE_Sandbox"
  depends_on = [
    harness_platform_infrastructure.infra,
    harness_platform_service.lambda_service,
  ]
  project_id       = local.final_input
  name       = "Build and Deploy"
  yaml = <<-EOT
      pipeline:
          name: Build and Deploy
          identifier: build_and_deploy
          allowStageExecutions: false
          projectIdentifier: ${local.final_input}
          orgIdentifier: SE_Sandbox
          tags: {}
          properties:
            ci:
              codebase:
                connectorRef: account.Onboarding_Storz
                repoName: ${var.repo_name}
                build: <+input>

          stages:
              - stage:
                  name: Build
                  identifier: Build
                  description: ""
                  type: CI
                  spec:
                    cloneCodebase: true
                    platform:
                      os: Linux
                      arch: Amd64
                    runtime:
                      type: Cloud
                      spec: {}
                    execution:
                      steps:
                        - step:
                            type: Run
                            name: Zip
                            identifier: Zip
                            spec:
                              shell: Sh
                              command: |+
                                zip release-<+pipeline.executionId>.zip lambda_function.py

                        - step:
                            type: S3Upload
                            name: S3 Upload
                            identifier: S3_Upload
                            spec:
                              connectorRef: account.AWS_Sales_Account
                              region: us-east-1
                              bucket: storzccm
                              sourcePath: release-<+pipeline.executionId>.zip
              - stage:
                  name: Deploy
                  identifier: Deploy
                  description: ""
                  type: Deployment
                  spec:
                    deploymentType: AwsLambda
                    service:
                      serviceRef: ${local.final_input}
                      serviceInputs:
                        serviceDefinition:
                          type: AwsLambda
                          spec:
                            artifacts:
                              primary:
                                primaryArtifactRef: <+input>
                                sources: <+input>
                    environment:
                      environmentRef: preprod
                      deployToAll: false
                      infrastructureDefinitions:
                        - identifier: AWS
                    execution:
                      steps:
                        - step:
                            name: Deploy Aws Lambda
                            identifier: deployawslambda
                            type: AwsLambdaDeploy
                            timeout: 10m
                            spec: {}
                      rollbackSteps:
                        - step:
                            name: Aws Lambda rollback
                            identifier: awslambdarollback
                            type: AwsLambdaRollback
                            timeout: 10m
                            spec: {}
                  tags: {}
                  failureStrategies:
                    - onFailure:
                        errors:
                          - AllErrors
                        action:
                          type: StageRollback
  EOT
}

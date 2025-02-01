# Catalog-fed-ramp
The following folder contains guidelines and examples on how to create scorecards based on custom attributes, as an example to meet FIPS compliance.  See https://harness.atlassian.net/wiki/spaces/IE1/pages/22281127180/IDP+PS+Best+Practice+Implementations for case studies.

The scorecards are being reviewed by development team each week, and OPA policies will be eventually used to warn or enforce from deployment until dev team fixes defects to be in federal compliance.

The score card will be relying on several custom attributes to pass:

metadata.cve.warn
metadata.cve.fail
metadata.baseImage.compliance
metadata.fips.compliance

These attributes are populated using 3 pipelines to test the service Dockerfile, Jira tickets, and deployed image.  The pipelines run once a day for each registered service to update these flags.  Timestamp attributes are stamped for each execution.

In this example, the pipelines are store in infra-harness repo, along with python scripts, and catalog-info.yaml.  But there should be logic to allow overrides to use catalog-info.yaml residing in the service repo.

# Catalog 
Catalog file is centralized in a repo managed by Infra team, or it could be maintained by each development team owning the service.  However, the pipeline that performs the checks should be owned by infra or security team.

Here is an example of a typical registration of catalog component.

```yaml
# see https://developer.harness.io/docs/internal-developer-portal/catalog/how-to-create-idp-yaml/

apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
# name of the service
  name: test-service
# tags - python/go/nodejs/java and fedramp are required for the scorecard to include only fedramp tags (exclusion rule does not exist yet)
  tags:
    - auto-generated
    - python
    - fedramp
# useful links
  links:
    - url: https://app.harness.io/ng/account/xyz/module/cd/orgs/demo/projects/testervice/overview
      title: Deployment Dashboard
      icon: dashboard
 # recommended annotations
  annotations:
# source code location for catalog-info.yaml, omit if move to service repo
    backstage.io/source-location: url:https://github.com/acme/test-service
# service repository
    github.com/project-slug: acme/test-service
# jira project key
    jira/project-key: xyz
# optional jira component
    jira/component: xyz-service
# technical doc 
    backstage.io/techdocs-ref: url:https://github.com/acme/test-service
# project url required for feature flag plugin
    harness.io/project-url: https://app.harness.io/ng/account/xyz/all/orgs/xyz/projects/testservice
# serviceId required for listing CD and also used in OPA 
    harness.io/cd-serviceId: testserviceid    
# numerate pipelines as needed (cd-serviceId list its default pipelines)
    harness.io/pipelines: |
      All in One Pipeline: 
      Daily Security Scans: https://app.harness.io/ng/account/xyz/module/ci/orgs/demo/projects/testservice/pipelines/Daily_Security_Scan...
# enumerate services as needed (cd-serviceId list its default service)
    harness.io/services: |
      test-service: http://...
# optional jql warn / fail override (custom)
    acme/cve-warn: 'project = <<projectKey>> AND type = CVE AND "CVE SLA: Due date[Date]" >= endOfDay() AND "CVE SLA: Due date[Date]" <= 5d AND statusCategory != Done'
    acme/cve-fail: 'project = <<projectKey>> and type = CVE and "CVE SLA: Due date[Date]" < endOfDay() AND statusCategory != Done'


spec:
  type: service
  lifecycle: staging
# claim owner
  owner: devops_usergroup
# optional reference to grpc definition
  providesApis:
    - test-service-grpc-api  
```

## Python scripts 

# common.py
Contains commonly used python functions used across scripts:

extract_image_and_tag - extracts the Dockerfile's image_name and tag.  Requires stage name to be labelled.

fetch_catalog_attributes - reads the catalog info and extract any custom info from catalog info using annotations acme/docker-path and tags for languages

updateCatalogAttributes - very useful fucntion to update IDP catalog attributes 

determine_catalog_path - determines where to pull catalog info yaml, either from service repo path ./harness/idp/catalog-info.yaml or from harness-infra repo (the repo hosting all the catalog-info.yaml owned by infra or security team)

# Base tag compliance check
docker-basetag-check.py inspects the Dockerfile looking for specific stage tags, and inspects whether the image used matches the ones defined in compliant_image function. The results are posted back to IDP catalog.

# CVE check
jira-cve-check-dir.py iterates through the catalog configuration file for warn / fail overrides (use default jql query defined in the code otherwise), and post queries to Jira.  Results are updated into IDP catalog.


# fetch-repo-default-branch.py
Queries GITHUB to determine a service's default branch (main or master for example).

# checks language FIPs compliance
fips-validator.py uses different logic to check if the image built by the service passes compliance for different languages.  It examines the service's helm chart, determine the image built, pulls the image.  It will perform MD5 tests for nodejs and python.  It will check for specific attributes in the docker image for labels matching chain guard inages.  Chain guard images are useful for fed compliance.

# experimental
docker-image-fips.py is an experimental docker n docker build and execute commands.  Deprecated.  Uses fips subfolder for docker n docker build as an example

# catalog-cve-scorecard.yaml
Pipeline to pull information from Jira to populate cve ticket violates into IDP

# dockerverifications-pipeline.yaml
Pipeline to very base image used

# fips-pipeline.yaml
Examine the helm chart in the service repo to pull the latest image, to check for FIPS compliance for different languages

# Custom checks for score card
# Fips compliance check
Catalog Info YAML 
Equal to TRUE
jexl: <+metadata.fips.compliance>

# Base Image Compliance
Catalog Info YAML 
Equal to TRUE
jexl: <+metadata.baseImage.compliance>

# CVE Fail
Catalog Info YAML 
Equal to 0
jexl: <+metadata.cve.fail>

# CVE Warn
Catalog Info YAML 
Equal to 0
jexl: <+metadata.cve.warn>

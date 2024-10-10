# harness account to catalog

an example python script to query harness for orgs, projects, and services

and generate domains, systems, and components for each item

an example of the output generated is [this repo](https://github.com/rssnyder/idp-service-catalog/tree/main)

## usage

authentication:

```
export HARNESS_URL=app.harness.io
export HARNESS_ACCOUNT_ID=abc123
export HARNESS_PLATFORM_API_KEY=sat.abc123.xxx
```

settings:

```
# to generate a locations catalog yaml, specify your repo location
export REPO=https://github.com/myorg/myrepo
# the main branch of the repo (default: main)
export BRANCH=main
# and with a custom file name (default: locations.yaml)
export LOCATION=my-harness-locations.yaml

# to create files in a sub folder
export DIR=catalogs/gohere
```

execution:
```
python main.py
```

the above will generate files in the following format:

```
locations.yaml
<org a>/_domain.yaml
<org a>/<proj b>/_system.yaml
<org a>/<proj b>/<service c>.yaml
```

by default it will not overwrite any existing files

## development guide

### main.py

main function of program, scan harness and create catalog yamls

### harness.py

functions to retrive information from harness

### catalogs.py

functions to render catalogs based on templates

### templates/

jinja2 template for catalogs

### Dockerfile

container for running the application
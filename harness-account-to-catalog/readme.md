# harness account to catalog

an example python script to query harness for orgs, projects, and services

and generate domains, systems, and components for each item

## usage

authentication:

```
export HARNESS_URL=app.harness.io
export HARNESS_ACCOUNT_ID=abc123
export HARNESS_PLATFORM_API_KEY=sat.abc123.xxx
```

execution:

```
python main.py
```

the above will generate files in the following format:

```
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

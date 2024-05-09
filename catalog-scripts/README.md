# scripts

## Create Services:
- Generates a monorepo with the following file structure, assigning random english names.

```sh
repo
   - antronasal-service
      - catalog-info.yaml
   - cespititous-service
      - catalog-info.yaml
   - ....
   - geomaly-service
        - catalog-info.yaml
```
## Delete Services:
- Will clean up the services already created.

## Registered Locations

- Discover catalog-info.yaml matching the regex filter and register under the catalog provided in `apiurl`. This would separate locations for all the matching catalog-info.yaml files and hence would be synchronised separately.

## IDP Catalog Wizard Script
- A pregenerated/created repo (let's call it chosen_repo) is to be cloned. After opening it on your code editor and from chosen_repo, below commands can be run to generate and register catalog-info.yaml files of all the repos in your org. The catalog-info.yaml files will be in - chosen_repo/services/{repos}/catalog-info.yaml where repos will be all the repo in your org. 

- Usage
   python3 idp-catalog-wizard.py [OPTIONS]
   Options:

   These are funtion args (function to be performed)
      --create-yamls: Create YAML files for repositories in local
      --register-yamls: Register YAML files which were created using previous command
      --run-all: Perform all actions: create YAML files, push changes, and register YAML files.

   These are supporting args (variables)
      --org ORG_NAME: Specify the organization name.
      --token TOKEN: Specify the token for authentication.
      --x_api_key X_API_KEY: Specify the X-API-Key for authentication.
      --account ACCOUNT_NAME: Specify the account name.
      --repo-pattern REPO_PATTERN: Specify a pattern to filter repositories.

      Case 1: Run command using --create-yamls args, then you'll have to manually push the files - "services/" ..... after which you can run command using --register-yamls args to register all the yamls.

      Case 2: Run command using --run-all args, all actions will be performed - create, push and register in one go.

- Example:
   ### Create YAML files for repositories in the organization "example-org" with the provided token (all given args in command below are required)
      python3 idp-catalog-wizard.py --create-yamls --org example-org --token your_token

   ### Register YAML files using X-API-Key and account name (all given args in command below are required)
      python3 idp-catalog-wizard.py --register-yamls --x_api_key your_x_api_key --account your_account

   ### Perform all actions: create YAML files, push changes, and register YAML files (all given args in command below are required)
      python3 idp-catalog-wizard.py --run-all --org example-org --token your_token --x_api_key your_x_api_key --account your_account


### Problems Solved Using Registeres Locations:

- The Github Catalog Discovery plugin registers 1 location per repository. This might not be a good idea when there are many (3000+ in this case) as any error in fetching one catalog-yaml would mark the whole location as failed and create trouble with the entity sync.

- While we work with the backstage team to identify a fix for this, we would recommend you to follow these scripts which would register separate locations for all the matching `catalog-info.yaml` files and hence would be synchronised separately.

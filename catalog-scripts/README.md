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

### Problems Solved Using Registeres Locations:

- The Github Catalog Discovery plugin registers 1 location per repository. This might not be a good idea when there are many (3000+ in this case) as any error in fetching one catalog-yaml would mark the whole location as failed and create trouble with the entity sync.

- While we work with the backstage team to identify a fix for this, we would recommend you to follow these scripts which would register separate locations for all the matching `catalog-info.yaml` files and hence would be synchronised separately.

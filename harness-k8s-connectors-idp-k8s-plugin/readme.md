#

Generate and update the configuration for the Kubernetes IDP plugin based on Kubernetes connectors at the account level.

Only uses connectors that use a masterURL and credentials as we cannot leverage delegate auth for connections with this plugin.

## setup 

- `HARNESS_URL`: URL for you harness instance (default: `app.harness.io`)
- `HARNESS_ACCOUNT_ID`: Id for your harness account
- `HARNESS_PLATFORM_API_KEY`: Harness api key with access to edit plugins in IDP
from os import getenv
from yaml import dump

from requests import post

HARNESS_URL = getenv("HARNESS_URL", "app.harness.io")

HEADERS = {
    "Harness-Account": getenv("HARNESS_ACCOUNT_ID"),
    "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
}

API_LIMIT = int(getenv("API_LIMIT", 1))


def get_connectors(type: str, page: int = 0) -> list:
    # get all connectors of the specified type from the Harness API

    resp = post(
        f"https://{HARNESS_URL}/ng/api/connectors/listV2",
        headers=HEADERS,
        params={
            "page": page,
            "limit": API_LIMIT,
            "accountIdentifier": HEADERS["Harness-Account"],
        },
        json={"types": [type], "filterType": "Connector"},
    )

    resp.raise_for_status()

    data = resp.json().get("data")

    if (page + 1) < int(data.get("totalPages")):
        data.extend(get_connectors(type, page + 1))

    return data.get("content")


def main() -> str:
    # get all masterURL connectors and build idp k8s plugin config

    env_variables = []
    proxy = []
    configs = {
        "kubernetes": {
            "serviceLocatorMethod": {"type": "multiTenant"},
            "clusterLocatorMethods": [{"type": "config", "clusters": []}],
        }
    }

    # filter on master url connectors
    for item in [
        x
        for x in get_connectors("K8sCluster")
        if (x["connector"]["spec"]["credential"]["type"] == "ManualConfig")
        and (
            x["connector"]["spec"]["credential"]["spec"]["auth"]["type"]
            == "ServiceAccount"
        )
    ]:
        id = item["connector"]["identifier"]
        url = item["connector"]["spec"]["credential"]["spec"]["masterUrl"]
        secret = item["connector"]["spec"]["credential"]["spec"]["auth"]["spec"][
            "serviceAccountTokenRef"
        ].split(".")[-1]
        delegates = item["connector"]["spec"]["delegateSelectors"]

        # add cluster to spec
        configs["kubernetes"]["clusterLocatorMethods"][0]["clusters"].append(
            {
                "name": id,
                "url": url,
                "authProvider": "serviceAccount",
                "skipTLSVerify": True,
                "skipMetricsLookup": False,
                "serviceAccountToken": f"${{{secret}}}",
            }
        )

        # add secret to env
        env_variables.append(
            {
                "env_name": secret,
                "type": "Secret",
                "harness_secret_identifier": f"account.{secret}",
                "is_deleted": False,
                # need to find out how this is generated
                "identifier": "670ff76e7716cd0116dd5281",
            }
        )

        # use delegate for connections
        proxy.append(
            {
                "host": url,
                "proxy": True,
                "selectors": delegates,
                "pluginId": "kubernetes",
                # need to find out how this is generated
                "identifier": "670fe8a8ffc2587c02314289",
            }
        )

        print(f"added {id}")

    print(dump(configs))
    resp = post(
        f"https://{HARNESS_URL}/gateway/v1/app-config",
        headers=HEADERS,
        params={"account": HEADERS["Harness-Account"]},
        json={
            "app_config": {
                "config_id": "kubernetes",
                "config_name": "Kubernetes",
                "enabled": True,
                "configs": dump(configs, default_flow_style=False),
                "env_variables": env_variables,
                "proxy": proxy,
            }
        },
    )

    resp.raise_for_status()

    return resp.text


if __name__ == "__main__":
    print(main())

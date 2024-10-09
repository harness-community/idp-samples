from os import getenv

from requests import get

HARNESS_URL = getenv("HARNESS_URL", "app.harness.io")

HEADERS = {
    "Harness-Account": getenv("HARNESS_ACCOUNT_ID"),
    "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
}

API_LIMIT = int(getenv("API_LIMIT", 1))


def get_orgs(page: int = 0) -> list:
    resp = get(
        f"https://{HARNESS_URL}/v1/orgs",
        headers=HEADERS,
        params={"page": page, "limit": API_LIMIT},
    )

    resp.raise_for_status()

    data = resp.json()

    if (page + 1) < int(resp.headers.get("X-Total-Elements")):
        data.extend(get_orgs(page + 1))

    return data


def get_projects(org: str, page: int = 0) -> list:
    resp = get(
        f"https://{HARNESS_URL}/v1/orgs/{org}/projects",
        headers=HEADERS,
        params={"page": page, "limit": API_LIMIT},
    )

    resp.raise_for_status()

    data = resp.json()

    if (page + 1) < int(resp.headers.get("X-Total-Elements")):
        data.extend(get_projects(org, page + 1))

    return data


def get_all_projects():
    data = []

    for org in get_orgs():
        data.extend(get_projects(org=org["org"]["identifier"]))

    return data


def get_services(org: str, project: str, page: int = 0) -> list:
    resp = get(
        f"https://{HARNESS_URL}/v1/orgs/{org}/projects/{project}/services",
        headers=HEADERS,
        params={"page": page, "limit": API_LIMIT},
    )

    resp.raise_for_status()

    data = resp.json()

    if (page + 1) < int(resp.headers.get("X-Total-Elements")):
        data.extend(get_services(org, project, page + 1))

    return data


def get_all_services() -> list:
    data = []

    for project in get_all_projects():
        data.extend(
            get_services(project["project"]["org"], project["project"]["identifier"])
        )

    return data

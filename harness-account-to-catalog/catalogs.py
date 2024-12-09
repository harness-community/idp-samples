from os import getenv

from jinja2 import Environment, PackageLoader, select_autoescape

OWNER = getenv("OWNER", "default/admins")

JINJA_ENV = Environment(
    loader=PackageLoader("catalogs"), autoescape=select_autoescape()
)


def generate_org_yaml(name: str, description: str, owner: str):
    template = JINJA_ENV.get_template("org.yaml.j2")

    return template.render(name=name, description=description, owner=owner)


def generate_project_yaml(
    harness_url: str,
    harness_account_id: str,
    name: str,
    org: str,
    description: str,
    owner: str,
):
    template = JINJA_ENV.get_template("project.yaml.j2")

    return template.render(
        harness_url=harness_url,
        harness_account_id=harness_account_id,
        name=name,
        org=org,
        description=description,
        owner=owner,
    )


def generate_service_yaml(
    harness_url: str,
    harness_account_id: str,
    name: str,
    description: str,
    org: str,
    project: str,
    owner: str,
    type: str = "service",
):
    template = JINJA_ENV.get_template("service.yaml.j2")

    return template.render(
        harness_url=harness_url,
        harness_account_id=harness_account_id,
        name=name,
        org=org,
        project=project,
        description=description,
        owner=owner,
        type=type,
    )


def generate_location_yaml(repo: str, branch: str, catalogs: list):
    template = JINJA_ENV.get_template("locations.yaml.j2")

    return template.render(repo=repo, branch=branch, catalogs=catalogs)

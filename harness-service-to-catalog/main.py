from os import getenv, mkdir, path

from harness import (
    get_orgs,
    get_projects,
    get_services,
)
from catalogs import generate_org_yaml, generate_project_yaml, generate_service_yaml


OWNER = getenv("OWNER", "default/admins")


def create_dir(name: str) -> str:
    try:
        mkdir(name)
    except FileExistsError:
        return name
    except Exception as e:
        raise (e)
    else:
        return name


def main():
    for org in get_orgs():
        org_identifier = org["org"]["identifier"]

        dir_name = create_dir(org_identifier)

        with open(f"{dir_name}/_domain.yaml", "w") as output:
            output.write(
                generate_org_yaml(org_identifier, org["org"]["description"], OWNER)
            )

        for proj in get_projects(org["org"]["identifier"]):
            proj_identifier = proj["project"]["identifier"]

            dir_name = create_dir(f"{org_identifier}/{proj_identifier}")

            with open(f"{dir_name}/_system.yaml", "w") as output:
                output.write(
                    generate_project_yaml(
                        proj_identifier,
                        org_identifier,
                        proj["project"]["description"],
                        OWNER,
                    )
                )

                for service in get_services(org_identifier, proj_identifier):
                    output_file = f"{dir_name}/{service['service']['identifier']}.yaml"

                    if not path.exists(output_file):
                        with open(output_file, "w") as output:
                            output.write(
                                generate_service_yaml(
                                    service["service"]["identifier"],
                                    service["service"]["description"],
                                    proj_identifier,
                                    OWNER,
                                )
                            )


if __name__ == "__main__":
    main()

from os import getenv, mkdir, path
from sys import argv
from argparse import ArgumentParser, Namespace

from harness import get_orgs, get_projects, get_services, HARNESS_URL, HEADERS
from catalogs import (
    generate_org_yaml,
    generate_project_yaml,
    generate_service_yaml,
    generate_location_yaml,
)


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


def main(args: Namespace):
    # create parent dir if specified
    if directory := (args.dir or getenv("DIR")):
        target_dir_name = create_dir(directory) + "/"
    else:
        target_dir_name = ""

    # keep track of all newly created catalogs
    created_items = []

    for org in get_orgs():
        org_identifier = org["org"]["identifier"]

        # create dir for this organization
        org_dir_name = create_dir(f"{target_dir_name}{org_identifier}")
        org_file_name = f"{org_dir_name}/_domain.yaml"

        # create the domain if not already existing
        if not path.isfile(org_file_name):
            with open(org_file_name, "w") as output:
                output.write(
                    generate_org_yaml(org_identifier, org["org"]["description"], OWNER)
                )
            print(org_file_name)
            created_items.append(org_file_name)

        for proj in get_projects(org["org"]["identifier"]):
            proj_identifier = proj["project"]["identifier"]

            # create dir for this project
            proj_dir_name = create_dir(f"{org_dir_name}/{proj_identifier}")
            proj_file_name = f"{proj_dir_name}/_system.yaml"

            # create the system if not already existing
            if not path.isfile(proj_file_name):
                with open(proj_file_name, "w") as output:
                    output.write(
                        generate_project_yaml(
                            HARNESS_URL,
                            HEADERS.get("Harness-Account"),
                            proj_identifier,
                            org_identifier,
                            proj["project"]["description"],
                            OWNER,
                        )
                    )
                print(proj_file_name)
                created_items.append(proj_file_name)

                for service in get_services(org_identifier, proj_identifier):
                    output_file = (
                        f"{proj_dir_name}/{service['service']['identifier']}.yaml"
                    )

                    if not path.exists(output_file):
                        with open(output_file, "w") as output:
                            output.write(
                                generate_service_yaml(
                                    HARNESS_URL,
                                    HEADERS.get("Harness-Account"),
                                    service["service"]["identifier"],
                                    service["service"]["description"],
                                    org_identifier,
                                    proj_identifier,
                                    OWNER,
                                )
                            )
                        print(output_file)
                        created_items.append(output_file)

    # create or update locations file
    if repo := (args.repo or getenv("REPO")):
        location = target_dir_name + (getenv("LOCATION") or args.location)
        branch = args.branch or getenv("BRANCH", "main")
        if not path.isfile(location):
            with open(location, "w") as output:
                output.write(generate_location_yaml(repo, branch, created_items))
            print(location)
        else:
            with open(location, "a") as output:
                for item in created_items:
                    output.write(f"\n  - {repo}/blob/{branch}/{item}")
            print(f"updated: {location}")


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="harness-account-to-catalog",
        description="Generate IDP domains, systems and components from your Harness structure",
    )

    # parent directory for catalog yamls
    parser.add_argument("-d", "--dir")
    # current git repo url to generate location yaml
    parser.add_argument("-r", "--repo")
    # branch in git
    parser.add_argument("-b", "--branch")
    # location file to save to
    parser.add_argument("-l", "--location", default="locations.yaml")

    args = parser.parse_args()

    main(args)
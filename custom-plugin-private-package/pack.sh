#!/bin/bash

usage() {
    echo "Usage: $0"
    exit 1
}

run_yarn_command() {
    echo "Running yarn $1..."
    yarn "$1"
    if [ $? -ne 0 ]; then
        echo "yarn $1 failed. Exiting"
        exit 1
    fi
}

prompt_for_input() {
    read -p "$1: " input
    echo "$input"
}

copy_package() {
    local package=$1
    local source_path=$2
    local destination_path=$3

    if [[ $package == @*/* ]]; then
        local scope=$(echo "$package" | cut -d'/' -f1)
        local package_name=$(echo "$package" | cut -d'/' -f2)
        local package_path="$source_path/$scope/$package_name"
    else
        local package_path="$source_path/$package"
    fi

    if [ ! -d "$package_path" ]; then
        echo "Package not found: $package"
        return 1
    fi

    mkdir -p "$destination_path/$(dirname "$package")"
    cp -r "$package_path" "$destination_path/$package"
    echo "Copied $package to $destination_path/$package"
    return 0
}

update_package_json() {
    local package=$1
    local package_json=$2
    jq --arg pkg "$package" '.dependencies[$pkg] = "./" + $pkg' "$package_json" > "$package_json.tmp" && mv "$package_json.tmp" "$package_json"
}

CHILD_RELATIVE_PATH=$(prompt_for_input "Enter the relative path of the child directory")

if [ ! -d "$CHILD_RELATIVE_PATH" ]; then
    echo "Child directory not found: $CHILD_RELATIVE_PATH"
    exit 1
fi

cd "$CHILD_RELATIVE_PATH" || exit

printf "Do you have any private packages? (yes/no): "
read -r has_private_packages

run_yarn_command "tsc"
run_yarn_command "build"

if [[ $has_private_packages == "yes" ]]; then
    cp package.json package_copy.json

    PACKAGE_LIST=$(prompt_for_input "Enter the packages to copy, separated by commas (e.g., package1,package2)")

    IFS=',' read -r -a PACKAGES <<< "$PACKAGE_LIST"

    for PACKAGE in "${PACKAGES[@]}"; do
        if copy_package "$PACKAGE" "../../node_modules" .; then
            update_package_json "$PACKAGE" "package.json"
        fi
    done

    run_yarn_command "pack"

    TAR_NAME=$(ls *.tgz)
    tar -xvf "$TAR_NAME"
    rm -f "$TAR_NAME"

    PACKAGE_DIR="package"

    for PACKAGE in "${PACKAGES[@]}"; do
        if copy_package "$PACKAGE" "." "$PACKAGE_DIR"; then
            echo "Copied $PACKAGE to $PACKAGE_DIR/$PACKAGE"
        fi
    done

    tar -cvf "$TAR_NAME" -C . "$PACKAGE_DIR"

    rm -rf "$PACKAGE_DIR"

    for PACKAGE in "${PACKAGES[@]}"; do
        if [[ $PACKAGE == @*/* ]]; then
            SCOPE=$(echo "$PACKAGE" | cut -d'/' -f1)
            rm -rf "$PWD/$SCOPE"
            echo "Removed copied package directory for scope $SCOPE"
        else
            rm -rf "$PWD/$PACKAGE"
            echo "Removed copied package: $PACKAGE"
        fi
    done

    cp package_copy.json package.json

    rm package_copy.json

    echo "Tarball created: $TAR_NAME"
    echo "All packages processed."
else
    run_yarn_command "pack"
fi

echo "Complete"

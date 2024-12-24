# Custom Plugin Packaging Script

This script automates the process of including private packages hosted in a customer's private registry by copying specified dependencies from the `node_modules` to the plugin directory, updating the `package.json` file with local dependencies, and creating a tarball file for upload in the Custom Plugins tab in IDP Admin.

## Prerequisites

Before running the script, ensure you have the following prerequisites installed on your system:

- **Node.js**: Ensure Node.js is installed on your system. You can download it from [Node.js — Run JavaScript Everywhere](https://nodejs.org/).
- **Yarn**: Yarn is required to manage packages and run commands. You can install Yarn by following the instructions on the [Yarn website](https://classic.yarnpkg.com/en/docs/install).
- **jq**: jq is a lightweight and flexible command-line JSON processor used for updating `package.json`. You can install it using your system's package manager or from the [official website](https://stedolan.github.io/jq/download/).

## Usage

Follow the steps below to use the script:

1. Place this script inside the root of your Backstage App created using Backstage CLI.

2. Run the script: Execute the script by running the following command:

```bash
   ./pack.sh
```

3. The script will ask for a few prompts, please provide the information carefully:

    1. **Enter the relative path of the child directory**: Please enter the relative path of the plugin for which you want to run this script.

    2. **Do you have any private packages? (yes/no)**: Please specify if you have any private packages:

        -   If **no**, the script will run `yarn pack` and create a tarball inside the plugins directory.

        -   If **yes**, the script will ask you to provide the list of packages. Please provide a list of all the packages that are not available in the public npm registry, separated by commas.


4. Once all the details are provided, the script will generate a tarball file inside the plugin directory specified in step 3.1.
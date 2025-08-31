# Project: Notion Template Deployment

## Project Overview

This project is a Notion template for estate planning, called "Estate Planning Concierge v4.0". The template is deployed to a Notion workspace using a Python script that leverages the Notion API. The structure and content of the template are defined in a series of YAML files located in the `split_yaml` directory.

The deployment script (`deploy.py`) is highly configurable and supports features like:

*   **Incremental deployment:** The script can deploy the template in parts, based on the YAML files.
*   **Idempotency:** The script is designed to be run multiple times without causing errors or duplicating content.
*   **Role-based access control:** The template has different views for "owner", "executor", and "family" roles.
*   **Dynamic content:** The script can generate dynamic content like QR codes and progress visualizations.
*   **Asset management:** The script can upload and manage assets like icons and cover images.

## Building and Running

### 1. Setup

The project includes a setup script that helps configure the environment and validate the deployment.

To run the setup script:

```bash
bash setup.sh
```

The script will:

*   Check for a valid Python installation.
*   Install required Python packages (`requests`, `PyYAML`).
*   Prompt you to set the following environment variables:
    *   `NOTION_TOKEN`: Your Notion API token.
    *   `NOTION_PARENT_PAGEID`: The ID of the Notion page where the template will be deployed.

### 2. Deployment Commands

Once the setup is complete, you can use the following commands to deploy the template:

*   **Validate deployment configuration:**

    ```bash
    python3 validate_deployment.py
    ```

*   **Run validation-only check:**

    ```bash
    python3 deploy.py --validate-only --verbose
    ```

*   **Run dry-run test (simulates deployment):**

    ```bash
    python3 deploy.py --dry-run --verbose
    ```

*   **Execute full deployment:**

    ```bash
    python3 deploy.py --verbose
    ```

*   **View help:**
    ```bash
    python3 deploy.py --help
    ```

## Development Conventions

*   **Configuration:** The template is configured using YAML files in the `split_yaml` directory. Each file represents a part of the template, such as pages, databases, or UI elements.
*   **Deployment:** The `deploy.py` script is the single source of truth for deploying the template. It is designed to be modular and extensible.
*   **Idempotency:** The script uses markers to track the deployment of each part of the template, ensuring that the script can be run multiple times without duplicating content.
*   **Roles:** The template uses a role-based access control system to provide different views for different users. The roles are defined in the YAML files and enforced by the deployment script.

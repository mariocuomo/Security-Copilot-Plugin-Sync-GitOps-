"""
Sync script — uploads all changed plugin YAML files to Security Copilot.

Usage (local):
    python sync_plugins.py --plugins-dir plugins

Usage (CI/CD — GitHub Actions):
    Authentication (pick one):
      Option A - Workload Identity Federation (OIDC, no secrets):
        AZURE_TENANT_ID, AZURE_CLIENT_ID
      Option B - Client Secret:
        AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET

    Other env vars:
      SECURITY_COPILOT_REGION  (optional, default: eastus)
      CHANGED_FILES            (optional, comma-separated list of changed files)
"""

import argparse
import glob
import logging
import os
import sys

from azure.identity import DefaultAzureCredential
from security_copilot_client import SecurityCopilotClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("SecurityCopilotSync")


def get_credential():
    """
    Build an Azure credential using DefaultAzureCredential.

    This automatically picks the best available method:
      - In GitHub Actions with OIDC: uses Workload Identity Federation (no secrets!)
      - With AZURE_CLIENT_SECRET set: uses ClientSecretCredential
      - Locally: uses Azure CLI, VS Code, or interactive browser login
    """
    return DefaultAzureCredential()


def discover_plugins(plugins_dir: str, changed_files: str | None = None) -> list[str]:
    """
    Return plugin YAML file paths to sync.

    If `changed_files` is set (comma-separated), only those files under
    `plugins_dir` are returned.  Otherwise ALL yaml/yml files are returned.
    """
    if changed_files:
        paths = [f.strip() for f in changed_files.split(",") if f.strip()]
        # Keep only files that are inside the plugins directory and are YAML
        return [
            p for p in paths
            if p.startswith(plugins_dir) and p.endswith((".yaml", ".yml"))
        ]
    # Full sync — all YAML files in the directory
    return sorted(glob.glob(os.path.join(plugins_dir, "**", "*.yaml"), recursive=True) +
                  glob.glob(os.path.join(plugins_dir, "**", "*.yml"), recursive=True))


def main():
    parser = argparse.ArgumentParser(description="Sync Security Copilot plugins")
    parser.add_argument("--plugins-dir", default="plugins", help="Directory containing plugin YAML files")
    parser.add_argument("--changed-files", default=os.getenv("CHANGED_FILES"), help="Comma-separated changed file paths (from CI)")
    parser.add_argument("--region", default=os.getenv("SECURITY_COPILOT_REGION", "eastus"), help="Security Copilot region")
    args = parser.parse_args()

    files = discover_plugins(args.plugins_dir, args.changed_files)
    if not files:
        logger.info("No plugin files to sync.")
        return

    logger.info(f"Found {len(files)} plugin(s) to sync: {files}")

    credential = get_credential()
    client = SecurityCopilotClient(credential, region=args.region)

    results = {"created": [], "updated": [], "failed": []}

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                yaml_content = f.read()
            result = client.upload_plugin(yaml_content)
            results[result["status"]].append(result["name"])
        except Exception as e:
            logger.error(f"Failed to sync {filepath}: {e}")
            results["failed"].append(filepath)

    # Summary
    logger.info("=== Sync Summary ===")
    logger.info(f"  Created: {results['created']}")
    logger.info(f"  Updated: {results['updated']}")
    logger.info(f"  Failed:  {results['failed']}")

    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

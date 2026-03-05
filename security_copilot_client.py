"""
Simplified Security Copilot client for plugin (skillset) upload/sync.
Designed for CI/CD automation via GitHub Actions.
"""

import requests
import yaml
import logging

logger = logging.getLogger("SecurityCopilotSync")


class SecurityCopilotClient:
    """Minimal client to manage Security Copilot plugins (skillsets)."""

    SCOPE = "https://api.securitycopilot.microsoft.com/.default"

    def __init__(self, credential, base_url="https://api.securitycopilot.microsoft.com", region="eastus"):
        self.credential = credential
        self.base_url = base_url
        self.region = region

    # ── Auth ────────────────────────────────────────────────────────────
    def _headers(self, content_type="application/json"):
        token = self.credential.get_token(self.SCOPE).token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }

    # ── Skillsets (plugins) ─────────────────────────────────────────────
    def list_plugins(self):
        """Return the list of existing plugin names."""
        url = f"{self.base_url}/geo/{self.region}/skillsets"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return [p["name"] for p in resp.json().get("value", [])]

    def upload_plugin(self, yaml_content: str) -> dict:
        """
        Upload or update a plugin in Security Copilot.

        - If the plugin already exists → PUT (update)
        - If it does not exist → POST (create)

        Args:
            yaml_content: Raw YAML string of the plugin descriptor.

        Returns:
            dict with keys: status ("created" | "updated"), name, response
        """
        # Extract plugin name from YAML
        plugin_data = yaml.safe_load(yaml_content)
        plugin_name = plugin_data["Descriptor"]["Name"]
        logger.info(f"Processing plugin: {plugin_name}")

        existing = self.list_plugins()
        headers = self._headers(content_type="application/yaml")
        base = f"{self.base_url}/geo/{self.region}/skillsets"
        qs = "?scope=Tenant&skillsetFormat=SkillsetYaml"

        if plugin_name in existing:
            # Update
            resp = requests.put(f"{base}/{plugin_name}{qs}", data=yaml_content, headers=headers)
            resp.raise_for_status()
            logger.info(f"Plugin '{plugin_name}' updated successfully.")
            return {"status": "updated", "name": plugin_name, "response": resp.json()}
        else:
            # Create
            resp = requests.post(f"{base}{qs}", data=yaml_content, headers=headers)
            resp.raise_for_status()
            logger.info(f"Plugin '{plugin_name}' created successfully.")
            return {"status": "created", "name": plugin_name, "response": resp.json()}

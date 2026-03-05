# Security Copilot Plugin Sync (GitOps)

Manage Microsoft Security Copilot plugins as code.  
Every change to YAML files in the `plugins/` folder is automatically synced via GitHub Actions.

## Repository Structure

```
├── .github/workflows/
│   └── sync-plugins.yml          # GitHub Actions workflow
├── plugins/
│   └── SamplePlugin.yaml         # ← Your plugin YAML files go here
├── security_copilot_client.py     # Simplified upload client
├── sync_plugins.py                # Sync script
├── requirements.txt
└── README.md
```

## How It Works

1. **Add or modify** a `.yaml` file in the `plugins/` folder
2. **Push** to `main`
3. **GitHub Actions** detects the changed files and automatically uploads them to Security Copilot
   - If the plugin **already exists** → it is updated (PUT)
   - If the plugin **does not exist** → it is created (POST)

## Setup

### 1. Register an App in Microsoft Entra ID

The automation uses a **Service Principal** with a client secret to authenticate.

1. **Create an App Registration** in Entra ID (note the Tenant ID and Client ID)
2. Go to **Certificates & secrets → Client secrets → New client secret** and create one
3. Assign permissions to the app:

#### Required Permissions

The app needs two things configured:

**a) API Permission in Entra ID**
1. In the App Registration, go to **API permissions → Add a permission**
2. Select **APIs my organization uses** and search for `Security Copilot` (or `https://api.securitycopilot.microsoft.com`)
3. Add the available application permission
4. Click **Grant admin consent** for the tenant

**b) Role in Security Copilot**
1. Open the Security Copilot portal → **Settings → Role assignments**
2. Add the Service Principal (search by name or Client ID of the app)
3. Assign the **Contributor** role
   - *Contributor* is sufficient for managing plugins/skillsets
   - *Owner* also works but is more permissive than necessary

### 2. Configure GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

| Secret                  | Value                           |
|-------------------------|---------------------------------|
| `AZURE_TENANT_ID`      | Your Azure Tenant ID            |
| `AZURE_CLIENT_ID`      | The app's Client ID             |
| `AZURE_CLIENT_SECRET`  | The app's Client Secret         |

(Optional) Add a **variable** (not a secret):

| Variable                      | Default   |
|-------------------------------|-----------|
| `SECURITY_COPILOT_REGION`     | `eastus`  |

### 3. Add Your Plugins

Create YAML files in the `plugins/` folder. Each file must follow the standard Security Copilot plugin structure:

```yaml
Descriptor:
  Name: MyPlugin
  DisplayName: My Plugin
  Description: Description of my plugin

SkillGroups:
  - Format: KQL
    Skills:
      - Name: MySkill
        DisplayName: My Skill
        Description: What this skill does
        Inputs:
          - Name: Parameter1
            Description: Description of the parameter
            Required: true
        Settings:
          Target: Defender
          Template: |-
            // Your KQL query here
```

## Local Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."

# Sync all plugins
python sync_plugins.py --plugins-dir plugins

# Sync specific files
python sync_plugins.py --plugins-dir plugins --changed-files "plugins/MyPlugin.yaml"
```

## Manual Trigger

You can also run the sync manually from GitHub:  
**Actions → Sync Security Copilot Plugins → Run workflow**

This performs a **full sync** of all plugins in the folder.

# Teams App Deployment

Two Teams Tab Apps that embed the ISD Chat assistants running on Azure Container Apps.

| App | ACA URL | Package |
|-----|---------|---------|
| **Seller** | `isd-chat-seller-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io` | `isd-seller-teams-app.zip` |
| **Customer** | `isd-chat-customer-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io` | `isd-customer-teams-app.zip` |

## Prerequisites

- Microsoft Teams admin or sideloading enabled for your tenant
- The ACA frontend apps must be running (verify at the URLs above)

## Build Packages

```bash
cd teams-apps
bash package.sh
```

This creates two `.zip` files, each containing `manifest.json`, `color.png`, and `outline.png`.

## Install via Sideloading (Dev/Test)

1. Open **Microsoft Teams** → click **Apps** (left sidebar)
2. Click **Manage your apps** → **Upload an app**
3. Select **Upload a custom app**
4. Choose `isd-seller-teams-app.zip` or `isd-customer-teams-app.zip`
5. Click **Add** to install

## Install via Teams Admin Center (Production)

1. Go to [Teams Admin Center](https://admin.teams.microsoft.com)
2. Navigate to **Teams apps** → **Manage apps**
3. Click **Upload new app** → select the `.zip` file
4. Configure app policies to control who can access it

## Troubleshooting

### Blank Tab / "Refused to connect"

The ACA frontend must allow being embedded in an iframe. If Teams shows a blank tab, add these response headers to the frontend container:

```
X-Frame-Options: ALLOW-FROM https://teams.microsoft.com
Content-Security-Policy: frame-ancestors 'self' https://teams.microsoft.com https://*.teams.microsoft.com
```

This can be set in the frontend's web server config (nginx/caddy) or as ACA ingress custom headers.

### App Not Loading

- Confirm the ACA app is running: `curl -s https://<frontend-url>/`
- Check ACA logs in the Azure Portal under Container Apps → isd-chat-*-frontend → Log stream

## Customization

- Replace `color.png` (192×192) and `outline.png` (32×32) with proper branded icons
- Update `manifest.json` fields (`name`, `description`, `developer`) as needed
- Generate real GUIDs for `id` in each manifest before production use

# Gradio Frontend Version Control

## Current Baseline: v1.0-baseline

**Created:** 2025-11-11  
**Image Digest:** `sha256:3c3aef462c83f32f40985844549960f3b3f06582643b0b90e78c7eee1df1bf84`  
**Status:** ✅ Stable - All features working correctly

### Features in v1.0-baseline
- Gradio 5.49.1 chat interface with streaming responses
- Example prompt buttons with proper generator delegation
- SSE-based backend communication
- Backend health monitoring
- Session ID management
- Proper error handling for backend connectivity
- Styled chat UI with Microsoft branding

### Known Working State
- Example buttons: ✅ Working (uses `yield from` delegation)
- Streaming responses: ✅ Working (SSE from backend)
- Backend connectivity: ✅ Working (private VNet endpoint)
- Session management: ✅ Working (UUID-based sessions)

---

## Version History

### v1.0-baseline (Current Stable)
- **Tag:** `v1.0-baseline`
- **Tag:** `latest` (also points to this version)
- **ACR Image:** `indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio:v1.0-baseline`
- **Key Changes:**
  - Initial working Gradio implementation
  - Fixed generator delegation for example buttons
  - Proper module-level `create_example_handler()` function
  - Removed unnecessary session management in ChatClient
  - Confirmed working deployment to Azure Container Apps

---

## Deployment Procedures

### Deploy Current Baseline
```bash
# Deploy the stable v1.0-baseline version
BACKEND_FQDN=$(az containerapp show \
  --name indsolse-dev-backend-v2-vnet \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp update \
  --name indsolse-dev-frontend-gradio \
  --resource-group indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio:v1.0-baseline \
  --set-env-vars "BACKEND_API_URL=https://$BACKEND_FQDN"
```

### Deploy Latest Development Version
```bash
# Deploy whatever is tagged as "latest"
BACKEND_FQDN=$(az containerapp show \
  --name indsolse-dev-backend-v2-vnet \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp update \
  --name indsolse-dev-frontend-gradio \
  --resource-group indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio:latest \
  --set-env-vars "BACKEND_API_URL=https://$BACKEND_FQDN"
```

### Rollback to Baseline
If new changes cause issues, instantly rollback:
```bash
# Quick rollback to stable baseline
BACKEND_FQDN=$(az containerapp show \
  --name indsolse-dev-backend-v2-vnet \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp update \
  --name indsolse-dev-frontend-gradio \
  --resource-group indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio:v1.0-baseline \
  --set-env-vars "BACKEND_API_URL=https://$BACKEND_FQDN"

# Force restart to ensure new image loads
az containerapp revision restart \
  --name indsolse-dev-frontend-gradio \
  --resource-group indsolse-dev-rg \
  --revision $(az containerapp revision list \
    --name indsolse-dev-frontend-gradio \
    --resource-group indsolse-dev-rg \
    --query '[0].name' -o tsv)
```

---

## Versioning Strategy for Future Updates

### Creating New Versions
When making improvements or changes:

1. **Make code changes** to `gradio_app.py` or other frontend files
2. **Build and tag as latest:**
   ```bash
   cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-gradio
   az acr build --registry indsolsedevacr \
     --image industry-solutions-frontend-gradio:latest \
     --file Dockerfile .
   ```

3. **Deploy and test** the latest version:
   ```bash
   # Use "Deploy Latest Development Version" command above
   ```

4. **If successful, create a new version tag:**
   ```bash
   # Example: Creating v1.1
   az acr import \
     --name indsolsedevacr \
     --source indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio:latest \
     --image industry-solutions-frontend-gradio:v1.1 \
     --force
   ```

5. **If unsuccessful, rollback:**
   ```bash
   # Use "Rollback to Baseline" command above
   # OR rollback to any specific version:
   az containerapp update \
     --name indsolse-dev-frontend-gradio \
     --resource-group indsolse-dev-rg \
     --image indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio:v1.0-baseline
   ```

### Recommended Version Numbering
- **v1.0-baseline:** Current stable version (this)
- **v1.1:** Minor feature additions (e.g., new UI element, styling change)
- **v1.2:** Additional minor improvements
- **v2.0:** Major architectural changes or breaking changes

### Tag Management
```bash
# List all available versions
az acr repository show-tags \
  --name indsolsedevacr \
  --repository industry-solutions-frontend-gradio \
  --output table

# Delete a tag (if needed)
az acr repository delete \
  --name indsolsedevacr \
  --image industry-solutions-frontend-gradio:TAG_NAME \
  --yes
```

---

## Container App Configuration

**Container App Name:** `indsolse-dev-frontend-gradio`  
**Resource Group:** `indsolse-dev-rg`  
**Environment:** `indsolse-dev-env`  
**Current URL:** `https://indsolse-dev-frontend-gradio.redplant-675b33da.swedencentral.azurecontainerapps.io`

**Backend Connection:**
- **Service:** `indsolse-dev-backend-v2-vnet`
- **URL:** `https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io`
- **Environment Variable:** `BACKEND_API_URL`

---

## Testing After Deployment

After deploying any version, verify functionality:

1. **Access the UI:** https://indsolse-dev-frontend-gradio.redplant-675b33da.swedencentral.azurecontainerapps.io
2. **Test example buttons:** Click each example prompt
3. **Test manual input:** Type a custom question
4. **Check streaming:** Verify responses stream word-by-word
5. **Check backend status:** Look for green checkmark in UI
6. **Check session ID:** Verify session ID displays correctly

---

## Emergency Procedures

### If the app won't start:
```bash
# Check logs
az containerapp logs show \
  --name indsolse-dev-frontend-gradio \
  --resource-group indsolse-dev-rg \
  --tail 100

# Check revision status
az containerapp revision list \
  --name indsolse-dev-frontend-gradio \
  --resource-group indsolse-dev-rg \
  --output table
```

### If example buttons break:
- Likely generator delegation issue
- Rollback to v1.0-baseline immediately
- Review `create_example_handler()` implementation

### If backend connection fails:
- Check backend health: `https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io/api/health`
- Verify environment variable: `BACKEND_API_URL`
- Check VNet connectivity between Container Apps

---

## Backup Information

**ACR Repository:** `indsolsedevacr.azurecr.io/industry-solutions-frontend-gradio`  
**Baseline Image Digest:** `sha256:3c3aef462c83f32f40985844549960f3b3f06582643b0b90e78c7eee1df1bf84`  
**Source Code Location:** `/Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-gradio/`

### Critical Files
- `gradio_app.py` - Main application logic
- `Dockerfile` - Container image definition
- `requirements.txt` - Python dependencies
- `README.md` - Deployment and usage documentation

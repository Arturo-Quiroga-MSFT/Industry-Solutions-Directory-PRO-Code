cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react

# 1. Remove .env file (critical!)
mv .env .env.local.backup 2>/dev/null || echo "No .env to remove"

# 2. Build frontend with backend URL
az acr build \
  --registry indsolsedevacr \
  --image isd-frontend-seller:v2.6-jan2026 \
  --file Dockerfile \
  --build-arg VITE_API_URL=https://isd-chat-seller-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io \
  .

# 3. Deploy frontend
az containerapp create \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/isd-frontend-seller:v2.6-jan2026 \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.25 \
  --memory 0.5Gi

# 4. Configure ACR authentication
az containerapp registry set \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --server indsolsedevacr.azurecr.io \
  --username indsolsedevacr \
  --password $(az acr credential show --name indsolsedevacr --query 'passwords[0].value' -o tsv)

# 5. Get frontend URL
az containerapp show \
  --name isd-chat-seller-frontend \
  --resource-group indsolse-dev-rg \
  --query properties.configuration.ingress.fqdn -o tsv
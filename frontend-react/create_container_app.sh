# Create Container App
az containerapp create \
  --name isd-chat-seller-backend \
  --resource-group indsolse-dev-rg \
  --environment indsolse-dev-env \
  --image indsolsedevacr.azurecr.io/isd-backend-seller:v2.6 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    APP_MODE=seller \
    AZURE_OPENAI_API_KEY='<your-azure-openai-api-key-here>' \
    AZURE_OPENAI_ENDPOINT=https://aq-ai-foundry-sweden-central.openai.azure.com/ \
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4.1 \
    SQL_SERVER=mssoldir-prd-sql.database.windows.net \
    SQL_DATABASE=mssoldir-prd \
    SQL_USERNAME=isdapi_dev \
    SQL_PASSWORD='<your-sql-password-here>' \
    ALLOWED_ORIGINS=http://localhost:5173
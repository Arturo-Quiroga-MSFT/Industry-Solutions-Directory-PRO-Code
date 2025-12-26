lsof -ti:8000 | xargs kill -9 2>/dev/null 

cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react/backend && export AZURE_OPENAI_API_KEY="10e15f18e77c44b6bf97c638d7d9253e" && export AZURE_OPENAI_ENDPOINT="https://aq-ai-foundry-sweden-central.openai.azure.com/" && export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1" && export SQL_SERVER="mssoldir-prd-sql.database.windows.net" && export SQL_DATABASE="Solutions" && export SQL_USERNAME="sa-mssoldir-prd-sql" && export SQL_PASSWORD="DZ!8Qt&Dx2PjAxf7" && export APP_MODE="seller" && export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173" && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react && npm run dev
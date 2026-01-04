# Build and push Docker image
cd frontend-react/backend
az acr build \
  --registry indsolsedevacr \
  --image isd-backend-seller:v2.6 \
  --file Dockerfile \
  .


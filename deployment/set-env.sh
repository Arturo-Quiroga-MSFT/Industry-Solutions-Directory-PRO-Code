#!/bin/bash
# Environment Variables for ISD Chat Deployment
# Source this file: source ./set-env.sh

export AZURE_OPENAI_API_KEY='<your-azure-openai-api-key>'
export AZURE_OPENAI_ENDPOINT='https://aq-ai-foundry-sweden-central.openai.azure.com/'
export AZURE_OPENAI_CHAT_DEPLOYMENT_NAME='gpt-4.1'
export SQL_PASSWORD='<your-sql-password>'

echo "✅ Environment variables set:"
echo "   AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT"
echo "   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: $AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
echo "   AZURE_OPENAI_API_KEY: [hidden]"
echo "   SQL_PASSWORD: [hidden]"

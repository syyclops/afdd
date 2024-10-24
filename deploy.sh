#!/bin/bash

# Example run
# ./deploy.sh afdd-rg afdd-aci afddacr afdd-app "postgres://user:password@host:port/db" "bolt://host:port"

# Check if the correct number of arguments is provided
if [ "$#" -ne 6 ]; then
  echo "Usage: $0 <resource-group> <aci-name> <acr-name> <image-name> <postgres-connection-string> <neo4j-url>"
  exit 1
fi

# Set variables from input arguments
RESOURCE_GROUP=$1
ACI_NAME=$2
ACR_NAME=$3
IMAGE_NAME=$4
POSTGRES_CONNECTION_STRING=$5
NEO4J_URL=$6

# Azure login
# echo "Logging in to Azure..."
# az login

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create --name $RESOURCE_GROUP --location eastus

# Build Docker image locally
echo "Building Docker image..."
docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME --platform linux/amd64 .

# Push the image to Azure Container Registry (ACR)
echo "Logging in to ACR..."
az acr login --name $ACR_NAME

echo "Pushing image to ACR..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv)

# Create ACI instance
echo "Deploying container to Azure Container Instances..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --environment-variables POSTGRES_CONNECTION_STRING=$POSTGRES_CONNECTION_STRING NEO4J_URL=$NEO4J_URL \
  --cpu 1 --memory 2 \
  --dns-name-label $ACI_NAME \
  --ports 80 \
  --restart-policy Never

echo "Deployment complete. ACI DNS Name: $ACI_NAME.eastus.azurecontainer.io"

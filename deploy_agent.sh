#!/bin/bash
# deploy_agent.sh - Provision Vertex AI Agent Builder, enable APIs, and bind IAM Roles

set -euo pipefail

# 1. Load Local Environment Configuration
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading project variables from $ENV_FILE..."
    # Export vars, ignoring comments and blank lines
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Fallback values
PROJECT_ID=${VERTEX_AI_PROJECT_ID:-""}
LOCATION=${VERTEX_AI_LOCATION:-"us-central1"}
SERVICE_ACCOUNT=${VERTEX_AI_SERVICE_ACCOUNT:-""}

echo "========================================================="
echo "   Vertex AI Agent Pipeline Provisioning Script          "
echo "========================================================="

# 2. Check gcloud installation
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed or not in PATH."
    echo "Please install the Google Cloud SDK and try again."
    exit 1
fi

# 3. Check active GCP project
if [ -z "$PROJECT_ID" ]; then
    echo "Warning: VERTEX_AI_PROJECT_ID is not configured in .env."
    # Try reading current gcloud config
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
        echo "Error: No Google Cloud Project ID detected. Please configure VERTEX_AI_PROJECT_ID."
        exit 1
    fi
fi

echo "Target Google Cloud Project: $PROJECT_ID"
echo "Target Location: $LOCATION"

# 4. Enable Google Cloud APIs
echo "Enabling necessary Google Cloud API services..."
gcloud services enable \
    discoveryengine.googleapis.com \
    aiplatform.googleapis.com \
    --project="$PROJECT_ID"

echo "API services successfully enabled."

# 5. Bind IAM Roles to Service Account
if [ -n "$SERVICE_ACCOUNT" ]; then
    echo "Configuring IAM role bindings for Service Account: $SERVICE_ACCOUNT"
    
    # Bind Vertex AI User role
    echo "Binding roles/aiplatform.user..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/aiplatform.user" \
        --quiet
        
    # Bind Agent Builder / Discovery Engine Admin role
    echo "Binding roles/discoveryengine.admin..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/discoveryengine.admin" \
        --quiet

    echo "IAM role bindings successfully configured."
else
    echo "No Service Account specified (VERTEX_AI_SERVICE_ACCOUNT is blank). Skipping role bindings."
    echo "Ensure your application environment credentials have the appropriate Vertex AI permissions."
fi

# 6. Provisioning Vertex AI Search Data Store Reference
# Note: Agent Builder Data Store creation is usually performed via the Google Cloud Console 
# (https://console.cloud.google.com/gen-app-builder) or via Alpha SDK.
echo ""
echo "========================================================="
echo " Provisioning Instructions for Vertex AI Agent & Stores: "
echo "========================================================="
echo "1. Go to the Vertex AI Agent Builder Console:"
echo "   https://console.cloud.google.com/gen-app-builder/engines?project=$PROJECT_ID"
echo "2. Click 'Create App' -> Select 'Chat' or 'Search'."
echo "3. Specify the name: '401k-crm-compliance-copilot'."
echo "4. Under 'Data Stores', link your target PDF/HTML ERISA sources."
echo "5. For API-based access, configure your Client credentials with roles/aiplatform.user."
echo "========================================================="
echo "Agent deployment configuration complete!"

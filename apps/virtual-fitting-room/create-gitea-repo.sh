#!/bin/bash

# Gitea Repository Creator for Virtual Fitting Room
# Run this script to create the repository on Gitea server

echo "🔧 Gitea Repository Setup"
echo "========================="
echo ""

GITEA_URL="http://192.168.10.35:3000"
REPO_NAME="virtual-fitting-room"
REPO_OWNER="maj"

echo "📋 Repository Information:"
echo "   Name: $REPO_NAME"
echo "   Owner: $REPO_OWNER"
echo "   Gitea: $GITEA_URL"
echo ""

# Check if we have API token
if [ -z "$GITEA_TOKEN" ]; then
    echo "⚠️  GITEA_TOKEN environment variable not set"
    echo ""
    echo "📝 Manual Steps:"
    echo "   1. Open: $GITEA_URL"
    echo "   2. Login as: $REPO_OWNER"
    echo "   3. Click '+' → New Repository"
    echo "   4. Repository Name: $REPO_NAME"
    echo "   5. Description: Virtual Fitting Room - AI-Powered Try-On with CatVTON"
    echo "   6. Visibility: Private (or Public)"
    echo "   7. Click 'Create Repository'"
    echo ""
    echo "🔑 OR set API token:"
    echo "   export GITEA_TOKEN='your-gitea-api-token'"
    echo "   Then run this script again"
    echo ""
    exit 1
fi

echo "🚀 Creating repository via API..."

# Create repository via API
RESPONSE=$(curl -s -X POST "$GITEA_URL/api/v1/user/repos" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"Virtual Fitting Room v1.0 - AI-Powered Virtual Try-On with CatVTON\",
    \"private\": false,
    \"auto_init\": false,
    \"default_branch\": \"main\"
  }")

# Check if successful
if echo "$RESPONSE" | grep -q "\"name\":\"$REPO_NAME\""; then
    echo "✅ Repository created successfully!"
    echo ""
    echo "📦 Repository URL: $GITEA_URL/$REPO_OWNER/$REPO_NAME"
    echo ""
    echo "🔗 Git remote already configured:"
    echo "   gitea: ssh://git@192.168.10.35:2222/$REPO_OWNER/$REPO_NAME.git"
    echo ""
    echo "📤 Now pushing code..."
    git push gitea main

    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Success! Code pushed to Gitea!"
        echo "   View at: $GITEA_URL/$REPO_OWNER/$REPO_NAME"
    else
        echo ""
        echo "❌ Push failed. Check SSH keys and permissions."
    fi
else
    echo "❌ Failed to create repository"
    echo "Response: $RESPONSE"
    echo ""
    echo "Please create manually at: $GITEA_URL"
fi

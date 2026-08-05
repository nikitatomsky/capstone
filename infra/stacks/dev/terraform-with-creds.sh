#!/bin/bash
# Helper script to run Terraform with current AWS session credentials
# This solves the issue where AWS CLI works but Terraform can't find credentials

set -e

# Clear any old AWS environment variables that might be expired
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE

# Get current AWS credentials from AWS CLI session
echo "Exporting AWS credentials from current session..."

CREDS=$(aws configure export-credentials --format env-no-export 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$CREDS" ]; then
    echo "ERROR: Could not get AWS credentials from current session"
    echo "Make sure you're logged in with: aws sts get-caller-identity"
    exit 1
fi

# Parse credentials and export explicitly
export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | grep AWS_ACCESS_KEY_ID | cut -d'=' -f2-)
export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | grep AWS_SECRET_ACCESS_KEY | cut -d'=' -f2-)
export AWS_SESSION_TOKEN=$(echo "$CREDS" | grep AWS_SESSION_TOKEN | cut -d'=' -f2-)
export AWS_DEFAULT_REGION=$(aws configure get region)

echo "✓ AWS credentials exported"
echo "  Account: $(aws sts get-caller-identity --query Account --output text)"
echo "  User: $(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)"
echo ""
echo "Debug: Exported variables:"
echo "  AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:20}..."
echo "  AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:20}..."
echo "  AWS_SESSION_TOKEN: ${AWS_SESSION_TOKEN:0:50}..."
echo ""

# Run terraform command
if [ $# -eq 0 ]; then
    echo "Usage: ./terraform-with-creds.sh <terraform-command>"
    echo "Example: ./terraform-with-creds.sh plan"
    echo "Example: ./terraform-with-creds.sh apply"
    exit 1
fi

echo "Running: terraform $@"
terraform "$@"

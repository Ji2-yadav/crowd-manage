#!/bin/bash
# Deploy frontend static files to Google Cloud Storage
BUCKET_NAME=drishti-frontend-$(date +%s)
gsutil mb -l us-central1 gs://$BUCKET_NAME
gsutil rsync -R . gs://$BUCKET_NAME
# Make files public
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
# Print bucket URL
echo "Frontend deployed to: https://storage.googleapis.com/$BUCKET_NAME/index.html"

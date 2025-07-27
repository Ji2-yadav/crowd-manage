# GCP Deployment Steps for Project Drishti

## 1. Backend (Python) - Cloud Run
1. Go to `simulator/backend`.
2. Build and deploy with:
   ```sh
   gcloud builds submit --tag gcr.io/PROJECT_ID/drishti-backend
   gcloud run deploy drishti-backend --image gcr.io/PROJECT_ID/drishti-backend --platform managed --region us-central1 --allow-unauthenticated
   ```
   Replace `PROJECT_ID` with your GCP project ID.
3. Note the backend URL from Cloud Run output.

## 2. Frontend (HTML/JS/CSS) - Cloud Storage
1. Go to `simulator/frontend`.
2. Run:
   ```sh
   bash deploy.sh
   ```
3. The script will print the public URL for your frontend.

## 3. (Optional) Use Cloud CDN for faster delivery
- In GCP Console, set up Cloud CDN for your storage bucket.

## 4. Connect Frontend to Backend
- Update your frontend JS (`app.js`) to use the Cloud Run backend URL.

## 5. (Optional) App Engine Alternative
- You can deploy backend using App Engine with `app.yaml`.

## 6. Clean Up
- Delete resources when done to avoid charges.

---
For more details, see GCP docs: https://cloud.google.com/docs

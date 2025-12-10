# 📋 Streamlit Cloud Gmail Setup Guide

## Problem
Gmail status showing "Gmail: Offline (No Secrets)" on Streamlit Cloud

## Solution
Configure Gmail OAuth token in Streamlit Cloud Secrets

## Step-by-Step Instructions

### 1. Go to Streamlit Cloud Dashboard
- Visit: https://share.streamlit.io/
- Select your app: **PrimeLine-CRM**
- Click **Settings** (⚙️) → **Secrets**

### 2. Copy This Format to Secrets

```toml
# Google Gemini API Key (REQUIRED for AI features)
GEMINI_API_KEY = "AIzaSyAD0aTHqmURI7i--_IwUkK3UqpBtgEAaiw"

# Gmail OAuth Token (For Email Features)
# Copy values from your local token.json file
[gmail_token]
token = "ya29.___YOUR_ACCESS_TOKEN_HERE___"
refresh_token = "1//__YOUR_REFRESH_TOKEN_HERE___"
token_uri = "https://oauth2.googleapis.com/token"
client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "GOCSPX-___YOUR_CLIENT_SECRET___"
scopes = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"]
universe_domain = "googleapis.com"
account = ""
expiry = "2025-12-31T23:59:59Z"
```

### 3. Get Your Gemini API Key
- Go to: https://aistudio.google.com/app/apikey
- Create or copy your API key
- Replace `YOUR_GEMINI_API_KEY_HERE` with your actual key

### 4. Gmail Token Already Included
The Gmail token above is from your local `token.json` file.
This will work as long as:
- The token hasn't expired
- You don't revoke access in Google Account settings

### 5. Save and Deploy
- Click **Save** button in Streamlit Cloud
- Your app will automatically restart
- Gmail status should change to: **"Gmail: Connected"** ✅

## Troubleshooting

### If Gmail Still Shows Offline:
1. Check if token is expired
2. Run app locally to regenerate `token.json`
3. Update secrets with new token

### If AI Engine Still Shows Offline:
1. Verify Gemini API key is correct
2. Check key starts with "AIza..."
3. Ensure no extra spaces in secrets.toml

## Important Notes
- Never commit secrets to Git
- Token needs refresh every ~7 days (automatically handled)
- If token expires, regenerate locally and update secrets

---

**Created:** 2025-12-10  
**For:** PrimeLine CRM Streamlit Cloud Deployment

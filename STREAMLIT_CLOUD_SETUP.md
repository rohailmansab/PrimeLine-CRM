# 🚀 Quick Fix: Gmail "Offline (No Secrets)" on Streamlit Cloud

## Problem
Your app shows **"Gmail: Offline (No Secrets)"** when deployed on Streamlit Cloud.

## ✅ Solution (5 Minutes)

### Step 1: Open Your Local `token.json`
The file is in your project directory: `/media/rohail/e03bc025-2b57-455f-ac6e-e41790f8a3f6/home/rohail/PrimeLine-CRM-main/token.json`

### Step 2: Go to Streamlit Cloud
1. Visit: **https://share.streamlit.io/**
2. Find your app: **PrimeLine-CRM**
3. Click **Settings** (⚙ icon) → **Secrets**

### Step 3: Paste This in Secrets Box

```toml
# Gemini API Key (Required for AI features)
GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_KEY"

# Gmail Token (Copy from your local token.json file)
[gmail_token]
token = "PASTE_TOKEN_VALUE_HERE"
refresh_token = "PASTE_REFRESH_TOKEN_VALUE_HERE"
token_uri = "https://oauth2.googleapis.com/token"
client_id = "PASTE_CLIENT_ID_HERE"
client_secret = "PASTE_CLIENT_SECRET_HERE"
scopes = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"]
universe_domain = "googleapis.com"
account = ""
expiry = "2025-12-31T23:59:59Z"
```

### Step 4: Fill in the Values

**From `.env` file:**
- Replace `YOUR_ACTUAL_GEMINI_KEY` with your Gemini API key

**From `token.json` file** (open it and copy values):
- `token` → Copy the `"token"` value
- `refresh_token` → Copy the `"refresh_token"` value  
- `client_id` → Copy the `"client_id"` value
- `client_secret` → Copy the `"client_secret"` value

### Step 5: Save
Click **Save** button in Streamlit Cloud. Your app will restart automatically.

## ✅ Expected Result
After saving secrets, your app status should show:
- ✅ **Gmail: Connected**
- ✅ **AI Engine: Online**  
- ✅ **Database: Connected**

## 📝 Example (DO NOT COPY - Use Your Own Values)
```toml
GEMINI_API_KEY = "AIzaSyABC123..."

[gmail_token]
token = "ya29.a0AfB_YOUR_ACTUAL_TOKEN"
refresh_token = "1//0gYOUR_ACTUAL_REFRESH_TOKEN"
token_uri = "https://oauth2.googleapis.com/token"
client_id = "12345-YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "GOCSPX-YOUR_CLIENT_SECRET"
scopes = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"]
universe_domain = "googleapis.com"
account = ""
expiry = "2025-12-31T23:59:59Z"
```

## ⚠️ Important Notes
1. **Never commit secrets to Git** (already protected by `.gitignore`)
2. Token auto-refreshes every ~7 days
3. If token expires, regenerate locally and update secrets
4. Keep your `token.json` file safe - backup it

## 🔧 Troubleshooting

**Gmail Still Offline?**
- Check expiry date isn't in the past
- Verify all values are correctly copied (no extra spaces/quotes)
- Make sure you clicked "Save" in Streamlit Cloud

**AI Engine Still Offline?**
- Verify Gemini API key is correct
- Key should start with "AIza..."
- Go to https://aistudio.google.com/app/apikey to verify

---

**Last Updated:** 2025-12-10  
**For App:** PrimeLine CRM  
**Platform:** Streamlit Cloud

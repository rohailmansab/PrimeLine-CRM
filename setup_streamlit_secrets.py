#!/usr/bin/env python3
"""
Helper script to encode token.json for Streamlit Cloud secrets.
Run this after you've authenticated locally with Gmail.

Usage:
    python setup_streamlit_secrets.py
"""

import os
import base64
import json
import sys


def main():
    """Main function to generate base64-encoded token for secrets."""
    
    if not os.path.exists('token.json'):
        print("❌ Error: token.json not found!")
        print("\nTo generate token.json:")
        print("  1. Run: streamlit run app.py")
        print("  2. Authenticate with your Gmail account when prompted")
        print("  3. token.json will be created automatically")
        print("  4. Then run this script again")
        sys.exit(1)
    
    try:
        with open('token.json', 'rb') as f:
            token_data = f.read()
        
        token_b64 = base64.b64encode(token_data).decode('utf-8')
        
        print("\n✅ Gmail token encoded successfully!\n")
        print("=" * 80)
        print("Copy this value to your Streamlit Cloud Secrets:")
        print("=" * 80)
        print(f"\ngmail_token_b64 = \"{token_b64}\"\n")
        print("=" * 80)
        print("\nSteps to add to Streamlit Cloud:")
        print("1. Go to your Streamlit Cloud app → Settings → Secrets")
        print("2. Paste the above line into the secrets editor")
        print("3. Save and redeploy\n")
        
        # Also save to a local secrets file for testing
        secrets_path = '.streamlit/secrets.toml'
        os.makedirs('.streamlit', exist_ok=True)
        
        with open(secrets_path, 'w') as f:
            f.write(f"# Streamlit Secrets\n")
            f.write(f"# This file is created locally for testing and should NOT be committed to git\n\n")
            f.write(f"gmail_token_b64 = \"{token_b64}\"\n")
        
        print(f"✓ Saved to {secrets_path} for local testing")
        print(f"⚠️  REMINDER: Add {secrets_path} to .gitignore before committing!\n")
        
    except Exception as e:
        print(f"❌ Error processing token.json: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

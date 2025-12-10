import os.path
import base64
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailService:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None
        self._authenticate()
    
    def is_authenticated(self) -> bool:
        return bool(self.creds and self.creds.valid)
    
    def get_user_email(self) -> str:
        """Get the email address of the authenticated user."""
        try:
            if not self.service:
                self._authenticate()
            profile = self.service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress', '')
        except Exception as e:
            print(f"Error getting user email: {str(e)}")
            return ''
    
    def _is_headless(self) -> bool:
        """Check if running in a headless environment (Streamlit Cloud, etc)."""
        import os
        headless_indicators = [
            'STREAMLIT_SERVER_HEADLESS',
            'CI',
            'GITHUB_ACTIONS',
            'DOCKER',
            'RENDER',
            'HEROKU_APP_NAME'
        ]
        is_headless = any(os.environ.get(indicator) for indicator in headless_indicators)
        if is_headless:
            print(f"✓ Headless environment detected: {[k for k in headless_indicators if os.environ.get(k)]}")
        return is_headless
    
    def _load_token_from_streamlit_secrets(self) -> bool:
        """Attempt to load Gmail token from Streamlit secrets (for Cloud deployment)."""
        try:
            import streamlit as st
            import base64
            import json
            
            print("🔍 Attempting to load Gmail token from Streamlit secrets...")
            
            # Check if Streamlit secrets are available
            if not hasattr(st, 'secrets'):
                print("❌ Streamlit secrets not available (not running in Streamlit?)")
                return False
            
            # Method 1: Load from base64 encoded token
            if 'gmail_token_b64' in st.secrets:
                print("✓ Found gmail_token_b64 in secrets")
                token_b64 = st.secrets['gmail_token_b64']
                token_json = base64.b64decode(token_b64).decode('utf-8')
                with open('token.json', 'w') as f:
                    f.write(token_json)
                print("✓ Successfully loaded Gmail token from Streamlit secrets (base64)")
                return True
            
            # Method 2: Load from [gmail_token] section
            if 'gmail_token' in st.secrets:
                print("✓ Found [gmail_token] section in secrets")
                token_dict = dict(st.secrets['gmail_token'])
                with open('token.json', 'w') as f:
                    json.dump(token_dict, f, indent=2)
                print("✓ Successfully loaded Gmail token from Streamlit secrets ([gmail_token])")
                return True
            
            print("❌ No Gmail token found in secrets (checked: gmail_token_b64, gmail_token)")
            available_secrets = list(st.secrets.keys())
            print(f"ℹ️ Available secrets: {available_secrets}")
            
        except Exception as e:
            print(f"❌ Error loading token from Streamlit secrets: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def _authenticate(self):
        # Try to load existing credentials
        try:
            # First, try to load from Streamlit secrets (for Cloud deployment)
            # Always attempt to load from secrets in Streamlit environment
            try:
                import streamlit as st
                if hasattr(st, 'secrets'):
                    print("🔍 Streamlit environment detected, attempting secrets load...")
                    if not os.path.exists('token.json') or self._is_headless():
                        self._load_token_from_streamlit_secrets()
            except ImportError:
                # Not running in Streamlit
                if self._is_headless() and not os.path.exists('token.json'):
                    self._load_token_from_streamlit_secrets()
            
            if os.path.exists('token.json'):
                try:
                    self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
                except Exception as e:
                    print(f"Warning: Failed to load token.json: {e}. Will re-authenticate.")
                    try:
                        os.remove('token.json')
                    except Exception:
                        pass

            # If credentials are missing or invalid, try to refresh or run the flow
            if not self.creds or not self.creds.valid:
                # If expired and refresh token available, attempt refresh
                if self.creds and getattr(self.creds, 'expired', False) and getattr(self.creds, 'refresh_token', None):
                    try:
                        self.creds.refresh(Request())
                    except RefreshError as re:
                        # Token was revoked or expired beyond refresh — remove and force re-auth
                        print(f"RefreshError: {re} — token expired or revoked. Removing token.json and re-authenticating.")
                        try:
                            if os.path.exists('token.json'):
                                os.remove('token.json')
                        except Exception:
                            pass
                        self.creds = None
                        # fallthrough to full auth flow
                
                if not self.creds:
                    # Check if running in headless environment
                    if self._is_headless():
                        print("⚠️ Headless environment detected (Streamlit Cloud, Docker, etc)")
                        print("ℹ️ Gmail authentication via browser is not available in this environment.")
                        print("✓ Attempting to use existing token.json credentials...")
                        
                        # In headless mode, we cannot proceed with new auth
                        # App will use whatever creds were pre-stored
                        if not os.path.exists('token.json'):
                            raise RuntimeError(
                                "No existing Gmail credentials found. "
                                "To use email features in Streamlit Cloud:\n"
                                "1. Run the app locally first to authenticate with Gmail\n"
                                "2. Copy the generated 'token.json' file\n"
                                "3. Upload it to your Streamlit secrets or app directory\n"
                                "See https://docs.streamlit.io/deploy/tutorials/databases for secrets setup."
                            )
                        self.creds = None  # Will raise if token.json can't be loaded
                    else:
                        # Desktop/local environment - use browser-based OAuth
                        try:
                            flow = InstalledAppFlow.from_client_secrets_file(
                                self.credentials_path, self.SCOPES)
                            self.creds = flow.run_local_server(
                                port=8080,
                                prompt='consent',
                                success_message='Authentication successful! You can close this window.'
                            )
                        except Exception as e:
                            # If local server fails (e.g. no browser found), treat as headless
                            print(f"⚠️ Local auth failed: {e}")
                            raise RuntimeError(
                                "Gmail authentication failed (could not launch browser). "
                                "If you are running on Streamlit Cloud or a remote server, you must set up secrets.\n"
                                "1. Run locally to generate token.json\n"
                                "2. Copy content of token.json\n"
                                "3. Add to Streamlit Secrets as 'gmail_token_b64' (base64 encoded) or just upload token.json if possible."
                            )

                # Persist credentials
                try:
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
                except Exception as e:
                    print(f"Warning: Couldn't write token.json: {e}")

            # Build service with valid credentials
            self.service = build('gmail', 'v1', credentials=self.creds)

        except RefreshError as re:
            # Catch any leftover refresh errors and force re-auth
            print(f"Authentication failed with RefreshError: {re}. Removing token and asking to re-authenticate.")
            try:
                if os.path.exists('token.json'):
                    os.remove('token.json')
            except Exception:
                pass
            raise
        except Exception as e:
            print(f"Unexpected error during Gmail authentication: {e}")
            raise
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            raw_message = {'raw': raw}
            
            sent_message = self.service.users().messages().send(
                userId='me', body=raw_message).execute()
            
            return {
                'status': 'success',
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId', sent_message['id'])
            }
            
        except HttpError as error:
            return {
                'status': 'error',
                'error': str(error)
            }
    
    def check_inbox(self, query: str = None, max_results: int = 10) -> list:
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            if not messages:
                # Try to provide diagnostic info - check if ANY messages exist
                try:
                    all_messages = self.service.users().messages().list(
                        userId='me', maxResults=10).execute().get('messages', [])
                    if all_messages:
                        print(f"  [No match for query: {query}]")
                        print(f"  [But {len(all_messages)} messages exist in inbox]")
                        # Show first few subjects for debugging
                        for msg_preview in all_messages[:2]:
                            try:
                                msg = self.service.users().messages().get(
                                    userId='me', id=msg_preview['id'], format='minimal').execute()
                                headers = msg.get('payload', {}).get('headers', [])
                                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                                print(f"      - {subject[:60]}")
                            except:
                                pass
                    else:
                        print(f"  [Gmail inbox appears to be empty]")
                except:
                    pass
                return []
            
            print(f"Found {len(messages)} messages for query: {query}")
            
            full_messages = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me', id=msg['id'], format='full').execute()
                    
                    headers = message['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                    
                    body = self._extract_body(message['payload'])
                    
                    message_data = {
                        'id': message['id'],
                        'thread_id': message['threadId'],
                        'subject': subject,
                        'sender': sender,
                        'body': body,
                        'date': message['internalDate'],
                        'labels': message.get('labelIds', [])
                    }
                    
                    print(f"  Message: From={sender}, Subject={subject}, Has Body={len(body) > 0}")
                    
                    full_messages.append(message_data)
                    
                except Exception as e:
                    print(f"Error processing message {msg['id']}: {str(e)}")
                    continue
            
            return full_messages
            
        except HttpError as error:
            print(f'Gmail API error: {error}')
            return []
    
    def _extract_body(self, payload: dict) -> str:
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        break
        else:
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def mark_as_read(self, message_id: str) -> bool:
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"Marked message {message_id} as read")
            return True
        except HttpError as error:
            print(f'Error marking as read: {error}')
            return False

    def archive_message(self, message_id: str) -> bool:
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            print(f"Archived message {message_id}")
            return True
        except HttpError as error:
            print(f'Error archiving: {error}')
            return False
    
    def get_thread_messages(self, thread_id: str) -> list:
        try:
            thread = self.service.users().threads().get(
                userId='me', id=thread_id, format='full').execute()
            
            messages = []
            for msg in thread['messages']:
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                
                body = self._extract_body(msg['payload'])
                
                messages.append({
                    'id': msg['id'],
                    'thread_id': thread_id,
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'date': msg['internalDate']
                })
            
            return messages
            
        except HttpError as error:
            print(f'Error getting thread: {error}')
            return []
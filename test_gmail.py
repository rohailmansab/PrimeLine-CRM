#!/usr/bin/env python3
"""
Diagnostic script to test Gmail connection and email queries.
Run this to debug why emails are not being found.
"""

import sys
from database import Database
from gmail_service import GmailService
from email_handler import EmailHandler
from config import GMAIL_CREDENTIALS_PATH, DATABASE_PATH

def test_gmail():
    print("=" * 80)
    print("GMAIL DIAGNOSTIC TEST")
    print("=" * 80)
    
    try:
        print("\n1. Initializing Gmail Service...")
        gmail = GmailService(GMAIL_CREDENTIALS_PATH)
        print("   [OK] Gmail service initialized")
        
        print("\n2. Getting user email...")
        user_email = gmail.get_user_email()
        print(f"   [OK] Authenticated as: {user_email}")
        
        print("\n3. Testing different Gmail queries...")
        
        test_queries = [
            'subject:"Re: Price Update Request"',
            'subject:"Price Update"',
            'to:me',
            'is:unread',
        ]
        
        for query in test_queries:
            print(f"\n   Query: {query}")
            results = gmail.check_inbox(query=query, max_results=5)
            print(f"   Results: {len(results)} messages found")
            if results:
                for msg in results[:2]:
                    print(f"     - {msg['subject'][:60]}")
        
        print("\n4. Testing EmailHandler...")
        db = Database(DATABASE_PATH)
        handler = EmailHandler(db)
        print("   [OK] EmailHandler initialized")
        
        print("\n5. Running check_replies_and_save...")
        results = handler.check_replies_and_save()
        print(f"   Found {len(results)} results")
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_gmail()
    sys.exit(0 if success else 1)

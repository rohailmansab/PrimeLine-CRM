import schedule
import time
import threading
from datetime import datetime
import pytz
from typing import Optional

from config import SCHEDULER_CONFIG, SAMPLE_PRODUCTS
from database import Database
from email_handler import EmailHandler
from gemini_client import GeminiClient

class SchedulerService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db: Database, email_handler: EmailHandler, gemini_client: Optional[GeminiClient]):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SchedulerService, cls).__new__(cls)
                    cls._instance.db = db
                    cls._instance.email_handler = email_handler
                    cls._instance.gemini_client = gemini_client
                    cls._instance.is_running = False
                    cls._instance.thread = None
        return cls._instance

    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            return

        self._setup_jobs()
        self.is_running = True
        self.thread = threading.Thread(target=self._run_continuously, daemon=True)
        self.thread.start()
        print("✅ Scheduler service started")

    def _setup_jobs(self):
        """Configure scheduled jobs based on config"""
        # Weekly Price Updates
        # Note: schedule uses system time by default. 
        # For simplicity in this demo, we'll assume system time is close enough or use a simple offset if needed.
        # In production, we'd handle timezones more strictly.
        
        update_time = SCHEDULER_CONFIG["weekly_update_time"]
        check_time = SCHEDULER_CONFIG["daily_check_time"]
        
        # Weekly Update (Monday)
        schedule.every().monday.at(update_time).do(self.weekly_price_updates)
        
        # Daily Check (Mon-Fri)
        schedule.every().monday.at(check_time).do(self.daily_reply_check)
        schedule.every().tuesday.at(check_time).do(self.daily_reply_check)
        schedule.every().wednesday.at(check_time).do(self.daily_reply_check)
        schedule.every().thursday.at(check_time).do(self.daily_reply_check)
        schedule.every().friday.at(check_time).do(self.daily_reply_check)
        
        print(f"📅 Jobs scheduled: Weekly update Mon {update_time}, Daily check Mon-Fri {check_time}")

    def _run_continuously(self):
        """Run the scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)

    def weekly_price_updates(self):
        """Send price requests to all suppliers"""
        print("🔄 Starting scheduled weekly price updates...")
        try:
            suppliers = self.db.get_suppliers()
            if not suppliers:
                self.db.log_sync_event("weekly_update", "skipped", "No suppliers found")
                return

            products = [p["name"] for p in SAMPLE_PRODUCTS]
            sent_count = 0
            
            for supplier in suppliers:
                try:
                    email = supplier.get('email')
                    if email:
                        self.email_handler.send_price_request(email, products)
                        sent_count += 1
                except Exception as e:
                    print(f"Error sending to {supplier.get('name')}: {e}")
            
            msg = f"Sent requests to {sent_count}/{len(suppliers)} suppliers"
            self.db.log_sync_event("weekly_update", "success", msg)
            print(f"✅ Weekly update completed: {msg}")
            
        except Exception as e:
            error_msg = str(e)
            self.db.log_sync_event("weekly_update", "error", error_msg)
            print(f"❌ Weekly update failed: {error_msg}")

    def daily_reply_check(self):
        """Check for email replies and update prices"""
        print("🔄 Starting scheduled daily reply check...")
        try:
            if not self.gemini_client:
                self.db.log_sync_event("daily_check", "warning", "Gemini client not initialized")
                return

            results = self.email_handler.check_replies_and_save(self.gemini_client)
            
            if results:
                count = sum(len(r.get('products', [])) for r in results)
                msg = f"Processed {len(results)} emails, updated {count} products"
                self.db.log_sync_event("daily_check", "success", msg)
                print(f"✅ Daily check completed: {msg}")
            else:
                self.db.log_sync_event("daily_check", "success", "No new replies found")
                print("✅ Daily check completed: No new replies")
                
        except Exception as e:
            error_msg = str(e)
            self.db.log_sync_event("daily_check", "error", error_msg)
            print(f"❌ Daily check failed: {error_msg}")

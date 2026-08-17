import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger("supabase_db")

class SupabaseDB:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "https://twollneowqkekmxoctdz.supabase.co")
        self.key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3b2xsbmVvd3FrZWtteG9jdGR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY5NjM1NDEsImV4cCI6MjEwMjUzOTU0MX0.-QfSVz7FpjEb7Y2E_Z3c9lmEyepeNIdqKIkV65KeNEc")
        self.client = None
        self.local_cache = []
        self._connect()

    def _connect(self):
        if self.url and self.key:
            try:
                from supabase import create_client
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client connected successfully.")
            except Exception as e:
                logger.warning(f"Supabase connection warning: {e}. Running in local storage mode.")
                self.client = None

    def save_item(self, agent_id: str, category: str, title: str, content: str) -> Dict[str, Any]:
        record = {
            "agent_id": agent_id,
            "category": category,
            "title": title,
            "content": content,
            "created_at": datetime.utcnow().isoformat()
        }
        self.local_cache.insert(0, record)
        if self.client:
            try:
                self.client.table("calshot_campaigns").insert(record).execute()
            except Exception as e:
                logger.warning(f"Could not push to Supabase table: {e}")
        return record

    def get_recent_items(self, limit: int = 40) -> List[Dict[str, Any]]:
        if self.client:
            try:
                res = self.client.table("calshot_campaigns").select("*").order("created_at", desc=True).limit(limit).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return self.local_cache[:limit]

db = SupabaseDB()

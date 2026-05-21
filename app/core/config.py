import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

# Temporary dev carrier — replaced by JWT-extracted carrier_id once auth is wired
DEV_CARRIER_ID: str = "11111111-1111-1111-1111-111111111111"

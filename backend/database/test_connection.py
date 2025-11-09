import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv("../.env")
# --- 1. GET YOUR CONNECTION STRING ---
# Put your Supabase connection string here
# (The one that looks like: "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")

if SUPABASE_DB_URL == "":
    raise ValueError("SUPABASE_DB_URL must be set in .env")
try:
    # --- 2. CREATE THE ENGINE ---
    # This is the same 'engine' your FastAPI app will use
    engine = create_engine(SUPABASE_DB_URL)

    # --- 3. TRY TO CONNECT AND RUN A TEST QUERY ---
    print("Attempting to connect to the database...")

    with engine.connect() as connection:
        # Run a simple, harmless query to check the connection
        result = connection.execute(text("SELECT 1"))

        print("Connection successful!")
        print(f"Test query result (should be 1): {result.scalar()}")

except OperationalError as e:
    print("\n--- CONNECTION FAILED ---")
    print("Could not connect to the database.")
    print(f"\nError Details:\n{e}")
    print("\nChecklist:")
    print("1. Is your Supabase project 'Active'?")
    print("2. Did you copy the *entire* connection string correctly?")
    print("3. Is your password correct?")
    print(
        "4. Is your IP address whitelisted in Supabase (if you enabled IP restrictions)?"
    )

except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")

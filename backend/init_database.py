from database.connection import init_db

if __name__ == "__main__":
    print("🚀 Initializing database tables...")
    init_db()
    print("✅ Database initialization complete!")

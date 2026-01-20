from app.db.session import init_db

def main():
    print("Initializing database...")
    init_db()
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    main()

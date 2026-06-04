"""
Insurance Claim Pre-Assurance – Database Initialisation Script
Run once to create all tables:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

# Allow imports from the backend root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base  # noqa: E402

# Import all models so their metadata is registered with Base
from app.models import claim, document, assessment, audit_log  # noqa: E402, F401


def main() -> None:
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables created:")
    for table_name in Base.metadata.tables:
        print(f"  ✓ {table_name}")


if __name__ == "__main__":
    main()

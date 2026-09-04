import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.seed import seed_database

if __name__ == "__main__":
    seed_database()

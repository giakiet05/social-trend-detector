"""
Migration script: Migrate keywords from YAML to MongoDB.

Usage:
    uv run python scripts/migrate_keywords_to_mongo.py
"""

import yaml
from pymongo import MongoClient
from datetime import datetime
import os
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parents[1]
KEYWORDS_CONFIG = ROOT_DIR / "producer/config/scraping_keywords.yaml"

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@localhost:27017/?authSource=admin")


def migrate():
    """Migrate keywords from YAML to MongoDB."""

    print("=" * 70)
    print("MIGRATION: YAML Keywords → MongoDB")
    print("=" * 70)

    # 1. Load YAML keywords
    print(f"\n[1/4] Loading keywords from {KEYWORDS_CONFIG}...")
    try:
        with open(KEYWORDS_CONFIG, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load YAML: {e}")
        return

    print(f"✅ Loaded keywords for: {list(config.keys())}")

    # 2. Connect to MongoDB
    print(f"\n[2/4] Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI)
        db = client["social_trends"]
        collection = db.active_keywords

        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return

    # 3. Create indexes
    print(f"\n[3/4] Creating indexes...")
    collection.create_index("keyword", unique=True)
    collection.create_index([("status", 1), ("sources", 1)])
    print("✅ Indexes created")

    # 4. Migrate keywords
    print(f"\n[4/4] Migrating keywords...")

    migrated_count = 0
    skipped_count = 0

    # Migrate TikTok keywords
    tiktok_keywords = config.get('tiktok', {}).get('keywords', [])
    print(f"\n  TikTok: {len(tiktok_keywords)} keywords")
    for keyword in tiktok_keywords:
        try:
            result = collection.update_one(
                {"keyword": keyword},
                {
                    "$setOnInsert": {
                        "keyword": keyword,
                        "status": "active",
                        "added_at": datetime.utcnow(),
                        "added_by": "migration",
                        "origin": "manual"
                    },
                    "$addToSet": {"sources": "tiktok"}
                },
                upsert=True
            )
            if result.upserted_id:
                migrated_count += 1
                print(f"    ✅ '{keyword}' (new)")
            else:
                skipped_count += 1
                print(f"    ⏭️  '{keyword}' (exists, added 'tiktok' source)")
        except Exception as e:
            print(f"    ❌ '{keyword}': {e}")

    # Migrate News keywords
    news_keywords = config.get('news', {}).get('keywords', [])
    print(f"\n  News: {len(news_keywords)} keywords")
    for keyword in news_keywords:
        try:
            result = collection.update_one(
                {"keyword": keyword},
                {
                    "$setOnInsert": {
                        "keyword": keyword,
                        "status": "active",
                        "added_at": datetime.utcnow(),
                        "added_by": "migration",
                        "origin": "manual"
                    },
                    "$addToSet": {"sources": "news"}
                },
                upsert=True
            )
            if result.upserted_id:
                migrated_count += 1
                print(f"    ✅ '{keyword}' (new)")
            else:
                skipped_count += 1
                print(f"    ⏭️  '{keyword}' (exists, added 'news' source)")
        except Exception as e:
            print(f"    ❌ '{keyword}': {e}")

    # Migrate YouTube keywords
    youtube_keywords = config.get('youtube', {}).get('keywords', [])
    print(f"\n  YouTube: {len(youtube_keywords)} keywords")
    for keyword in youtube_keywords:
        try:
            result = collection.update_one(
                {"keyword": keyword},
                {
                    "$setOnInsert": {
                        "keyword": keyword,
                        "status": "active",
                        "added_at": datetime.utcnow(),
                        "added_by": "migration",
                        "origin": "manual"
                    },
                    "$addToSet": {"sources": "youtube"}
                },
                upsert=True
            )
            if result.upserted_id:
                migrated_count += 1
                print(f"    ✅ '{keyword}' (new)")
            else:
                skipped_count += 1
                print(f"    ⏭️  '{keyword}' (exists, added 'youtube' source)")
        except Exception as e:
            print(f"    ❌ '{keyword}': {e}")

    # Summary
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print(f"  New keywords inserted: {migrated_count}")
    print(f"  Existing keywords updated: {skipped_count}")
    print(f"  Total in MongoDB: {collection.count_documents({})}")
    print("=" * 70)

    # Verify
    print("\n[Verification] Sample MongoDB documents:")
    for doc in collection.find().limit(3):
        print(f"  - {doc['keyword']}: sources={doc['sources']}, status={doc['status']}")

    client.close()


if __name__ == "__main__":
    migrate()

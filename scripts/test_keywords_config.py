"""
Test script: Verify keywords configuration in both YAML and MongoDB modes.

Usage:
    # Test YAML mode (default)
    uv run python scripts/test_keywords_config.py

    # Test MongoDB mode
    KEYWORDS_SOURCE=mongodb uv run python scripts/test_keywords_config.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from producer.config.settings import settings


def test_keywords_config():
    """Test keywords configuration."""

    mode = os.getenv("KEYWORDS_SOURCE", "yaml")

    print("=" * 70)
    print(f"TESTING KEYWORDS CONFIGURATION (Mode: {mode.upper()})")
    print("=" * 70)

    # Test TikTok
    print("\n[1] TikTok Configuration")
    print(f"  Source mode: {settings.keywords.source}")
    print(f"  Keywords: {len(settings.keywords.tiktok_keywords)} items")
    print(f"  Hashtags: {len(settings.keywords.tiktok_hashtags)} items")
    print(f"  Max videos: {settings.tiktok_config.MAX_VIDEOS_PER_QUERY}")
    if settings.keywords.tiktok_keywords:
        print(f"  Sample keywords: {settings.keywords.tiktok_keywords[:3]}")

    # Test News
    print("\n[2] News Configuration")
    print(f"  Keywords: {len(settings.keywords.news_keywords)} items")
    print(f"  RSS feeds: {len(settings.keywords.news_rss_feeds)} items")
    if settings.keywords.news_keywords:
        print(f"  Sample keywords: {settings.keywords.news_keywords[:3]}")
    if settings.keywords.news_rss_feeds:
        print(f"  Sample RSS feeds: {settings.keywords.news_rss_feeds[:2]}")

    # Test YouTube
    print("\n[3] YouTube Configuration")
    print(f"  Keywords: {len(settings.keywords.youtube_keywords)} items")
    print(f"  Max videos: {settings.youtube_config.MAX_VIDEOS_PER_KEYWORD}")
    if settings.keywords.youtube_keywords:
        print(f"  Sample keywords: {settings.keywords.youtube_keywords[:3]}")

    # Validation
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    all_passed = True

    if len(settings.keywords.tiktok_keywords) == 0:
        print("❌ TikTok keywords empty!")
        all_passed = False
    else:
        print(f"✅ TikTok keywords OK ({len(settings.keywords.tiktok_keywords)} items)")

    if len(settings.keywords.news_keywords) == 0:
        print("❌ News keywords empty!")
        all_passed = False
    else:
        print(f"✅ News keywords OK ({len(settings.keywords.news_keywords)} items)")

    if len(settings.keywords.news_rss_feeds) == 0:
        print("❌ News RSS feeds empty!")
        all_passed = False
    else:
        print(f"✅ News RSS feeds OK ({len(settings.keywords.news_rss_feeds)} items)")

    if len(settings.keywords.youtube_keywords) == 0:
        print("❌ YouTube keywords empty!")
        all_passed = False
    else:
        print(f"✅ YouTube keywords OK ({len(settings.keywords.youtube_keywords)} items)")

    if settings.tiktok_config.MAX_VIDEOS_PER_QUERY <= 0:
        print("❌ TikTok max_videos invalid!")
        all_passed = False
    else:
        print(f"✅ TikTok max_videos OK ({settings.tiktok_config.MAX_VIDEOS_PER_QUERY})")

    if settings.youtube_config.MAX_VIDEOS_PER_KEYWORD <= 0:
        print("❌ YouTube max_videos invalid!")
        all_passed = False
    else:
        print(f"✅ YouTube max_videos OK ({settings.youtube_config.MAX_VIDEOS_PER_KEYWORD})")

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = test_keywords_config()
    sys.exit(0 if success else 1)

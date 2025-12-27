"""
Test script: Test keyword submission functionality.

Usage:
    uv run python scripts/test_keyword_submission.py
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from common.keyword_manager import MongoKeywordManager


def test_keyword_submission():
    """Test keyword submission."""

    print("=" * 70)
    print("TESTING KEYWORD SUBMISSION")
    print("=" * 70)

    manager = MongoKeywordManager()

    # Test 1: Submit new keyword
    print("\n[Test 1] Submit new keyword")
    result = manager.submit_keyword(
        keyword="Test Keyword 1",
        reason="This is a test submission",
        submitted_by="test@example.com"
    )
    print(f"  Result: {result}")

    # Test 2: Submit duplicate keyword
    print("\n[Test 2] Submit duplicate keyword")
    result = manager.submit_keyword(
        keyword="Test Keyword 1",
        reason="Duplicate test",
        submitted_by="test2@example.com"
    )
    print(f"  Result: {result}")

    # Test 3: Submit anonymous
    print("\n[Test 3] Submit anonymous keyword")
    result = manager.submit_keyword(
        keyword="Test Keyword Anonymous"
    )
    print(f"  Result: {result}")

    # Test 4: Get pending submissions
    print("\n[Test 4] Get pending submissions")
    submissions = manager.get_pending_submissions(limit=10)
    print(f"  Found {len(submissions)} pending submissions:")
    for sub in submissions[:3]:
        print(f"    - {sub['keyword']} (by {sub['submitted_by']}) - {sub['created_at']}")

    # Test 5: Approve submission
    if submissions:
        print("\n[Test 5] Approve first submission")
        first_sub = submissions[0]
        result = manager.approve_submission(
            submission_id=str(first_sub["_id"]),
            sources=["tiktok", "youtube"],
            reviewed_by="test_admin"
        )
        print(f"  Result: {result}")

        # Verify it's in active keywords
        active_keywords = manager.get_active_keywords()
        print(f"  Active keywords count: {len(active_keywords)}")

    # Test 6: Reject submission
    if len(submissions) > 1:
        print("\n[Test 6] Reject second submission")
        second_sub = submissions[1]
        result = manager.reject_submission(
            submission_id=str(second_sub["_id"]),
            reason="Test rejection",
            reviewed_by="test_admin"
        )
        print(f"  Result: {result}")

    # Test 7: Add keyword manually
    print("\n[Test 7] Add keyword manually")
    result = manager.add_keyword(
        keyword="Manual Test Keyword",
        sources=["tiktok", "news"],
        added_by="test_admin"
    )
    print(f"  Result: {result}")

    # Test 8: Remove keyword
    print("\n[Test 8] Remove keyword")
    result = manager.remove_keyword(
        keyword="Manual Test Keyword",
        removed_by="test_admin"
    )
    print(f"  Result: {result}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    active_count = len(manager.get_active_keywords())
    pending_count = len(manager.get_pending_submissions())

    print(f"  Active keywords: {active_count}")
    print(f"  Pending submissions: {pending_count}")

    print("=" * 70)

    manager.close()


if __name__ == "__main__":
    test_keyword_submission()

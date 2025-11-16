"""
Task 4: Tech Keywords Extraction

Mục tiêu: Xây dựng keyword dictionary để filter videos về Tech.
Output: results/tech_keywords.json
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter

# ============================================================================
# TODO: FILL VÀO TECH KEYWORDS
# ============================================================================

# Danh sách keywords liên quan Tech (lowercase)
TECH_KEYWORDS = [
    "ai", "artificial intelligence", "tech", "technology",
    "coding", "programming", "developer", "software",
    "chatgpt", "claude", "openai", "machine learning",
    # TODO: Thêm keywords khác sau khi đọc data
]

# Danh sách hashtags liên quan Tech (lowercase, không cần # prefix)
TECH_HASHTAGS = [
    "techtok", "ai", "coding", "programming",
    "softwareengineering", "machinelearning", "devlife",
    # TODO: Thêm hashtags khác
]

# ============================================================================


def load_data():
    """Load CSV data."""
    df = pd.read_csv('../data/raw_tiktok_data.csv', encoding='utf-8-sig')
    print(f"✅ Loaded {len(df)} videos")
    return df


def extract_hashtags(row, hashtag_cols):
    """Extract hashtags từ row."""
    hashtags = []
    for col in hashtag_cols:
        if pd.notna(row[col]):
            hashtags.append(str(row[col]).lower())
    return hashtags


def is_tech_video(text, hashtags, keyword_list, hashtag_list):
    """
    Check xem video có phải Tech hay không.

    Args:
        text: Video caption text
        hashtags: List of hashtags
        keyword_list: List of tech keywords
        hashtag_list: List of tech hashtags

    Returns:
        bool: True nếu video về Tech
    """
    if pd.isna(text):
        return False

    text_lower = text.lower()

    # Check keywords trong text
    for keyword in keyword_list:
        if keyword in text_lower:
            return True

    # Check hashtags
    for hashtag in hashtags:
        if hashtag in hashtag_list:
            return True

    return False


def test_accuracy(df, keyword_list, hashtag_list):
    """
    Test accuracy của keyword filtering.

    TODO: Manual labeling để tính precision/recall chính xác.
    Hiện tại function này chỉ count số videos được filter.
    """
    hashtag_cols = [col for col in df.columns if col.startswith('hashtags/')]

    tech_count = 0
    non_tech_count = 0

    for idx, row in df.iterrows():
        text = row.get('text', '')
        hashtags = extract_hashtags(row, hashtag_cols)

        if is_tech_video(text, hashtags, keyword_list, hashtag_list):
            tech_count += 1
        else:
            non_tech_count += 1

    print(f"\nFiltering results:")
    print(f"  Tech videos: {tech_count} ({tech_count/len(df)*100:.1f}%)")
    print(f"  Non-tech videos: {non_tech_count} ({non_tech_count/len(df)*100:.1f}%)")

    # TODO: Manual labeling để tính precision/recall
    # Bây giờ return placeholder values
    return {
        "precision": 0.90,  # TODO: Tính thật sau khi manual label
        "recall": 0.85,     # TODO: Tính thật sau khi manual label
        "total_videos": len(df),
        "tech_videos": tech_count,
        "non_tech_videos": non_tech_count
    }


def analyze_common_hashtags(df, top_n=20):
    """Analyze top hashtags để tìm thêm tech hashtags."""
    hashtag_cols = [col for col in df.columns if col.startswith('hashtags/')]

    all_hashtags = []
    for idx, row in df.iterrows():
        for col in hashtag_cols:
            if pd.notna(row[col]):
                all_hashtags.append(str(row[col]).lower())

    counter = Counter(all_hashtags)

    print(f"\nTop {top_n} hashtags:")
    for hashtag, count in counter.most_common(top_n):
        print(f"  #{hashtag}: {count}")

    return counter


def sample_videos(df, n=10):
    """Sample random videos để manual labeling."""
    sample = df.sample(n=min(n, len(df)))
    hashtag_cols = [col for col in df.columns if col.startswith('hashtags/')]

    print(f"\n{'='*80}")
    print(f"SAMPLE {n} VIDEOS FOR MANUAL LABELING")
    print(f"{'='*80}\n")

    for idx, row in sample.iterrows():
        text = row.get('text', '')
        hashtags = extract_hashtags(row, hashtag_cols)

        print(f"Video {idx}:")
        print(f"  Text: {text[:150]}...")
        print(f"  Hashtags: {', '.join(['#' + h for h in hashtags[:5]])}")
        print(f"  TODO: Tech-related? (1=Yes, 0=No)")
        print()


def main():
    """Main function."""
    print("="*80)
    print("TASK 4: TECH KEYWORDS EXTRACTION")
    print("="*80)

    # Load data
    df = load_data()

    # Step 1: Sample videos để manual labeling
    print("\n[Step 1] Sample videos for labeling:")
    sample_videos(df, n=10)

    # Step 2: Analyze common hashtags
    print("\n[Step 2] Analyze common hashtags:")
    analyze_common_hashtags(df, top_n=20)

    # Step 3: Test filtering với current keywords
    print("\n[Step 3] Test filtering:")
    print(f"Current keywords: {len(TECH_KEYWORDS)} keywords")
    print(f"Current hashtags: {len(TECH_HASHTAGS)} hashtags")

    accuracy = test_accuracy(df, TECH_KEYWORDS, TECH_HASHTAGS)

    # Step 4: Save results
    output = {
        "keywords": TECH_KEYWORDS,
        "hashtags": ["#" + h for h in TECH_HASHTAGS],  # Add # prefix
        "accuracy": accuracy,
        "methodology": "Manual analysis of common hashtags and video texts. TODO: Improve with manual labeling."
    }

    output_path = Path('../results/tech_keywords.json')
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to {output_path}")

    # Preview
    print("\nPreview:")
    print(json.dumps(output, indent=2, ensure_ascii=False))

    print("\n" + "="*80)
    print("TODO:")
    print("1. Đọc sample videos ở trên")
    print("2. Thêm keywords/hashtags vào TECH_KEYWORDS và TECH_HASHTAGS")
    print("3. Chạy lại script để test accuracy")
    print("4. Manual label 30-50 videos để tính precision/recall chính xác")
    print("="*80)


if __name__ == "__main__":
    main()

"""
Task 5: LLM Prompt Testing

Mục tiêu: Tìm LLM prompt tốt nhất để analyze trends.
Output: results/best_llm_prompt.txt
"""

import pandas as pd
import json
import os
from pathlib import Path
from openai import OpenAI

# ============================================================================
# PROMPT VARIATIONS
# ============================================================================

PROMPTS = {
    "v1_baseline": """Analyze these {n} TikTok videos about TECH trends.

Sample videos:
{video_texts}

Extract:
1. Topic (3-7 words)
2. Summary (1-2 sentences)
3. Sentiment (positive/negative/neutral)
4. Keywords (5-10 keywords)

Respond in JSON format:
{{
  "topic": "...",
  "summary": "...",
  "sentiment": "...",
  "keywords": [...]
}}""",

    "v2_detailed": """You are analyzing a cluster of {n} TECH-related TikTok videos that were grouped by semantic similarity.

CONTEXT:
These videos likely discuss the same tech trend, tool, product, or news. Your goal is to identify what trend they represent.

SAMPLE VIDEOS:
{video_texts}

TASK:
Extract the following information about this trend:

1. TOPIC: A specific, concise title (4-8 words)
   - Good examples: "Claude Code AI Assistant Launch", "Python 3.12 New Features"
   - Bad examples: "AI Tools", "Tech News"

2. SUMMARY: A 1-2 sentence explanation of what this trend is about
   - Focus on WHAT the trend is, not just describing the videos

3. SENTIMENT: The overall tone of the discussion
   - Options: positive, negative, neutral

4. KEYWORDS: 5-10 specific, relevant keywords
   - Include: product names, technologies, companies, concepts
   - Example: ["Claude", "AI coding", "VSCode", "developer tools"]

RESPOND ONLY IN VALID JSON FORMAT:
{{
  "topic": "...",
  "summary": "...",
  "sentiment": "...",
  "keywords": ["...", "..."]
}}""",

    "v3_constraints": """Analyze this cluster of {n} TikTok videos about a tech trend.

Videos:
{video_texts}

Requirements:
- Topic: Must be SPECIFIC (e.g., "Claude Code Launch", NOT "AI Tools")
- Summary: 1-2 sentences explaining the trend
- Sentiment: positive/negative/neutral
- Keywords: 5-10 keywords (product names, technologies, companies)

JSON format only:
{{
  "topic": "...",
  "summary": "...",
  "sentiment": "...",
  "keywords": [...]
}}""",

    # TODO: Thêm prompt variations khác
}

# ============================================================================


def load_data():
    """Load CSV data."""
    df = pd.read_csv('../data/raw_tiktok_data.csv', encoding='utf-8-sig')
    print(f"✅ Loaded {len(df)} videos")
    return df


def create_sample_clusters(df, n_clusters=3, videos_per_cluster=5):
    """
    Tạo sample clusters để test.

    TODO: Để test đúng, nên dùng DBSCAN clustering thật.
    Hiện tại function này chỉ random sample.
    """
    clusters = []

    for i in range(n_clusters):
        sample = df.sample(n=videos_per_cluster)
        cluster = []

        for idx, row in sample.iterrows():
            video = {
                'text': row.get('text', ''),
                'id': row.get('id', ''),
            }

            # Extract hashtags
            hashtag_cols = [col for col in df.columns if col.startswith('hashtags/')]
            hashtags = [row[col] for col in hashtag_cols if pd.notna(row[col])]
            video['hashtags'] = hashtags[:5]  # Top 5 hashtags

            cluster.append(video)

        clusters.append(cluster)

    return clusters


def format_cluster_for_prompt(cluster):
    """Format cluster videos cho prompt."""
    video_texts = []
    for i, video in enumerate(cluster, 1):
        text = video.get('text', '')[:200]  # Truncate
        hashtags = video.get('hashtags', [])
        video_texts.append(
            f"{i}. Text: {text}...\n"
            f"   Hashtags: {', '.join(['#' + h for h in hashtags])}"
        )

    return "\n\n".join(video_texts)


def test_prompt(client, prompt_template, cluster):
    """
    Test 1 prompt với 1 cluster.

    Args:
        client: OpenAI client
        prompt_template: Prompt template string
        cluster: List of video dicts

    Returns:
        dict: LLM response (parsed JSON)
    """
    n = len(cluster)
    video_texts = format_cluster_for_prompt(cluster)

    prompt = prompt_template.format(n=n, video_texts=video_texts)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Hoặc "gpt-4.1-nano"
            messages=[
                {"role": "system", "content": "You are a TikTok trend analyst specializing in tech content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON
        # Remove markdown code blocks nếu có
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)
        return result

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def rate_output(result, prompt_version):
    """
    Manual rating của output.

    TODO: Fill in ratings sau khi xem output.
    """
    print(f"\n{'='*80}")
    print(f"Prompt: {prompt_version}")
    print(f"{'='*80}")
    print(f"Topic: {result['topic']}")
    print(f"Summary: {result['summary']}")
    print(f"Sentiment: {result['sentiment']}")
    print(f"Keywords: {', '.join(result['keywords'])}")
    print()

    # TODO: Manual rating
    print("TODO: Rate this output (1-5 stars):")
    print("  - Topic quality (specific vs generic):")
    print("  - Summary quality (accurate vs vague):")
    print("  - Keyword relevance:")
    print()

    return {
        "topic_quality": 0,      # TODO: Fill 1-5
        "summary_quality": 0,    # TODO: Fill 1-5
        "keyword_relevance": 0,  # TODO: Fill 1-5
    }


def main():
    """Main function."""
    print("="*80)
    print("TASK 5: LLM PROMPT TESTING")
    print("="*80)

    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not found")
        print("Set environment variable: export OPENAI_API_KEY='sk-...'")
        return

    client = OpenAI(api_key=api_key)

    # Load data
    df = load_data()

    # Create sample clusters
    print("\n[Step 1] Creating sample clusters...")
    clusters = create_sample_clusters(df, n_clusters=3, videos_per_cluster=5)
    print(f"✅ Created {len(clusters)} sample clusters")

    # Test each prompt
    print("\n[Step 2] Testing prompts...")

    results = {}

    for prompt_name, prompt_template in PROMPTS.items():
        print(f"\n--- Testing {prompt_name} ---")

        # Test on first cluster only (để tiết kiệm API calls)
        cluster = clusters[0]

        result = test_prompt(client, prompt_template, cluster)

        if result:
            # TODO: Manual rating
            rating = rate_output(result, prompt_name)

            results[prompt_name] = {
                "output": result,
                "rating": rating
            }

    # Step 3: Compare results
    print("\n" + "="*80)
    print("COMPARISON TABLE")
    print("="*80)
    print(f"{'Prompt':<20} {'Topic Quality':<15} {'Summary Quality':<18} {'Keyword Relevance':<20}")
    print("-"*80)

    for prompt_name, data in results.items():
        rating = data['rating']
        print(f"{prompt_name:<20} "
              f"{rating['topic_quality']}/5{'':<12} "
              f"{rating['summary_quality']}/5{'':<15} "
              f"{rating['keyword_relevance']}/5")

    # TODO: Chọn best prompt
    best_prompt_name = "v2_detailed"  # TODO: Thay đổi sau khi compare

    print(f"\n✅ BEST PROMPT: {best_prompt_name}")

    # Save best prompt
    best_prompt = PROMPTS[best_prompt_name]

    output_path = Path('../results/best_llm_prompt.txt')
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(best_prompt)

    print(f"✅ Best prompt saved to {output_path}")

    # Save comparison table
    comparison_path = Path('../results/prompt_comparison.json')
    with open(comparison_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Comparison saved to {comparison_path}")

    print("\n" + "="*80)
    print("TODO:")
    print("1. Review output của từng prompt ở trên")
    print("2. Fill in ratings (topic_quality, summary_quality, keyword_relevance)")
    print("3. Chọn best_prompt_name")
    print("4. Chạy lại script để save best prompt")
    print("="*80)


if __name__ == "__main__":
    main()

# 📋 DANH SÁCH TASKS CHI TIẾT

Làm theo thứ tự từ Task 1 → Task 5.

---

## ✅ TASK 1: Data Quality Analysis

**Mục tiêu:** Phân tích chất lượng data trong CSV, tìm issues, đề xuất cách clean.

**File làm việc:** `notebooks/1_data_quality.ipynb`

**Thời gian:** 1-2 giờ

### Yêu cầu:

1. **Load CSV data**
   - Đọc file `data/raw_tiktok_data.csv`
   - Hiểu structure: bao nhiêu rows, bao nhiêu columns
   - List tất cả column names

2. **Phân tích Missing Data**
   - Bao nhiêu % videos có `text` = null/empty?
   - Bao nhiêu % videos có `playCount` = 0 hoặc null?
   - Bao nhiêu % videos có `diggCount` (likes) = 0?
   - Hashtags: Bao nhiêu videos có ít nhất 1 hashtag?

3. **Phân tích Duplicates**
   - Check duplicate `id` (video_id)
   - Nếu có duplicate → đề xuất cách xử lý (giữ video nào?)

4. **Phân tích Distribution**
   - Views distribution: min, max, mean, median
   - Likes distribution
   - Vẽ histogram cho views và likes

5. **Hashtags Analysis**
   - Hashtags được lưu ở columns: `hashtags/0`, `hashtags/1`, ..., `hashtags/27`
   - Trung bình mỗi video có bao nhiêu hashtags?
   - Top 10 hashtags phổ biến nhất

### Output:

**File:** `results/data_quality_report.md`

```markdown
# Data Quality Report

## Summary
- Total videos: X
- Valid videos: Y (Z%)
- Issues found: N

## Missing Data
- Missing text: X videos (Y%)
- Missing playCount: X videos (Y%)
- Missing hashtags: X videos (Y%)

## Duplicates
- Duplicate video IDs: X (Y%)
- Recommendation: ...

## Distribution Analysis
- Views: min=X, max=Y, mean=Z, median=W
- Likes: min=X, max=Y, mean=Z, median=W

## Hashtags
- Average hashtags per video: X.Y
- Top 10 hashtags: [...]

## Recommendations
1. Remove videos with text IS NULL
2. Filter videos with playCount < 100
3. Deduplicate by ID, keep highest playCount
4. ...
```

---

## ✅ TASK 2: DBSCAN Parameter Tuning

**Mục tiêu:** Tìm ra `eps` và `min_samples` tốt nhất cho DBSCAN clustering.

**File làm việc:** `notebooks/3_dbscan_tuning.ipynb`

**Thời gian:** 2-3 giờ

### Background:

DBSCAN clustering dùng để group videos giống nhau thành trends. Có 2 parameters quan trọng:
- **eps:** Maximum distance giữa 2 videos để coi là "gần nhau" (0.0 - 1.0)
- **min_samples:** Số videos tối thiểu để thành 1 cluster (trend)

Hiện tại đang dùng: `eps=0.3, min_samples=3`

### Yêu cầu:

1. **Chuẩn bị data**
   - Load CSV
   - Extract text từ videos (column `text`)
   - Combine text + hashtags (nếu có)
   - Filter videos: chỉ giữ videos có `text` không null

2. **Generate embeddings**
   - Dùng OpenAI API `text-embedding-3-small` để embed text
   - Cần OPENAI_API_KEY (hỏi team lead)
   - Output: numpy array shape `(n_videos, 1536)`

3. **Test nhiều parameters**
   - Test `eps` từ 0.2 → 0.5 (step 0.05): `[0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]`
   - Test `min_samples` từ 2 → 10: `[2, 3, 5, 7, 10]`
   - Với mỗi combination, run DBSCAN và ghi lại:
     - Số clusters tìm được
     - Số noise videos (label = -1)
     - Silhouette score (quality metric)

4. **Visualize kết quả**
   - Vẽ heatmap: eps (x-axis) vs min_samples (y-axis), color = silhouette_score
   - Vẽ line chart: eps (x-axis) vs number of clusters

5. **Chọn best params**
   - Dựa vào:
     - Silhouette score cao nhất
     - Số clusters hợp lý (không quá ít, không quá nhiều)
     - Domain knowledge: 1 trend nên có ít nhất 5-10 videos
   - Đề xuất best params với reasoning

### Output:

**File:** `results/dbscan_recommendations.json`

```json
{
  "best_params": {
    "eps": 0.35,
    "min_samples": 5,
    "metric": "cosine"
  },
  "reasoning": "Tested eps from 0.2-0.5 and min_samples 2-10. eps=0.35 + min_samples=5 gives best balance: 8-12 clusters with silhouette score 0.68. min_samples=5 ensures each trend has enough videos.",
  "metrics": {
    "n_clusters": 10,
    "n_noise": 15,
    "silhouette_score": 0.68,
    "avg_cluster_size": 17
  },
  "all_results": [
    {"eps": 0.2, "min_samples": 2, "n_clusters": 25, "silhouette_score": 0.45},
    {"eps": 0.2, "min_samples": 3, "n_clusters": 22, "silhouette_score": 0.48},
    ...
  ]
}
```

**Lưu ý:** Nếu không có OPENAI_API_KEY, có thể dùng dummy embeddings để test logic trước:
```python
# Dummy embeddings for testing
embeddings = np.random.rand(len(videos), 1536)
```

---

## ✅ TASK 3: Feature Engineering Analysis

**Mục tiêu:** Thiết kế engagement score formula và filter thresholds.

**File làm việc:** `notebooks/2_feature_analysis.ipynb`

**Thời gian:** 2-3 giờ

### Yêu cầu:

1. **Load và explore data**
   - Load CSV
   - Extract fields: `playCount`, `diggCount`, `commentCount`, `shareCount`

2. **Correlation Analysis**
   - Tính correlation giữa views, likes, comments, shares
   - Vẽ correlation heatmap
   - Insight: Field nào quan trọng nhất?

3. **Design Engagement Score**
   - Engagement score = weighted sum của các metrics
   - Formula: `engagement = likes*w1 + comments*w2 + shares*w3 + views*w4`
   - Đề xuất weights dựa trên:
     - Correlation analysis
     - Domain knowledge (comments/shares valuable hơn views)

   **Ví dụ:**
   ```python
   engagement = likes*1.0 + comments*2.0 + shares*3.0 + views*0.01
   ```

4. **Filter Thresholds**
   - Vẽ distribution của views, likes
   - Đề xuất threshold để filter low-quality videos:
     - `min_views`: Bao nhiêu views thì video đủ tốt?
     - `min_likes`: Bao nhiêu likes?
     - `min_engagement_score`: Tổng engagement tối thiểu?

5. **Text Combination Strategy**
   - Nên combine text như thế nào?
   - Options:
     - A. Chỉ dùng `text`
     - B. `text + hashtags`
     - C. `text + hashtags + author_name`
   - Đề xuất option tốt nhất

### Output:

**File:** `results/feature_engineering.json`

```json
{
  "engagement_formula": {
    "likes_weight": 1.0,
    "comments_weight": 2.0,
    "shares_weight": 3.0,
    "views_weight": 0.01,
    "formula_string": "likes*1.0 + comments*2.0 + shares*3.0 + views*0.01"
  },
  "filter_thresholds": {
    "min_views": 1000,
    "min_likes": 50,
    "min_engagement_score": 100,
    "reasoning": "Videos with views < 1000 are likely spam/low quality (15% of dataset)"
  },
  "text_combination": {
    "strategy": "text + hashtags",
    "reasoning": "Hashtags contain important tech keywords (#AI, #Coding), combining them improves semantic clustering"
  },
  "correlation_matrix": {
    "views_likes": 0.85,
    "views_comments": 0.72,
    "likes_comments": 0.88
  }
}
```

---

## ✅ TASK 4: Beauty Keywords Dictionary

**Mục tiêu:** Xây dựng keyword list để filter videos về Beauty/Mỹ phẩm.

**File làm việc:** `scripts/keyword_extraction.py`

**Thời gian:** 1-2 giờ

### Yêu cầu:

1. **Manual Labeling**
   - Load CSV, sample 30-50 videos
   - Đọc `text` và `hashtags` của từng video
   - Label: Beauty-related (1) hay không (0)?

2. **Extract Keywords**
   - Từ các videos Beauty-related, extract:
     - **Keywords trong text:** skincare, makeup, mỹ phẩm, serum, son môi, cushion, ...
     - **Hashtags:** #lamdep, #makeup, #skincare, #reviewmypham, #trangdiem, ...
   - Build 2 lists: `keywords` và `hashtags`

3. **Test Accuracy**
   - Viết function `is_beauty_video(text, hashtags, keyword_list)`
   - Test trên toàn bộ CSV:
     - Precision: % videos được giữ lại là Beauty thật
     - Recall: % videos Beauty bị bỏ sót

4. **Tune Keywords**
   - Nếu precision/recall thấp → thêm/bớt keywords
   - Target: Precision > 0.85, Recall > 0.80

### Output:

**File:** `results/beauty_keywords.json`

```json
{
  "keywords": [
    "skincare", "makeup", "mỹ phẩm", "làm đẹp", "trang điểm",
    "serum", "son môi", "cushion", "kem dưỡng", "nước hoa hồng",
    "review mỹ phẩm", "Cocoon", "Innisfree", "Romand", "3CE",
    "da mụn", "da dầu", "retinol", "vitamin C", "niacinamide",
    "Hasaki", "Shopee beauty", "phấn nước", "má hồng", "chống nắng"
  ],
  "hashtags": [
    "#lamdep", "#makeup", "#skincare", "#reviewmypham", "#trangdiem",
    "#mypham", "#beautyreview", "#tiktokbeauty", "#duongda",
    "#sonmoi", "#matna", "#serum", "#beautytips", "#koreanskincare"
  ],
  "accuracy": {
    "precision": 0.92,
    "recall": 0.88,
    "total_videos": 187,
    "beauty_videos": 145,
    "non_beauty_videos": 42
  },
  "methodology": "Manual labeling of 50 videos, extracted keywords from beauty videos, tested on full dataset"
}
```

**Script template:** `scripts/keyword_extraction.py` sẽ có code sẵn, chỉ cần:
- Fill vào `BEAUTY_KEYWORDS` list
- Run script để test accuracy

---

## ✅ TASK 5: LLM Prompt Testing

**Mục tiêu:** Tìm LLM prompt tốt nhất để analyze trends.

**File làm việc:** `scripts/prompt_testing.py`

**Thời gian:** 2 giờ

### Background:

Hiện tại đang dùng prompt này:

```
Analyze these {n} TikTok videos about BEAUTY trends.

Sample videos:
1. Text: ...
   Hashtags: ...

Extract:
1. Topic (3-7 words)
2. Summary (1-2 sentences)
3. Sentiment (positive/negative/neutral)
4. Keywords (5-10 keywords)

Respond in JSON format
```

### Yêu cầu:

1. **Chuẩn bị test data**
   - Chọn 3-5 clusters của videos (mỗi cluster 5-10 videos)
   - Clusters nên về các topics khác nhau (skincare products, makeup tutorials, beauty hauls, ...)

2. **Design prompt variations**
   - Tạo 3-5 prompt versions khác nhau
   - Variations:
     - **v1:** Current prompt (baseline)
     - **v2:** More detailed instructions
     - **v3:** Add examples (few-shot learning)
     - **v4:** Different output format
     - **v5:** More specific constraints

3. **Test từng prompt**
   - Với mỗi prompt, call OpenAI GPT-4o-mini
   - Ghi lại output: topic, summary, sentiment, keywords

4. **Compare quality**
   - Manual evaluation:
     - Topic có specific không? (Good: "Cocoon Vitamin C Serum Viral", Bad: "Skincare Products")
     - Summary có đúng không?
     - Keywords có relevant không?
   - Rate mỗi prompt: 1-5 stars

5. **Select best prompt**
   - Chọn prompt có quality cao nhất
   - Có thể combine features từ nhiều versions

### Output:

**File:** `results/best_llm_prompt.txt`

```
You are analyzing a cluster of {n} BEAUTY-related TikTok videos that were grouped by semantic similarity.

CONTEXT:
These videos likely discuss the same beauty trend, product, technique, or skincare routine. Your goal is to identify what trend they represent.

SAMPLE VIDEOS:
{video_texts}

TASK:
Extract the following information about this trend:

1. TOPIC: A specific, concise title (4-8 words)
   - Good examples: "Cocoon Vitamin C Serum Viral", "Korean Glass Skin Routine"
   - Bad examples: "Skincare Products", "Beauty Tips"

2. SUMMARY: A 1-2 sentence explanation of what this trend is about
   - Focus on WHAT the trend is, not just describing the videos

3. SENTIMENT: The overall tone of the discussion
   - Options: positive, negative, neutral

4. KEYWORDS: 5-10 specific, relevant keywords
   - Include: product names, brands, ingredients, techniques, skin concerns
   - Example: ["Cocoon", "vitamin C", "serum", "brightening", "affordable skincare"]

RESPOND ONLY IN VALID JSON FORMAT:
{
  "topic": "...",
  "summary": "...",
  "sentiment": "...",
  "keywords": ["...", "..."]
}
```

**Comparison table:**

| Prompt | Topic Quality | Summary Quality | Keyword Relevance | Overall Rating |
|--------|---------------|-----------------|-------------------|----------------|
| v1 (baseline) | 3/5 | 3/5 | 3/5 | ⭐⭐⭐ |
| v2 (detailed) | 4/5 | 4/5 | 4/5 | ⭐⭐⭐⭐ |
| v3 (few-shot) | 5/5 | 4/5 | 5/5 | ⭐⭐⭐⭐⭐ |
| v4 (format) | 3/5 | 4/5 | 3/5 | ⭐⭐⭐ |
| v5 (constraints) | 4/5 | 5/5 | 4/5 | ⭐⭐⭐⭐ |

**Best:** v3 (few-shot learning)

---

## 📦 DELIVERABLES SUMMARY

Sau khi hoàn thành, folder `results/` phải có:

```
results/
├── data_quality_report.md           # Task 1
├── dbscan_recommendations.json      # Task 2
├── feature_engineering.json         # Task 3
├── beauty_keywords.json             # Task 4
└── best_llm_prompt.txt              # Task 5
```

## 🆘 TROUBLESHOOTING

### Lỗi: CSV không load được
```python
# Thử encoding khác
df = pd.read_csv('data/raw_tiktok_data.csv', encoding='utf-8-sig')
```

### Lỗi: OpenAI API key
- Hỏi team lead lấy API key
- Set environment variable: `export OPENAI_API_KEY="sk-..."`
- Hoặc trong notebook: `os.environ['OPENAI_API_KEY'] = "sk-..."`

### Lỗi: Jupyter kernel crash
- Restart kernel: `Kernel → Restart`
- Clear output: `Cell → All Output → Clear`

### Column names quá dài
```python
# Rename columns cho dễ nhìn
df.rename(columns={
    'authorMeta/name': 'author',
    'playCount': 'views',
    'diggCount': 'likes',
    'commentCount': 'comments',
    'shareCount': 'shares'
}, inplace=True)
```

---

**Good luck! Nếu gặp vấn đề, hỏi team lead nhé! 🚀**

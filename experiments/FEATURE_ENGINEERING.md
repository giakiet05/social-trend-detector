 ---
  🎯 ĐÚNG! FEATURE ENGINEERING GIÚP THIẾT KẾ MODEL

  Vấn đề gốc mày nói lúc đầu:

  "Không đồng bộ model giữa producer và consumer"

  Nghĩa là:

  Hiện tại - KHÔNG ĐỒNG BỘ:

  Producer model (đang send vào Kafka):
  # producer gửi gì?? (chưa rõ, vì chưa có code producer)
  {
    "video_id": "...",
    "text": "...",
    "hashtags": [...],
    "likes": ...,
    "views": ...,
    # Còn gì nữa? Comments? Shares? Engagement score?
  }

  Consumer model (đang expect từ Kafka):
  # consumer/models/schemas.py
  @dataclass
  class TikTokVideo:
      video_id: str
      text: str
      hashtags: List[str]
      likes: int
      comments: int
      shares: int
      views: int
      author: str
      timestamp: Optional[str] = None

  VẤN ĐỀ:
  - Producer gửi gì → chưa rõ (tao chưa thấy code producer)
  - Consumer expect gì → đã rõ
  - CSV có gì → hàng trăm fields (playCount, diggCount, commentCount, shareCount, authorMeta/name, hashtags/0-27, ...)

  → 3 THẰNG KHÔNG KHỚP NHAU!

  ---
  🔧 FEATURE ENGINEERING GIÚP THIẾT KẾ MODEL CHUNG

  Feature Engineering sẽ trả lời:

  Câu hỏi 1: Fields nào cần thiết?

  Data guy sẽ analyze correlation:

  # Correlation matrix:
  #         views   likes  comments  shares
  # views    1.00    0.85      0.72    0.65
  # likes    0.85    1.00      0.88    0.75
  # comments 0.72    0.88      1.00    0.82
  # shares   0.65    0.75      0.82    1.00

  Kết luận:
  - ✅ CẦN: text, hashtags, views, likes, comments, shares (6 fields)
  - ❌ KHÔNG CẦN: author (không giúp clustering), timestamp (có thể optional)
  - ❌ KHÔNG CẦN: 100+ fields khác trong CSV (authorMeta/avatar, musicMeta/..., videoMeta/...)

  ---
  Câu hỏi 2: Fields nào nên combine/derive?

  Data guy sẽ đề xuất:

  {
    "derived_features": {
      "combined_text": "text + hashtags",  // For embedding
      "engagement_score": "likes*1 + comments*2 + shares*3 + views*0.01"  // For filtering
    }
  }

  Nghĩa là:
  - Model KHÔNG NÊN chỉ có text
  - Model NÊN CÓ combined_text (derived field)
  - Model NÊN CÓ engagement_score (derived field)

  ---
  
  📊 FLOW HOÀN CHỈNH

  CSV (hàng trăm fields)
      ↓
  [FEATURE ENGINEERING ANALYSIS]  ← Data guy làm
      ↓
  Chọn 8 fields: video_id, text, hashtags, views, likes, comments, shares, author
      ↓
  [SHARED MODEL: common/models.py]
      ↓
      ├─→ [PRODUCER]
      │      ├─ Read CSV
      │      ├─ TikTokVideo.from_csv_row()  ← Convert 100+ fields → 8 fields
      │      └─ Send to Kafka (8 fields only)
      │
      └─→ [CONSUMER]
             ├─ Read from Kafka (expect 8 fields)  ← KHỚP!
             ├─ TikTokVideo object
             ├─ Compute derived features:
             │    - combined_text = text + hashtags
             │    - engagement_score = formula
             ├─ Filter by engagement
             ├─ Embed combined_text
             └─ Cluster

  ---
  ✅ TÓM LẠI

  Câu hỏi của mày:
  "Có phải feature engineering giúp tìm ra các field cho model không?"

  Trả lời: ĐÚNG 100%!

  Feature Engineering giúp:

  1. ✅ Chọn fields nào cần thiết (từ 100+ fields CSV → 8 fields)
    - Core: video_id, text, hashtags
    - Metrics: views, likes, comments, shares
    - Metadata: author (optional)
  2. ✅ Thiết kế derived fields (features mới)
    - combined_text = text + hashtags
    - engagement_score = weighted sum
  3. ✅ Đồng bộ Producer ↔ Consumer
    - Producer send: 8 fields
    - Consumer expect: 8 fields (cùng schema)
    - Cùng dùng common/models.py
  4. ✅ Filter/Quality logic
    - Thresholds: min_views, min_likes, min_engagement
    - Formula: engagement score


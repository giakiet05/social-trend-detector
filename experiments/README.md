# 📊 EXPERIMENTS - Data Analysis Tasks

Folder này chứa các tasks phân tích data để tối ưu hóa hệ thống TikTok Trend Detection.

## 🎯 MỤC ĐÍCH

Thực hiện các experiments để tìm ra:
1. **DBSCAN parameters tốt nhất** (eps, min_samples)
2. **Feature engineering strategy** (engagement score, text combination)
3. **Tech keywords dictionary** để filter videos
4. **Data quality issues** cần fix
5. **LLM prompt tốt nhất** để analyze trends

## 📁 CẤU TRÚC FOLDER

```
experiments/
├── README.md                    # File này - hướng dẫn tổng quan
├── TASKS.md                     # Danh sách tasks chi tiết (ĐỌC FILE NÀY TRƯỚC!)
├── data/
│   └── raw_tiktok_data.csv     # CSV data từ TikTok scraper (187 videos)
├── notebooks/                   # Jupyter notebooks cho analysis
│   ├── 1_data_quality.ipynb
│   ├── 2_feature_analysis.ipynb
│   └── 3_dbscan_tuning.ipynb
├── scripts/                     # Python scripts
│   ├── keyword_extraction.py
│   └── prompt_testing.py
├── results/                     # OUTPUT - Lưu kết quả analysis ở đây
│   ├── dbscan_recommendations.json
│   ├── feature_engineering.json
│   ├── tech_keywords.json
│   ├── data_quality_report.md
│   └── best_llm_prompt.txt
└── requirements.txt             # Dependencies cần install
```

## 🚀 SETUP

### 1. Cài đặt dependencies

```bash
cd experiments
pip install -r requirements.txt
```

### 2. Khởi động Jupyter Notebook

```bash
jupyter notebook
```

### 3. Đọc file TASKS.md

Đọc file `TASKS.md` để biết phải làm gì theo thứ tự.

## 📊 VỀ DATA

### File: `data/raw_tiktok_data.csv`

- **Nguồn:** TikTok scraper (Apify)
- **Số lượng:** 187 videos
- **Format:** CSV với nhiều columns (authorMeta, hashtags, videoMeta, etc.)

### Các fields TIỀM NĂNG hữu ích:

  **LƯU Ý:** Đây là danh sách gợi ý fields **CÓ THỂ** hữu ích.
  **NHIỆM VỤ của bạn:** Analyze data để xác nhận fields nào **THẬT SỰ** cần thiết. Có thể thêm mới hoặc bỏ bớt field nếu cần

| Field | Mô tả | Ví dụ |
|-------|-------|-------|
| `id` | Video ID | "7565574004866600214" |
| `text` | Nội dung caption | "🩷 #fypシ゚viral #xyzbca..." |
| `hashtags/0`, `hashtags/1`, ... | Hashtags (tách riêng từng cột) | "fypシ゚viral", "xyzbca" |
| `playCount` | Lượt xem | 126800 |
| `diggCount` | Lượt like | 22000 |
| `commentCount` | Lượt comment | 2313 |
| `shareCount` | Lượt share | 289 |
| `authorMeta/name` | Tên author | "juliaxgri1" |
| `createTime` | Unix timestamp | 1761497469 |
| `createTimeISO` | ISO timestamp | "2025-10-26T16:51:09.000Z" |

**LƯU Ý:** Hashtags được tách thành nhiều columns: `hashtags/0`, `hashtags/1`, ... `hashtags/27`

## 📝 DELIVERABLES (Kết quả cần nộp)

Sau khi hoàn thành tất cả tasks, folder `results/` phải có các files:

### 1. `dbscan_recommendations.json`
```json
{
  "best_params": {
    "eps": 0.35,
    "min_samples": 5
  },
  "reasoning": "...",
  "metrics": {
    "n_clusters": 10,
    "silhouette_score": 0.68
  }
}
```

### 2. `feature_engineering.json`
```json
{
  "engagement_formula": {
    "likes_weight": 1.0,
    "comments_weight": 2.0,
    "shares_weight": 3.0,
    "views_weight": 0.01
  },
  "filter_thresholds": {
    "min_views": 1000,
    "min_likes": 50
  },
  "text_combination": "text + hashtags"
}
```

### 3. `tech_keywords.json`
```json
{
  "keywords": ["AI", "tech", "coding", "programming", ...],
  "hashtags": ["#TechTok", "#AI", "#Coding", ...],
  "accuracy": {
    "precision": 0.92,
    "recall": 0.88
  }
}
```

### 4. `data_quality_report.md`
Markdown file với analysis về:
- Missing data
- Duplicates
- Data distribution
- Recommendations

### 5. `best_llm_prompt.txt`
Text file chứa LLM prompt tốt nhất để analyze trends.

## 🆘 CẦN TRỢ GIÚP?

- **Notebooks không chạy?** → Check xem đã cài `requirements.txt` chưa
- **CSV không load được?** → Check path: `../data/raw_tiktok_data.csv`
- **Không hiểu task?** → Đọc kỹ file `TASKS.md`, có hướng dẫn chi tiết

## ✅ CHECKLIST

Hoàn thành các tasks theo thứ tự:

- [ ] Task 1: Data Quality Analysis (1-2 giờ)
- [ ] Task 2: DBSCAN Parameter Tuning (2-3 giờ)
- [ ] Task 3: Feature Engineering Analysis (2-3 giờ)
- [ ] Task 4: Tech Keywords Dictionary (1-2 giờ)
- [ ] Task 5: LLM Prompt Testing (2 giờ)

**Total time estimate:** 8-12 giờ

---

Good luck! 🚀

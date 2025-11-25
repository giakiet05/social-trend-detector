# 🚀 QUICK START GUIDE

Bắt đầu ngay trong 5 phút!

## ⚡ SETUP NHANH

### 1. Cài đặt dependencies

```bash
cd experiments
pip install -r requirements.txt
```

Hoặc nếu dùng virtual environment:

```bash
cd experiments
python -m venv venv
source venv/bin/activate  # Linux/Mac
# Hoặc: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Setup OpenAI API Key (cho Task 2 và 5)

Hỏi team lead lấy API key, sau đó:

```bash
export OPENAI_API_KEY="sk-..."
```

Hoặc tạo file `.env` trong folder `experiments/`:

```
OPENAI_API_KEY=sk-...
```

### 3. Khởi động Jupyter Notebook

```bash
jupyter notebook
```

Browser sẽ tự động mở. Navigate vào folder `notebooks/`.

---

## 📝 LÀM TASKS THEO THỨ TỰ

### ✅ Task 1: Data Quality (BẮT ĐẦU Ở ĐÂY)

1. Mở file `notebooks/1_data_quality.ipynb`
2. Run từng cell từ trên xuống
3. Fill vào các TODO
4. Check output: `results/data_quality_report.md`

**Time:** 1-2 giờ

---

### ✅ Task 2: DBSCAN Tuning

1. Mở file `notebooks/3_dbscan_tuning.ipynb`
2. Nếu có OPENAI_API_KEY → Set `USE_DUMMY_EMBEDDINGS = False`
3. Nếu chưa có API key → Dùng dummy embeddings để test
4. Run notebook, analyze charts
5. Chọn best params
6. Check output: `results/dbscan_recommendations.json`

**Time:** 2-3 giờ

---

### ✅ Task 3: Feature Engineering

1. Mở file `notebooks/2_feature_analysis.ipynb`
2. Run analysis
3. Design engagement formula
4. Đề xuất filter thresholds
5. Check output: `results/feature_engineering.json`

**Time:** 2-3 giờ

---

### ✅ Task 4: Keywords Extraction

1. Chạy script:
   ```bash
   cd scripts
   python keyword_extraction.py
   ```
2. Đọc sample videos được in ra
3. Mở file `keyword_extraction.py`, thêm keywords vào `BEAUTY_KEYWORDS`
4. Chạy lại script
5. Check output: `results/beauty_keywords.json`

**Time:** 1-2 giờ

---

### ✅ Task 5: Prompt Testing

1. Cần OPENAI_API_KEY
2. Chạy script:
   ```bash
   cd scripts
   python prompt_testing.py
   ```
3. Review output của từng prompt
4. Fill ratings vào code
5. Chọn best prompt
6. Check output: `results/best_llm_prompt.txt`

**Time:** 2 giờ

---

## 📦 DELIVERABLES

Sau khi xong, folder `results/` phải có:

```
results/
├── data_quality_report.md
├── dbscan_recommendations.json
├── feature_engineering.json
├── beauty_keywords.json
└── best_llm_prompt.txt
```

Gửi toàn bộ folder `results/` cho team lead!

---

## 🆘 TROUBLESHOOTING

### Lỗi: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

### Lỗi: `FileNotFoundError: data/raw_tiktok_data.csv`
Check xem đang ở đúng folder `experiments/` chưa:
```bash
pwd  # Should show: .../tiktok-trend-detector/experiments
```

### Lỗi: OpenAI API key
```bash
export OPENAI_API_KEY="sk-..."
```

### Jupyter kernel crash
- Kernel → Restart
- Cell → All Output → Clear

---

## 📞 CONTACT

Gặp vấn đề? Hỏi team lead!

Good luck! 🚀

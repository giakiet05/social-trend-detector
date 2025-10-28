
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

# Apify Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
# Đây là ID của "TikTok Scraper" actor trên Apify, mày cần thay thế bằng ID của mày
TIKTOK_SCRAPER_ACTOR_ID = "your_apify_actor_id"

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
RAW_DATA_TOPIC = "raw-tiktok-data"

# Scraping Strategies Configuration
SEARCH_KEYWORDS = [
    "review phim", "drama", "biến căng", "unboxing", "daily vlog", 
    "outfit ideas", "goc lam dep", "make up", "skincare", "funny",
    "dance trend", "cover", "game", "the thao", "am thuc",
    "du lich", "learn on tiktok", "startup", "AI", "technology"
]

HASHTAGS = [
    "xuhuong", "fyp", "viral", "trending", "thinhhanh"
]

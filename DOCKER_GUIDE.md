# Docker Deployment Guide

Hướng dẫn chạy toàn bộ hệ thống Social Trend Detector bằng Docker Compose.

## Yêu cầu

- Docker
- Docker Compose
- File `.env` với các API keys cần thiết

## Kiến trúc

Docker Compose sẽ chạy 4 services:

1. **Kafka**: Message broker cho data streaming
2. **MongoDB**: Database lưu trữ trends
3. **Backend**: Producer + Consumer (chạy mỗi 4 tiếng)
4. **Dashboard**: Streamlit web dashboard

## Cách chạy

### 1. Build và start tất cả services

```bash
docker-compose up -d --build
```

### 2. Xem logs

Xem logs của tất cả services:
```bash
docker-compose logs -f
```

Xem logs của từng service:
```bash
docker-compose logs -f backend
docker-compose logs -f dashboard
docker-compose logs -f kafka
docker-compose logs -f mongodb
```

### 3. Truy cập Dashboard

Mở browser và vào: http://localhost:8501

### 4. Stop services

```bash
docker-compose down
```

### 5. Stop và xóa data

```bash
docker-compose down -v
```

## Cấu trúc Services

### Backend
- Build từ `Dockerfile`
- Chạy `main.py` để orchestrate Producer và Consumer
- Schedule: chạy ngay khi start, sau đó lặp lại mỗi 4 tiếng
- Mount checkpoint folder để lưu trạng thái
- Kết nối với Kafka (kafka:29092) và MongoDB

### Dashboard
- Build từ `dashboard/Dockerfile`
- Chạy Streamlit app
- Port: 8501
- Chỉ cần kết nối MongoDB để đọc trends

### Kafka
- Image: confluentinc/cp-kafka
- Ports:
  - 9092: External (host machine)
  - 29092: Internal (Docker network)
- Tự động tạo topics khi cần

### MongoDB
- Image: mongo:latest
- Port: 27017
- Credentials: admin/password

## Troubleshooting

### Backend không kết nối được Kafka

Kiểm tra Kafka đã start chưa:
```bash
docker-compose ps kafka
```

Restart Kafka:
```bash
docker-compose restart kafka
```

### Dashboard không hiển thị data

1. Kiểm tra MongoDB có data chưa:
```bash
docker exec -it mongodb mongosh -u admin -p password
> use tiktok_trends
> db.trends.countDocuments()
```

2. Xem logs backend để đảm bảo pipeline chạy thành công:
```bash
docker-compose logs backend
```

### Thay đổi schedule time

Sửa file `main.py`, dòng 94:
```python
trigger=IntervalTrigger(hours=4),  # Đổi thành hours=1 cho 1 tiếng
```

Rebuild:
```bash
docker-compose up -d --build backend
```

## Development

Nếu muốn chạy từng phần riêng lẻ:

### Chỉ chạy Kafka + MongoDB
```bash
docker-compose up -d kafka mongodb
```

### Chạy Backend local, chỉ dùng Kafka + MongoDB từ Docker
```bash
docker-compose up -d kafka mongodb
uv run python main.py
```

### Chạy Dashboard local
```bash
docker-compose up -d mongodb
cd dashboard && uv run streamlit run app.py
```

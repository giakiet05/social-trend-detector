"""
Analysis stage: LLM analysis of clusters to detect trends (multi-source).
"""

from typing import List, Dict
import logging
import time
from datetime import datetime
from collections import Counter
from .base_stage import BaseStage
from common.models import ContentItem
from consumer.enrichment.base_llm_client import BaseLLMClient
from consumer.models.schemas import Trend
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class AnalysisStage(BaseStage):
    """Analyze clusters using LLM to extract trend information (multi-source support)."""

    def __init__(self, llm_client: BaseLLMClient):
        super().__init__("AnalysisStage")
        self.llm_client = llm_client
        self.sample_count = settings.processing.SAMPLE_VIDEOS_COUNT

    def execute(self, clusters: Dict[int, List[ContentItem]]) -> List[Trend]:
        """
        Analyze each cluster with LLM (multi-source support).

        Args:
            clusters: Dict mapping cluster_id -> ContentItems

        Returns:
            List of Trend objects
        """
        self.log_start()

        if not clusters:
            self.log_skip("No clusters to analyze")
            return []

        trends = []

        for cluster_id, cluster_items in clusters.items():
            # Count sources
            source_counts = Counter(item.source for item in cluster_items)
            source_str = ", ".join([f"{s}: {c}" for s, c in source_counts.items()])
            logger.info(f"   Analyzing cluster {cluster_id}: {len(cluster_items)} items ({source_str})")

            try:
                start_time = time.time()

                # Rank items by engagement score
                ranked_items = self._rank_by_engagement(cluster_items)

                # Select top 10 for LLM analysis (cost optimization)
                top_items = ranked_items[:10]

                # LLM analysis (with multi-source context)
                analysis = self._analyze_cluster(top_items, source_counts)

                # Rate limiting: ensure minimum 5s between LLM calls
                elapsed = time.time() - start_time
                if elapsed < 5:
                    sleep_time = 5 - elapsed
                    logger.debug(f"   Rate limiting: sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)

                # Calculate stats from ALL items in cluster
                total_views = sum(item.views or 0 for item in cluster_items)
                total_likes = sum(item.likes or 0 for item in cluster_items)

                # Sample items: top N by engagement (convert to dict for MongoDB)
                sample_items = [self._item_to_sample_dict(item) for item in ranked_items[:self.sample_count]]

                # Create Trend object
                trend = Trend(
                    timestamp=datetime.utcnow(),
                    topic=analysis['topic'],
                    summary=analysis['summary'],
                    sentiment=analysis['sentiment'],
                    keywords=analysis['keywords'],
                    video_count=len(cluster_items),
                    total_views=total_views,
                    total_likes=total_likes,
                    sample_videos=sample_items,
                    source_counts=dict(source_counts),
                    content_type=analysis.get('content_type', 'entertainment'),
                    risk_level=analysis.get('risk_level', 'safe'),
                    guidelines=analysis.get('guidelines', {})
                )

                trends.append(trend)

                logger.info(f"      → Topic: {trend.topic}")
                logger.info(f"      → Sentiment: {trend.sentiment}")
                logger.info(f"      → Items: {trend.video_count}, Views: {total_views:,}")

            except Exception as e:
                logger.error(f"Failed to analyze cluster {cluster_id}: {e}", exc_info=True)
                continue

        self.log_complete(f"Analyzed {len(trends)} trends")
        return trends

    def _analyze_cluster(self, items: List[ContentItem], source_counts: Counter) -> Dict:
        """Phân tích cụm nội dung bằng LLM với prompt tiếng Việt."""

        # Xây dựng thông tin nguồn
        source_info = []
        for source, count in source_counts.items():
            source_name = {
                'tiktok': 'TikTok',
                'vnexpress': 'VNExpress',
                'youtube': 'YouTube',
                'google_trends': 'Google Trends'
            }.get(source, source.upper())
            source_info.append(f"- {source_name}: {count} nội dung")

        # Xây dựng prompt tiếng Việt với guidelines
        prompt = f"""Phân tích xu hướng từ dữ liệu mạng xã hội:

NGUỒN DỮ LIỆU:
{chr(10).join(source_info)}

NỘI DUNG MẪU ({len(items)} nội dung đầu):
"""

        for i, item in enumerate(items, 1):
            source_name = {
                'tiktok': 'TikTok',
                'vnexpress': 'Tin tức',
                'youtube': 'YouTube',
                'google_trends': 'Tìm kiếm'
            }.get(item.source, item.source)

            prompt += f"\n{i}. [{source_name}] {item.text[:300]}"

        prompt += """

YÊU CẦU: Trả về JSON với cấu trúc sau:
{
  "topic": "Tên chủ đề chính",
  "summary": "Tóm tắt xu hướng (2-3 câu giải thích)",
  "sentiment": "positive/negative/neutral",
  "keywords": ["từ khóa 1", "từ khóa 2", "..."],

  "content_type": "entertainment/drama/dangerous/social_issue/commercial",
  "risk_level": "safe/cautious/high_risk/dangerous",

  "guidelines": {
    "for_marketers": {
      "should_participate": true/false,
      "summary": "Tóm tắt ngắn gọn 1 câu có nên tham gia không",
      "recommendations": ["Gợi ý 1", "Gợi ý 2", "Gợi ý 3"],
      "warnings": ["Cảnh báo 1", "Cảnh báo 2"],
      "detailed_advice": "Phân tích chi tiết 2-3 câu về cách tiếp cận trend này"
    },
    "for_social_managers": {
      "intervention_needed": true/false,
      "summary": "Tóm tắt 1 câu có cần can thiệp không",
      "actions": ["Hành động 1", "Hành động 2"],
      "monitoring_points": ["Điểm cần theo dõi 1", "Điểm cần theo dõi 2"],
      "detailed_analysis": "Phân tích chi tiết 2-3 câu về mức độ rủi ro và cách xử lý"
    }
  }
}

QUAN TRỌNG - Quy tắc đặt tên topic:
- Tên ngắn gọn, cụ thể, dễ hiểu
- Tập trung vào tên người, sự kiện, sản phẩm chính
- KHÔNG dùng: "xu hướng", "chuyên đề", "nội dung", "sự nổi bật"
- KHÔNG mô tả dài dòng, chỉ nêu tên chủ đề

VÍ DỤ TỐT:
- "Phở anh Hai" (thay vì "Xu hướng game quán phở...")
- "Zootopia 2" (thay vì "Xu hướng phim hoạt hình...")
- "Aura Farming" (thay vì "Xu hướng Aura Farming...")
- "Cloudflare sập" (thay vì "Sự cố Cloudflare...")

QUAN TRỌNG - Quy tắc viết summary:
- ĐI THẲNG VÀO NỘI DUNG, không mở đầu bằng "Xu hướng này tập trung vào...", "Xu hướng này xoay quanh...", "Nội dung này..."
- Viết trực tiếp về hiện tượng/sự kiện/nhân vật
- 2-3 câu ngắn gọn, súc tích

VÍ DỤ TỐT:
- "Game quán phở của anh Hai đang viral vì gameplay độc đáo và câu nói 'ăn phở không' trở thành meme. Người chơi thích thú với cách anh Hai phục vụ khách hàng hài hước."
- "Phim Zootopia 2 vừa ra trailer mới khiến fan phấn khích. Trailer hé lộ những nhân vật mới và cốt truyện hấp dẫn hơn phần 1."

VÍ DỤ XẤU (TRÁNH):
- "Xu hướng này tập trung vào game quán phở của anh Hai..."
- "Xu hướng xoay quanh việc Zootopia 2 ra trailer..."
- "Nội dung này nói về..."

KEYWORDS: 5-10 từ khóa quan trọng nhất

HƯỚNG DẪN PHÂN LOẠI:

Content Type:
- "entertainment": Giải trí vô hại (meme, dance, challenge lành mạnh)
- "drama": Drama người nổi tiếng, scandal, bóc phốt
- "dangerous": Nội dung nguy hiểm (tự hại, bạo lực, ma túy)
- "social_issue": Vấn đề xã hội (chính trị, tham nhũng, bất công)
- "commercial": Sản phẩm/dịch vụ viral

Risk Level:
- "safe": An toàn, brands có thể tham gia thoải mái
- "cautious": Cần cẩn trọng, có thể gây tranh cãi
- "high_risk": Rủi ro cao, dễ bị backlash
- "dangerous": Nguy hiểm, tuyệt đối không nên tham gia

Guidelines - For Marketers:
- should_participate: Đánh giá có nên tham gia trend không
- summary: Tóm tắt 1 câu ngắn gọn
- recommendations: Danh sách 3-5 gợi ý cụ thể (làm content thế nào, dùng hashtag gì,...)
- warnings: Những điều TRÁNH làm (2-3 items)
- detailed_advice: Phân tích chi tiết chiến lược tham gia (2-3 câu)

Guidelines - For Social Managers:
- intervention_needed: Có cần can thiệp/cảnh báo không
- summary: Tóm tắt 1 câu ngắn gọn
- actions: Hành động cần làm (nếu có) - remove content, warning, monitor,...
- monitoring_points: Những dấu hiệu cần theo dõi (2-3 items)
- detailed_analysis: Đánh giá tác động xã hội và rủi ro (2-3 câu)

VÍ DỤ CHO CÁC TRƯỜNG HỢP:

1. Positive Entertainment (Safe):
{
  "content_type": "entertainment",
  "risk_level": "safe",
  "guidelines": {
    "for_marketers": {
      "should_participate": true,
      "summary": "Trend tích cực, phù hợp để brands tham gia tạo nội dung vui vẻ",
      "recommendations": [
        "Tạo video nhân viên/sản phẩm tham gia challenge",
        "Dùng trending hashtags kết hợp brand hashtag",
        "Kêu gọi followers tham gia và tag brand"
      ],
      "warnings": [
        "Đảm bảo content phù hợp với brand personality",
        "Tránh làm quá lố làm mất tính authentic"
      ],
      "detailed_advice": "Đây là cơ hội tốt để tăng engagement và reach. Nên tạo version sáng tạo riêng thay vì copy y nguyên, kết hợp sản phẩm/thông điệp một cách tự nhiên."
    },
    "for_social_managers": {
      "intervention_needed": false,
      "summary": "Trend lành mạnh, không cần can thiệp",
      "actions": [],
      "monitoring_points": [
        "Theo dõi để đảm bảo không biến chất sang nội dung không phù hợp"
      ],
      "detailed_analysis": "Trend giải trí tích cực, không có dấu hiệu rủi ro xã hội. Chỉ cần monitoring thường xuyên."
    }
  }
}

2. Negative Drama (Cautious):
{
  "content_type": "drama",
  "risk_level": "cautious",
  "guidelines": {
    "for_marketers": {
      "should_participate": false,
      "summary": "Không nên tham gia trực tiếp, rủi ro bị liên lụy và backlash cao",
      "recommendations": [
        "Tránh hoàn toàn việc nhắc tên hoặc reference đến drama",
        "Nếu brand từng hợp tác với nhân vật liên quan, cần có statement distancing",
        "Có thể làm content về giá trị trái ngược (vd: transparency, honesty) nhưng không nhắc drama"
      ],
      "warnings": [
        "KHÔNG đùa cợt/meme về drama này - rất dễ bị chỉ trích",
        "KHÔNG cố gắng 'viral marketing' bằng cách leverage drama",
        "Cẩn thận với bất kỳ content nào có thể hiểu nhầm là supporting/attacking bên nào"
      ],
      "detailed_advice": "Drama người nổi tiếng rất unpredictable và polarizing. Brands tham gia sẽ bị scrutinize nặng và dễ mất điểm với một phần audience. Tốt nhất là giữ im lặng hoặc chỉ làm positive content về giá trị riêng của brand."
    },
    "for_social_managers": {
      "intervention_needed": true,
      "summary": "Cần monitoring để tránh mob violence, doxxing, misinformation",
      "actions": [
        "Theo dõi các keyword liên quan để phát hiện hate speech/threats",
        "Remove content có dấu hiệu doxxing (chia sẻ thông tin cá nhân)",
        "Đánh dấu và fact-check các claim chưa được verify"
      ],
      "monitoring_points": [
        "Mức độ lan truyền (có vượt khỏi tầm kiểm soát không)",
        "Dấu hiệu mob violence/organized harassment",
        "Fake news/deepfake được share"
      ],
      "detailed_analysis": "Drama có thể leo thang thành mob violence hoặc spread misinformation. Cần balance giữa free speech và protection. Ưu tiên remove nội dung nguy hại (threats, doxxing) nhưng cho phép discussion hợp lý."
    }
  }
}

3. Dangerous Content (Dangerous):
{
  "content_type": "dangerous",
  "risk_level": "dangerous",
  "guidelines": {
    "for_marketers": {
      "should_participate": false,
      "summary": "TUYỆT ĐỐI KHÔNG tham gia - rủi ro pháp lý và đạo đức cực cao",
      "recommendations": [],
      "warnings": [
        "KHÔNG nhắc đến trend dưới bất kỳ hình thức nào",
        "KHÔNG đùa cợt/meme về trend này",
        "Nếu sản phẩm của brand bị lạm dụng trong trend, phải issue safety warning ngay"
      ],
      "detailed_advice": "Trend này gây hại trực tiếp đến sức khỏe/tính mạng. Brands liên quan phải có public statement cảnh báo và có thể cần hợp tác với cơ quan chức năng. Tuyệt đối không được coi nhẹ hoặc cố leverage cho marketing."
    },
    "for_social_managers": {
      "intervention_needed": true,
      "summary": "CẦN CAN THIỆP KHẨN CẤP - nguy hiểm đến tính mạng",
      "actions": [
        "Ban/remove tất cả content liên quan ngay lập tức",
        "Issue public warning trên tất cả platforms",
        "Phối hợp với các platform khác để block trend",
        "Liên hệ cơ quan y tế/giáo dục để awareness campaign",
        "Report lên cơ quan chức năng nếu cần"
      ],
      "monitoring_points": [
        "Số lượng content mới được đăng (tốc độ lan truyền)",
        "Báo cáo về nạn nhân/người bị thương",
        "Phản ứng của cộng đồng (có người cảnh báo lại không)"
      ],
      "detailed_analysis": "Đây là tình huống khẩn cấp cần xử lý quyết liệt. Ưu tiên bảo vệ người dùng hơn free speech. Cần phối hợp đa ngành (platform, chính phủ, y tế, giáo dục) để ngăn chặn và giáo dục."
    }
  }
}

Bây giờ hãy phân tích trend từ nội dung trên và trả về JSON theo format đã cho.
"""

        # Call LLM
        return self.llm_client.analyze_cluster(prompt)

    def _rank_by_engagement(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Rank items by engagement score.

        Score = likes*1 + comments*2 + shares*3 + collects*4
        """
        def engagement_score(item: ContentItem):
            score = 0
            score += (item.likes or 0) * 1.0
            score += (item.comments or 0) * 2.0
            score += (item.shares or 0) * 3.0
            score += item.metadata.get('collects', 0) * 4.0
            return score

        return sorted(items, key=engagement_score, reverse=True)

    def _item_to_sample_dict(self, item: ContentItem) -> Dict:
        """Convert ContentItem to sample dict for MongoDB."""
        return {
            "content_id": item.content_id,
            "source": item.source,
            "text": item.text[:500],  # Truncate long text
            "url": item.url,
            "views": item.views,
            "likes": item.likes,
            "comments": item.comments,
            "author_name": item.author_name,
        }

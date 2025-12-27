"""
Socitrend - Bảng điều khiển xu hướng mạng xã hội
Theo dõi và phân tích xu hướng trên các nền tảng mạng xã hội
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from utils.mongo_client import DashboardMongoClient

# Page config
st.set_page_config(
    page_title="Socitrend - Xu hướng mạng xã hội",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF0050;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .sentiment-positive { background-color: #d1fae5; color: #065f46; }
    .sentiment-negative { background-color: #fee2e2; color: #991b1b; }
    .sentiment-neutral { background-color: #e5e7eb; color: #374151; }
    .risk-safe { background-color: #d1fae5; color: #065f46; }
    .risk-cautious { background-color: #fef3c7; color: #92400e; }
    .risk-high_risk { background-color: #fed7aa; color: #9a3412; }
    .risk-dangerous { background-color: #fee2e2; color: #991b1b; }
    .content-entertainment { background-color: #ddd6fe; color: #5b21b6; }
    .content-drama { background-color: #fecaca; color: #991b1b; }
    .content-dangerous { background-color: #dc2626; color: white; }
    .content-social_issue { background-color: #bfdbfe; color: #1e40af; }
    .content-commercial { background-color: #bbf7d0; color: #166534; }
</style>
""", unsafe_allow_html=True)

# Initialize MongoDB client
@st.cache_resource
def get_mongo_client():
    client = DashboardMongoClient()
    return client.connect()

mongo_client = get_mongo_client()

# Header
st.markdown('<h1 class="main-header">Socitrend</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Phân tích xu hướng mạng xã hội theo thời gian thực</p>', unsafe_allow_html=True)

refresh_button = st.sidebar.button("Làm mới dữ liệu", use_container_width=True)

# Keyword Submission Form
st.sidebar.markdown("---")
st.sidebar.header("Đề xuất xu hướng")

with st.sidebar.form("keyword_submission_form", clear_on_submit=True):
    keyword_input = st.text_input(
        "Từ khóa",
        placeholder="VD: Avatar 3",
        help="Nhập từ khóa bạn nghĩ đang trending"
    )
    reason_input = st.text_area(
        "Tại sao nó đang trending?",
        placeholder="Tôi thấy nó nhiều trên TikTok/YouTube...",
        height=80
    )
    name_input = st.text_input(
        "Tên/Email của bạn (không bắt buộc)",
        placeholder="Ẩn danh"
    )

    submit_button = st.form_submit_button("Gửi đề xuất", use_container_width=True)

    if submit_button:
        if not keyword_input or keyword_input.strip() == "":
            st.error("Vui lòng nhập từ khóa")
        elif not reason_input or reason_input.strip() == "":
            st.error("Vui lòng nhập lý do")
        else:
            # Import keyword manager
            import sys
            from pathlib import Path
            ROOT_DIR = Path(__file__).resolve().parents[1]
            sys.path.insert(0, str(ROOT_DIR))

            from common.keyword_manager import MongoKeywordManager

            try:
                manager = MongoKeywordManager()
                result = manager.submit_keyword(
                    keyword=keyword_input,
                    reason=reason_input if reason_input else None,
                    submitted_by=name_input if name_input else None
                )
                manager.close()

                if result["success"]:
                    st.success(result["message"])
                else:
                    st.warning(result["message"])
            except Exception as e:
                st.error(f"Lỗi khi gửi từ khóa: {e}")

st.sidebar.markdown("---")
st.sidebar.header("Bộ lọc")

sentiment_filter = st.sidebar.multiselect(
    "Cảm xúc",
    options=["positive", "negative", "neutral"],
    default=["positive", "negative", "neutral"]
)

risk_filter = st.sidebar.multiselect(
    "Mức độ rủi ro",
    options=["safe", "cautious", "high_risk", "dangerous"],
    default=["safe", "cautious", "high_risk", "dangerous"]
)

content_type_filter = st.sidebar.multiselect(
    "Loại nội dung",
    options=["entertainment", "drama", "dangerous", "social_issue", "commercial"],
    default=["entertainment", "drama", "dangerous", "social_issue", "commercial"]
)

limit = st.sidebar.selectbox(
    "Số lượng xu hướng hiển thị",
    options=[10, 20, 30, 50, 100],
    index=1
)

# Fetch data
try:
    stats = mongo_client.get_trends_stats()
    trends = mongo_client.get_all_trends(limit=limit)

    # Filter by sentiment, risk level, content type
    trends = [t for t in trends if t.get('sentiment') in sentiment_filter]
    trends = [t for t in trends if t.get('risk_level', 'safe') in risk_filter]
    trends = [t for t in trends if t.get('content_type', 'entertainment') in content_type_filter]

    # Sort by engagement: total_views (primary), total_likes (secondary)
    trends = sorted(
        trends,
        key=lambda t: (t.get('total_views', 0), t.get('total_likes', 0)),
        reverse=True
    )

    # Top Trends Chart (full width)
    st.subheader("Top xu hướng theo lượt xem")

    if trends:
        top_trends_df = pd.DataFrame([
            {'Chủ đề': t['topic'][:25] + '...' if len(t['topic']) > 25 else t['topic'],
             'Lượt xem': t.get('total_views', 0)}
            for t in trends[:10]
        ])

        fig_bar = px.bar(
            top_trends_df,
            x='Chủ đề',
            y='Lượt xem',
            color='Lượt xem',
            color_continuous_scale='Viridis'
        )
        fig_bar.update_layout(
            height=400,
            xaxis={'categoryorder': 'total descending'},
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu xu hướng")

    st.divider()

    # Modal dialog function
    @st.dialog("Chi tiết xu hướng", width="large")
    def show_trend_details(trend):
        """Show full trend details in a modal dialog."""
        # Badges
        sentiment = trend.get('sentiment', 'neutral')
        content_type = trend.get('content_type', 'entertainment')
        risk_level = trend.get('risk_level', 'safe')

        content_type_labels = {
            'entertainment': 'Giải trí',
            'drama': 'Drama',
            'dangerous': 'Nguy hiểm',
            'social_issue': 'Vấn đề XH',
            'commercial': 'Thương mại'
        }

        risk_labels = {
            'safe': 'An toàn',
            'cautious': 'Cẩn trọng',
            'high_risk': 'Rủi ro cao',
            'dangerous': 'Nguy hiểm'
        }

        badges_html = f"""
        <div style="margin-bottom: 1rem;">
            <span class="badge sentiment-{sentiment}">{sentiment.upper()}</span>
            <span class="badge content-{content_type}">{content_type_labels.get(content_type, content_type)}</span>
            <span class="badge risk-{risk_level}">{risk_labels.get(risk_level, risk_level)}</span>
        </div>
        """
        st.markdown(badges_html, unsafe_allow_html=True)

        # Topic
        st.markdown(f"## {trend['topic']}")

        # Basic info
        col_info, col_stats = st.columns([2, 1])

        with col_info:
            st.write(f"**Tóm tắt:** {trend.get('summary', 'N/A')}")
            st.write(f"**Từ khóa:** {', '.join(trend.get('keywords', []))}")
            st.write(f"**Thời gian:** {trend.get('timestamp', 'N/A')}")

            source_counts = trend.get('source_counts', {})
            if source_counts:
                source_str = " | ".join([f"{s.upper()}: {c}" for s, c in source_counts.items()])
                st.write(f"**Nguồn:** {source_str}")

        with col_stats:
            st.metric("Số video", trend.get('video_count') or 0)
            st.metric("Lượt xem", f"{trend.get('total_views') or 0:,}")
            st.metric("Lượt thích", f"{trend.get('total_likes') or 0:,}")

        st.divider()

        # Guidelines tabs
        guidelines = trend.get('guidelines', {})

        if guidelines:
            tab1, tab2, tab3 = st.tabs(["Cho Marketers", "Cho Quản lý XH", "Nội dung mẫu"])

            with tab1:
                marketers_guide = guidelines.get('for_marketers', {})

                if marketers_guide:
                    should_participate = marketers_guide.get('should_participate', False)

                    if should_participate:
                        st.success(f"**Nên tham gia:** {marketers_guide.get('summary', 'N/A')}")
                    else:
                        st.warning(f"**Không nên tham gia:** {marketers_guide.get('summary', 'N/A')}")

                    recommendations = marketers_guide.get('recommendations', [])
                    if recommendations:
                        st.write("**Gợi ý:**")
                        for rec in recommendations:
                            st.markdown(f"- {rec}")

                    warnings = marketers_guide.get('warnings', [])
                    if warnings:
                        st.write("**Cảnh báo:**")
                        for warn in warnings:
                            st.markdown(f"- {warn}")

                    detailed = marketers_guide.get('detailed_advice', '')
                    if detailed:
                        st.write("**Phân tích chi tiết:**")
                        st.write(detailed)
                else:
                    st.info("Chưa có guidelines cho marketers")

            with tab2:
                social_guide = guidelines.get('for_social_managers', {})

                if social_guide:
                    intervention = social_guide.get('intervention_needed', False)

                    if intervention:
                        st.error(f"**Cần can thiệp:** {social_guide.get('summary', 'N/A')}")
                    else:
                        st.success(f"**Không cần can thiệp:** {social_guide.get('summary', 'N/A')}")

                    actions = social_guide.get('actions', [])
                    if actions:
                        st.write("**Hành động cần làm:**")
                        for action in actions:
                            st.markdown(f"- {action}")

                    monitoring = social_guide.get('monitoring_points', [])
                    if monitoring:
                        st.write("**Điểm cần theo dõi:**")
                        for point in monitoring:
                            st.markdown(f"- {point}")

                    detailed = social_guide.get('detailed_analysis', '')
                    if detailed:
                        st.write("**Phân tích chi tiết:**")
                        st.write(detailed)
                else:
                    st.info("Chưa có guidelines cho quản lý xã hội")

            with tab3:
                if trend.get('sample_videos'):
                    st.write("**Nội dung mẫu:**")
                    for i, video in enumerate(trend['sample_videos'][:3], 1):
                        text = video.get('text') or 'N/A'
                        source = video.get('source', 'N/A').upper()
                        st.markdown(f"""
                        **{i}. [{source}]**
                        - Nội dung: {text[:150]}...
                        - Tác giả: {video.get('author_name') or 'N/A'}
                        - Likes: {video.get('likes') or 0:,} | Views: {video.get('views') or 0:,}
                        """)
                else:
                    st.info("Không có nội dung mẫu")
        else:
            if trend.get('sample_videos'):
                st.write("**Nội dung mẫu:**")
                for i, video in enumerate(trend['sample_videos'][:3], 1):
                    text = video.get('text') or 'N/A'
                    source = video.get('source', 'N/A').upper()
                    st.markdown(f"""
                    **{i}. [{source}]**
                    - Nội dung: {text[:150]}...
                    - Tác giả: {video.get('author_name') or 'N/A'}
                    - Likes: {video.get('likes') or 0:,} | Views: {video.get('views') or 0:,}
                    """)

    # Trends Table (compact cards)
    st.subheader(f"Xu hướng mới nhất (Tổng: {len(trends)})")

    if trends:
        for idx, trend in enumerate(trends):
            sentiment = trend.get('sentiment', 'neutral')
            content_type = trend.get('content_type', 'entertainment')
            risk_level = trend.get('risk_level', 'safe')

            content_type_labels = {
                'entertainment': 'Giải trí',
                'drama': 'Drama',
                'dangerous': 'Nguy hiểm',
                'social_issue': 'Vấn đề XH',
                'commercial': 'Thương mại'
            }

            risk_labels = {
                'safe': 'An toàn',
                'cautious': 'Cẩn trọng',
                'high_risk': 'Rủi ro cao',
                'dangerous': 'Nguy hiểm'
            }

            # Create columns: [card, button]
            col_card, col_button = st.columns([6, 1])

            with col_card:
                st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-radius: 0.75rem; padding: 1rem 1.25rem; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                    <div style="display: flex; align-items: center; gap: 2rem;">
                        <div style="flex-shrink: 0; width: 4.5rem; text-align: center;">
                            <div style="font-size: 2rem; font-weight: bold; color: #64748b;">#{idx + 1}</div>
                        </div>
                        <div style="flex: 2; min-width: 0;">
                            <div style="margin-bottom: 0.5rem;">
                                <span class="badge sentiment-{sentiment}">{sentiment.upper()}</span>
                                <span class="badge content-{content_type}">{content_type_labels.get(content_type, content_type)}</span>
                                <span class="badge risk-{risk_level}">{risk_labels.get(risk_level, risk_level)}</span>
                            </div>
                            <h3 style="margin: 0; font-size: 1.4rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{trend['topic']}</h3>
                        </div>
                        <div style="flex: 2; display: flex; gap: 2rem; align-items: center; justify-content: space-between;">
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">{trend.get('video_count', 0)}</div>
                                <div style="font-size: 0.8rem; color: #94a3b8;">videos</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">{trend.get('total_views', 0):,}</div>
                                <div style="font-size: 0.8rem; color: #94a3b8;">lượt xem</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">{trend.get('total_likes', 0):,}</div>
                                <div style="font-size: 0.8rem; color: #94a3b8;">lượt thích</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_button:
                st.markdown('<div style="display: flex; align-items: center; height: 100%;"></div>', unsafe_allow_html=True)
                if st.button("Xem chi tiết", key=f"card_{idx}"):
                    show_trend_details(trend)

            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("Không tìm thấy xu hướng. Đảm bảo Consumer đã xử lý dữ liệu.")

except Exception as e:
    st.error(f"Lỗi khi tải dữ liệu: {e}")
    st.info("Đảm bảo MongoDB đang chạy và có dữ liệu từ Consumer.")

# Footer
st.divider()

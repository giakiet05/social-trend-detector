"""
TikTok Tech Trends Dashboard
Real-time visualization of trending tech topics on TikTok
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from utils.mongo_client import DashboardMongoClient

# Page config
st.set_page_config(
    page_title="Social Trends Dashboard",
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
st.markdown('<h1 class="main-header">Social Trends Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time insights into social trends</p>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.header("Filters")

refresh_button = st.sidebar.button("Refresh Data", use_container_width=True)

sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=["positive", "negative", "neutral"],
    default=["positive", "negative", "neutral"]
)

risk_filter = st.sidebar.multiselect(
    "Risk Level",
    options=["safe", "cautious", "high_risk", "dangerous"],
    default=["safe", "cautious", "high_risk", "dangerous"]
)

content_type_filter = st.sidebar.multiselect(
    "Content Type",
    options=["entertainment", "drama", "dangerous", "social_issue", "commercial"],
    default=["entertainment", "drama", "dangerous", "social_issue", "commercial"]
)

limit = st.sidebar.selectbox(
    "Number of trends to display",
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

    # Top Trends Chart (full width)
    st.subheader("Top Trends by Views")

    if trends:
        top_trends_df = pd.DataFrame([
            {'Topic': t['topic'][:25] + '...' if len(t['topic']) > 25 else t['topic'],
             'Views': t.get('total_views', 0)}
            for t in trends[:10]
        ])

        fig_bar = px.bar(
            top_trends_df,
            x='Topic',
            y='Views',
            color='Views',
            color_continuous_scale='Viridis'
        )
        fig_bar.update_layout(
            height=400,
            xaxis={'categoryorder': 'total descending'},
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No trends data available")

    st.divider()

    # Modal dialog function
    @st.dialog("Trend Details", width="large")
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
            st.write(f"**Summary:** {trend.get('summary', 'N/A')}")
            st.write(f"**Keywords:** {', '.join(trend.get('keywords', []))}")
            st.write(f"**Timestamp:** {trend.get('timestamp', 'N/A')}")

            source_counts = trend.get('source_counts', {})
            if source_counts:
                source_str = " | ".join([f"{s.upper()}: {c}" for s, c in source_counts.items()])
                st.write(f"**Nguồn:** {source_str}")

        with col_stats:
            st.metric("Videos", trend.get('video_count') or 0)
            st.metric("Views", f"{trend.get('total_views') or 0:,}")
            st.metric("Likes", f"{trend.get('total_likes') or 0:,}")

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
    st.subheader(f"Latest Trends ({len(trends)} total)")

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
                                <div style="font-size: 0.8rem; color: #94a3b8;">views</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: bold; color: #1e293b;">{trend.get('total_likes', 0):,}</div>
                                <div style="font-size: 0.8rem; color: #94a3b8;">likes</div>
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
        st.info("No trends found. Make sure the Consumer has processed some data.")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure MongoDB is running and has data from the Consumer.")

# Footer
st.divider()

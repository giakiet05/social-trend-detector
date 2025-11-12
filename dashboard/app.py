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
    page_title="TikTok Tech Trends Dashboard",
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
</style>
""", unsafe_allow_html=True)

# Initialize MongoDB client
@st.cache_resource
def get_mongo_client():
    client = DashboardMongoClient()
    return client.connect()

mongo_client = get_mongo_client()

# Header
st.markdown('<h1 class="main-header">📊 TikTok Tech Trends Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time insights into trending tech topics on TikTok</p>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.header("Filters")

refresh_button = st.sidebar.button("🔄 Refresh Data", use_container_width=True)

sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=["positive", "negative", "neutral"],
    default=["positive", "negative", "neutral"]
)

limit = st.sidebar.slider("Number of trends to display", 5, 100, 20)

# Fetch data
try:
    stats = mongo_client.get_trends_stats()
    trends = mongo_client.get_all_trends(limit=limit)

    # Filter by sentiment
    trends = [t for t in trends if t.get('sentiment') in sentiment_filter]

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📈 Total Trends",
            value=stats['total_trends'],
            delta=None
        )

    with col2:
        st.metric(
            label="🎬 Total Videos",
            value=f"{stats['total_videos']:,}",
            delta=None
        )

    with col3:
        st.metric(
            label="👁️ Total Views",
            value=f"{stats['total_views']:,}",
            delta=None
        )

    with col4:
        st.metric(
            label="❤️ Total Likes",
            value=f"{stats['total_likes']:,}",
            delta=None
        )

    st.divider()

    # Charts Row
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("😊 Sentiment Distribution")

        if stats['sentiments']:
            sentiment_df = pd.DataFrame([
                {'Sentiment': k.capitalize(), 'Count': v}
                for k, v in stats['sentiments'].items()
            ])

            fig_pie = px.pie(
                sentiment_df,
                values='Count',
                names='Sentiment',
                color='Sentiment',
                color_discrete_map={
                    'Positive': '#10b981',
                    'Negative': '#ef4444',
                    'Neutral': '#6b7280'
                },
                hole=0.4
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No sentiment data available")

    with col_chart2:
        st.subheader("🔥 Top Trends by Views")

        if trends:
            top_trends_df = pd.DataFrame([
                {'Topic': t['topic'][:30] + '...' if len(t['topic']) > 30 else t['topic'],
                 'Views': t.get('total_views', 0)}
                for t in trends[:10]
            ])

            fig_bar = px.bar(
                top_trends_df,
                x='Views',
                y='Topic',
                orientation='h',
                color='Views',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(
                height=300,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No trends data available")

    st.divider()

    # Trends Table
    st.subheader(f"📋 Latest Trends ({len(trends)} total)")

    if trends:
        for trend in trends:
            with st.expander(f"**{trend['topic']}** ({trend.get('sentiment', 'neutral').capitalize()})"):
                col_info, col_stats = st.columns([2, 1])

                with col_info:
                    st.write(f"**Summary:** {trend.get('summary', 'N/A')}")
                    st.write(f"**Keywords:** {', '.join(trend.get('keywords', []))}")
                    st.write(f"**Timestamp:** {trend.get('timestamp', 'N/A')}")

                with col_stats:
                    st.metric("Videos", trend.get('video_count') or 0)
                    st.metric("Views", f"{trend.get('total_views') or 0:,}")
                    st.metric("Likes", f"{trend.get('total_likes') or 0:,}")

                # Sample videos
                if trend.get('sample_videos'):
                    st.write("**Sample Videos:**")
                    for i, video in enumerate(trend['sample_videos'][:3], 1):
                        text = video.get('text') or 'N/A'
                        st.markdown(f"""
                        **Video {i}:**
                        - Text: {text[:100]}...
                        - Author: {video.get('author') or 'N/A'}
                        - Likes: {video.get('likes') or 0:,} | Views: {video.get('views') or 0:,}
                        """)
    else:
        st.info("No trends found. Make sure the Consumer has processed some data.")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure MongoDB is running and has data from the Consumer.")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>TikTok Tech Trend Detector | Powered by Spark Streaming + OpenAI + MongoDB</p>
</div>
""", unsafe_allow_html=True)
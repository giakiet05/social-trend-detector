"""
Admin Dashboard for Social Trends Detection System
Manage trends, user submissions, and active keywords
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from utils.mongo_client import DashboardMongoClient
from common.keyword_manager import MongoKeywordManager

st.set_page_config(
    page_title="Admin Dashboard - Social Trends",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #DC2626;
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
    .status-pending { background-color: #fef3c7; color: #92400e; }
    .status-approved { background-color: #d1fae5; color: #065f46; }
    .status-rejected { background-color: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_mongo_client():
    client = DashboardMongoClient()
    return client.connect()

@st.cache_resource
def get_keyword_manager():
    return MongoKeywordManager()

mongo_client = get_mongo_client()
keyword_manager = get_keyword_manager()

st.markdown('<h1 class="main-header">Admin Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Manage trends, submissions, and keywords</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Trends Management", "User Submissions", "Active Keywords"])

# ==================== TAB 1: TRENDS MANAGEMENT ====================
with tab1:
    st.header("Trends Management")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search by topic or keyword", placeholder="Enter keyword...")
    with col2:
        refresh_trends = st.button("Refresh Trends", use_container_width=True)

    trends = mongo_client.get_all_trends(limit=200)

    if not trends:
        st.info("No trends found in database")
    else:
        st.write(f"**Total trends:** {len(trends)}")

        if search_query:
            trends = [
                t for t in trends
                if search_query.lower() in t.get('topic', '').lower()
                or any(search_query.lower() in k.lower() for k in t.get('keywords', []))
            ]
            st.write(f"**Filtered:** {len(trends)} trends")

        for idx, trend in enumerate(trends):
            with st.expander(f"**{trend.get('topic', 'Unknown')}** - {trend.get('timestamp', '')}"):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Summary:** {trend.get('summary', 'N/A')}")
                    st.write(f"**Keywords:** {', '.join(trend.get('keywords', []))}")
                    st.write(f"**Sentiment:** {trend.get('sentiment', 'N/A')}")

                with col2:
                    st.write(f"**Videos:** {trend.get('video_count', 0)}")
                    st.write(f"**Views:** {trend.get('total_views', 0):,}")
                    st.write(f"**Likes:** {trend.get('total_likes', 0):,}")

                    source_counts = trend.get('source_counts', {})
                    if source_counts:
                        st.write(f"**Sources:** {source_counts}")

                with col3:
                    st.write(f"**Content Type:** {trend.get('content_type', 'N/A')}")
                    st.write(f"**Risk Level:** {trend.get('risk_level', 'N/A')}")

                    if st.button(f"Delete", key=f"delete_trend_{idx}", type="primary", use_container_width=True):
                        if mongo_client.delete_trend(trend['_id']):
                            st.success(f"Deleted trend: {trend.get('topic')}")
                            st.rerun()
                        else:
                            st.error("Failed to delete trend")

# ==================== TAB 2: USER SUBMISSIONS ====================
with tab2:
    st.header("User Submissions Review")

    col1, col2 = st.columns([3, 1])
    with col1:
        filter_status = st.selectbox(
            "Filter by status",
            ["pending", "approved", "rejected", "all"],
            index=0
        )
    with col2:
        refresh_submissions = st.button("Refresh Submissions", use_container_width=True)

    if filter_status == "all":
        submissions = list(keyword_manager.user_submissions.find().sort("created_at", -1).limit(100))
    else:
        submissions = keyword_manager.get_pending_submissions(limit=100) if filter_status == "pending" else \
                     list(keyword_manager.user_submissions.find({"status": filter_status}).sort("created_at", -1).limit(100))

    if not submissions:
        st.info(f"No {filter_status} submissions found")
    else:
        st.write(f"**Total {filter_status} submissions:** {len(submissions)}")

        for idx, sub in enumerate(submissions):
            status = sub.get('status', 'pending')
            status_class = f"status-{status}"

            with st.expander(f"**{sub.get('keyword', 'Unknown')}** - {status.upper()}"):
                st.markdown(f"<span class='badge {status_class}'>{status.upper()}</span>", unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Keyword:** {sub.get('keyword', 'N/A')}")
                    st.write(f"**Reason:** {sub.get('reason', 'N/A')}")
                    st.write(f"**Submitted by:** {sub.get('submitted_by', 'Anonymous')}")
                    st.write(f"**Created at:** {sub.get('created_at', 'N/A')}")

                    if sub.get('reviewed_at'):
                        st.write(f"**Reviewed at:** {sub.get('reviewed_at', 'N/A')}")
                        st.write(f"**Reviewed by:** {sub.get('reviewed_by', 'N/A')}")
                        if sub.get('notes'):
                            st.write(f"**Notes:** {sub.get('notes', '')}")

                with col2:
                    if status == "pending":
                        st.write("**Actions:**")

                        col_approve, col_reject = st.columns(2)

                        with col_approve:
                            if st.button("Approve", key=f"approve_{idx}", use_container_width=True):
                                result = keyword_manager.approve_submission(
                                    submission_id=str(sub['_id']),
                                    sources=["tiktok", "news", "youtube"],
                                    reviewed_by="admin"
                                )
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])

                        with col_reject:
                            if st.button("Reject", key=f"reject_{idx}", type="secondary", use_container_width=True):
                                result = keyword_manager.reject_submission(
                                    submission_id=str(sub['_id']),
                                    reason="Rejected by admin",
                                    reviewed_by="admin"
                                )
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])

# ==================== TAB 3: ACTIVE KEYWORDS ====================
with tab3:
    st.header("Active Keywords Management")

    active_keywords = keyword_manager.get_active_keywords()

    col_list, col_add = st.columns([2, 1])

    with col_list:
        st.subheader("Current Keywords")

        if not active_keywords:
            st.info("No active keywords found")
        else:
            st.write(f"**Total:** {len(active_keywords)} keywords")
            st.caption("All keywords apply to: TikTok, News, YouTube")

            st.markdown("---")

            for idx, kw in enumerate(sorted(active_keywords, key=lambda x: x['keyword'])):
                col_text, col_btn = st.columns([4, 1])
                with col_text:
                    st.write(f"{idx + 1}. **{kw['keyword']}**")
                with col_btn:
                    if st.button("Delete", key=f"del_{kw['_id']}", type="secondary", use_container_width=True):
                        result = keyword_manager.remove_keyword(kw['keyword'], removed_by="admin")
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()
                        else:
                            st.error(result['message'])

    with col_add:
        st.subheader("Add New Keyword")

        with st.form("add_keyword_form"):
            new_keyword = st.text_input(
                "Keyword",
                placeholder="e.g., Avatar 3",
                label_visibility="collapsed"
            )
            st.caption("Will apply to all sources")

            submit_keyword = st.form_submit_button("Add Keyword", use_container_width=True, type="primary")

            if submit_keyword:
                if not new_keyword:
                    st.error("Please enter a keyword")
                else:
                    result = keyword_manager.add_keyword(
                        keyword=new_keyword,
                        sources=["tiktok", "news", "youtube"],
                        added_by="admin"
                    )
                    if result['success']:
                        st.success(result['message'])
                        st.rerun()
                    else:
                        st.error(result['message'])

st.markdown("---")
st.caption("Admin Dashboard - Social Trends Detection System")

"""
Socitrend - Bảng điều khiển quản trị
Quản lý xu hướng, đề xuất từ người dùng và từ khóa
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
    page_title="Socitrend - Quản trị",
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

st.markdown('<h1 class="main-header">Socitrend - Quản trị</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Quản lý xu hướng, đề xuất và từ khóa</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Quản lý xu hướng", "Đề xuất từ khóa", "Từ khóa hoạt động"])

# ==================== TAB 1: TRENDS MANAGEMENT ====================
with tab1:
    st.header("Quản lý xu hướng")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Tìm kiếm theo chủ đề hoặc từ khóa", placeholder="Nhập từ khóa...")
    with col2:
        refresh_trends = st.button("Làm mới", key="refresh_trends", use_container_width=True)

    trends = mongo_client.get_all_trends(limit=200)

    if not trends:
        st.info("Không tìm thấy xu hướng trong database")
    else:
        st.write(f"**Tổng số xu hướng:** {len(trends)}")

        if search_query:
            trends = [
                t for t in trends
                if search_query.lower() in t.get('topic', '').lower()
                or any(search_query.lower() in k.lower() for k in t.get('keywords', []))
            ]
            st.write(f"**Đã lọc:** {len(trends)} xu hướng")

        # Sort by engagement: total_views (primary), total_likes (secondary)
        trends = sorted(
            trends,
            key=lambda t: (t.get('total_views', 0), t.get('total_likes', 0)),
            reverse=True
        )

        for idx, trend in enumerate(trends, 1):
            with st.expander(f"#{idx} - **{trend.get('topic', 'Không rõ')}** ({trend.get('total_views', 0):,} views)"):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Tóm tắt:** {trend.get('summary', 'N/A')}")
                    st.write(f"**Từ khóa:** {', '.join(trend.get('keywords', []))}")
                    st.write(f"**Cảm xúc:** {trend.get('sentiment', 'N/A')}")

                with col2:
                    st.write(f"**Số video:** {trend.get('video_count', 0)}")
                    st.write(f"**Lượt xem:** {trend.get('total_views', 0):,}")
                    st.write(f"**Lượt thích:** {trend.get('total_likes', 0):,}")

                    source_counts = trend.get('source_counts', {})
                    if source_counts:
                        st.write(f"**Nguồn:** {source_counts}")

                with col3:
                    st.write(f"**Loại nội dung:** {trend.get('content_type', 'N/A')}")
                    st.write(f"**Mức độ rủi ro:** {trend.get('risk_level', 'N/A')}")

                    if st.button(f"Xóa", key=f"delete_trend_{idx}", type="primary", use_container_width=True):
                        if mongo_client.delete_trend(trend['_id']):
                            st.success(f"Đã xóa xu hướng: {trend.get('topic')}")
                            st.rerun()
                        else:
                            st.error("Xóa xu hướng thất bại")

# ==================== TAB 2: KEYWORD SUGGESTIONS ====================
with tab2:
    st.header("Đề xuất từ khóa")

    col_user, col_extracted = st.columns([1, 1])

    # ========== CỘT TRÁI: USER SUBMISSIONS ==========
    with col_user:
        st.subheader("Từ người dùng")

        col_filter, col_refresh = st.columns([3, 1])
        with col_filter:
            filter_status_user = st.selectbox(
                "Lọc theo trạng thái",
                ["pending", "approved", "rejected", "all"],
                index=0,
                key="filter_user"
            )
        with col_refresh:
            refresh_user = st.button("Làm mới", key="refresh_user", use_container_width=True)

        if filter_status_user == "all":
            submissions = list(keyword_manager.user_submissions.find().sort("created_at", -1).limit(50))
        else:
            submissions = keyword_manager.get_pending_submissions(limit=50) if filter_status_user == "pending" else \
                         list(keyword_manager.user_submissions.find({"status": filter_status_user}).sort("created_at", -1).limit(50))

        if not submissions:
            st.info(f"Không có đề xuất {filter_status_user}")
        else:
            st.write(f"**Tổng:** {len(submissions)}")

            for idx, sub in enumerate(submissions):
                status = sub.get('status', 'pending')
                status_class = f"status-{status}"

                with st.expander(f"**{sub.get('keyword', 'Không rõ')}**", expanded=False):
                    st.markdown(f"<span class='badge {status_class}'>{status.upper()}</span>", unsafe_allow_html=True)

                    st.write(f"**Lý do:** {sub.get('reason', 'N/A')}")
                    st.write(f"**Người gửi:** {sub.get('submitted_by', 'Ẩn danh')}")

                    if status == "pending":
                        col_approve, col_reject = st.columns(2)

                        with col_approve:
                            if st.button("Duyệt", key=f"approve_user_{idx}", use_container_width=True):
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
                            if st.button("Từ chối", key=f"reject_user_{idx}", type="secondary", use_container_width=True):
                                result = keyword_manager.reject_submission(
                                    submission_id=str(sub['_id']),
                                    reason="Từ chối bởi admin",
                                    reviewed_by="admin"
                                )
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])

    # ========== CỘT PHẢI: EXTRACTED KEYWORDS ==========
    with col_extracted:
        st.subheader("Từ Keyword Extractor")

        col_filter, col_refresh = st.columns([3, 1])
        with col_filter:
            filter_status_extracted = st.selectbox(
                "Lọc theo trạng thái",
                ["pending", "approved", "rejected", "all"],
                index=0,
                key="filter_extracted"
            )
        with col_refresh:
            refresh_extracted = st.button("Làm mới", key="refresh_extracted", use_container_width=True)

        extracted_keywords = mongo_client.get_extracted_keywords(
            status=filter_status_extracted,
            limit=50
        )

        if not extracted_keywords:
            st.info(f"Không có từ khóa {filter_status_extracted}")
        else:
            st.write(f"**Tổng:** {len(extracted_keywords)}")

            for idx, kw in enumerate(extracted_keywords):
                status = kw.get('status', 'pending')
                status_class = f"status-{status}"
                category = kw.get('category', 'N/A')

                with st.expander(f"**{kw.get('keyword', 'Không rõ')}** ({category})", expanded=False):
                    st.markdown(f"<span class='badge {status_class}'>{status.upper()}</span>", unsafe_allow_html=True)

                    st.write(f"**Danh mục:** {category}")
                    st.write(f"**Lý do trending:** {kw.get('reason', 'N/A')}")
                    st.write(f"**Nguồn:** {kw.get('source', 'news')}")

                    if status == "pending":
                        col_approve, col_reject = st.columns(2)

                        with col_approve:
                            if st.button("Thêm vào keywords", key=f"approve_extracted_{idx}", use_container_width=True):
                                approve_result = mongo_client.approve_extracted_keyword(
                                    keyword_id=str(kw['_id']),
                                    keyword_text=kw.get('keyword', ''),
                                    approved_by="admin"
                                )

                                if approve_result['success']:
                                    add_result = keyword_manager.add_keyword(
                                        keyword=kw.get('keyword', ''),
                                        sources=["tiktok", "news", "youtube"],
                                        added_by="admin (extractor)"
                                    )

                                    if add_result['success']:
                                        st.success(f"Đã thêm '{kw.get('keyword')}' vào keywords hoạt động")
                                        st.rerun()
                                    else:
                                        st.warning(add_result['message'])
                                else:
                                    st.error(approve_result['message'])

                        with col_reject:
                            if st.button("Bỏ qua", key=f"reject_extracted_{idx}", type="secondary", use_container_width=True):
                                result = mongo_client.reject_extracted_keyword(
                                    keyword_id=str(kw['_id']),
                                    rejected_by="admin",
                                    reason="Không phù hợp"
                                )
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])

# ==================== TAB 3: ACTIVE KEYWORDS ====================
with tab3:
    st.header("Quản lý từ khóa")

    active_keywords = keyword_manager.get_active_keywords()

    col_list, col_add = st.columns([2, 1])

    with col_list:
        st.subheader("Từ khóa hiện tại")

        if not active_keywords:
            st.info("Chưa có từ khóa nào")
        else:
            st.write(f"**Tổng:** {len(active_keywords)} từ khóa")
            st.caption("Tất cả từ khóa áp dụng cho: TikTok, News, YouTube")

            st.markdown("---")

            # Initialize editing state
            if 'editing_keyword' not in st.session_state:
                st.session_state.editing_keyword = None

            for idx, kw in enumerate(sorted(active_keywords, key=lambda x: x['keyword'])):
                keyword_id = str(kw['_id'])
                is_editing = st.session_state.editing_keyword == keyword_id

                if is_editing:
                    col_text, col_save, col_cancel = st.columns([4, 1, 1])

                    with col_text:
                        new_keyword = st.text_input(
                            f"Edit {idx + 1}",
                            value=kw['keyword'],
                            key=f"edit_input_{keyword_id}",
                            label_visibility="collapsed"
                        )

                    with col_save:
                        if st.button("Lưu", key=f"save_{keyword_id}", use_container_width=True):
                            if new_keyword and new_keyword != kw['keyword']:
                                result = keyword_manager.update_keyword(
                                    old_keyword=kw['keyword'],
                                    new_keyword=new_keyword,
                                    updated_by="admin"
                                )
                                if result['success']:
                                    st.success(result['message'])
                                    st.session_state.editing_keyword = None
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                            else:
                                st.session_state.editing_keyword = None
                                st.rerun()

                    with col_cancel:
                        if st.button("Hủy", key=f"cancel_{keyword_id}", type="secondary", use_container_width=True):
                            st.session_state.editing_keyword = None
                            st.rerun()

                else:
                    col_text, col_edit, col_del = st.columns([4, 1, 1])

                    with col_text:
                        st.write(f"{idx + 1}. **{kw['keyword']}**")

                    with col_edit:
                        if st.button("Sửa", key=f"edit_{keyword_id}", use_container_width=True):
                            st.session_state.editing_keyword = keyword_id
                            st.rerun()

                    with col_del:
                        if st.button("Xóa", key=f"del_{keyword_id}", type="secondary", use_container_width=True):
                            result = keyword_manager.remove_keyword(kw['keyword'], removed_by="admin")
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['message'])

    with col_add:
        st.subheader("Thêm từ khóa mới")

        with st.form("add_keyword_form", clear_on_submit=True):
            new_keyword = st.text_input(
                "Từ khóa",
                placeholder="VD: Avatar 3",
                label_visibility="collapsed"
            )
            st.caption("Sẽ áp dụng cho tất cả nguồn")

            submit_keyword = st.form_submit_button("Thêm từ khóa", use_container_width=True, type="primary")

            if submit_keyword:
                if not new_keyword:
                    st.error("Vui lòng nhập từ khóa")
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
st.caption("Socitrend - Bảng điều khiển quản trị")

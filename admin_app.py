import streamlit as st
import os
import time
import pandas as pd
import plotly.express as px
from analytics_db import get_analytics, get_recent_queries
from ingest import ingest_file
from Chroma_db import delete_documents_by_source

st.set_page_config(page_title="Admin Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
/* Base theme */
.stApp {
    background-color: #f8fafc;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Custom Header */
.dashboard-header {
    margin-bottom: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 1rem;
}
.header-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0;
}
.admin-profile {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: white;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    font-weight: 500;
    color: #334155;
}

/* KPI Cards */
.kpi-container {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}
.kpi-card {
    background: white;
    border-radius: 0.75rem;
    padding: 1.5rem;
    flex: 1;
    min-width: 200px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
}
.kpi-title {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
}
.kpi-trend {
    font-size: 0.75rem;
    color: #10b981;
    font-weight: 500;
}

/* Section titles */
.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

/* Upload zone */
[data-testid="stFileUploader"] {
    background-color: white;
    border: 2px dashed #cbd5e1;
    border-radius: 0.75rem;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
[data-testid="stFileUploader"]:hover {
    border-color: #3b82f6;
}
[data-testid="stForm"] {
    border: none;
    padding: 0;
}

/* Custom Table Header */
.table-header-row {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    background-color: #f1f5f9;
    border-radius: 0.5rem;
    color: #475569;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 1rem;
    border: 1px solid #e2e8f0;
}
.table-col {
    flex: 1;
}
.table-col-action {
    flex: 0 0 100px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_files_by_ext(extensions):
    if not os.path.exists(UPLOAD_DIR):
        return []
    return [f for f in os.listdir(UPLOAD_DIR) if f.endswith(extensions)]

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2rem; margin-top: 1rem;">
    <div style="width: 40px; height: 40px; background: #2563eb; border-radius: 8px; display: flex; justify-content: center; align-items: center; color: white; font-weight: bold; font-size: 20px;">🛡️</div>
    <span style="font-size: 1.25rem; font-weight: 600; color: #1e293b;">Admin Dash</span>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", ["Analytics", "RAG Documents", "SQL Databases", "Latency"], label_visibility="collapsed")

# Top Header
st.markdown(f"""
<div class="dashboard-header">
    <h1 class="header-title">{page} Overview</h1>
    <div class="admin-profile">
        <span>👨‍💼</span> Admin User
    </div>
</div>
""", unsafe_allow_html=True)

# --- PAGE 1: ANALYTICS ---
if page == "Analytics":
    stats = get_analytics()
    
    total_q = stats["total_queries"]
    text_q = stats["text_queries"]
    voice_q = stats["voice_queries"]
    unanswered_q = stats["unanswered_queries"]
    
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">📊 Total Queries</div>
            <div class="kpi-value">{total_q}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">📝 Text Queries</div>
            <div class="kpi-value">{text_q}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">🎙️ Voice Queries</div>
            <div class="kpi-value">{voice_q}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">⚠️ Unanswered Queries</div>
            <div class="kpi-value">{unanswered_q}</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Data Visualizations</div>', unsafe_allow_html=True)
    
    if total_q > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Query Input Types</div>
            """, unsafe_allow_html=True)
            
            df_input = pd.DataFrame({
                "Type": ["Text", "Voice"],
                "Count": [text_q, voice_q]
            })
            fig1 = px.bar(df_input, x="Type", y="Count", color="Type",
                          color_discrete_map={"Text": "#2563eb", "Voice": "#94a3b8"},
                          text_auto=True)
            fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(l=0, r=0, t=10, b=0),
                               showlegend=False, xaxis_title=None, yaxis_title=None, height=300)
            fig1.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Response Status</div>
            """, unsafe_allow_html=True)
            
            answered_q = total_q - unanswered_q
            df_status = pd.DataFrame({
                "Status": ["Answered", "Unanswered"],
                "Count": [answered_q, unanswered_q]
            })
            fig2 = px.pie(df_status, values='Count', names='Status', hole=0.6,
                          color='Status',
                          color_discrete_map={"Answered": "#10b981", "Unanswered": "#ef4444"})
            fig2.update_traces(textinfo='percent+label', textposition='inside')
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(l=0, r=0, t=10, b=0),
                               showlegend=False, height=300)
            fig2.add_annotation(text=f"<b style='font-size:24px; color:#1e293b;'>{total_q}</b><br><span style='color:#64748b; font-size:14px;'>Total</span>", x=0.5, y=0.5, showarrow=False)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No queries have been logged yet. Check back once users start interacting with the agent!")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↻ Refresh Analytics", use_container_width=True):
        st.rerun()

# --- PAGE 2: RAG DOCUMENTS ---
elif page == "RAG Documents":
    st.markdown('<div class="section-title">Upload Documents</div>', unsafe_allow_html=True)
    
    with st.form("rag_upload_form", clear_on_submit=True):
        uploaded_rags = st.file_uploader("Drag and drop PDF or TXT here", type=["pdf", "txt"], accept_multiple_files=True, label_visibility="collapsed")
        submit_rag = st.form_submit_button("Upload and Process")
        
    if submit_rag and uploaded_rags:
        for uploaded_rag in uploaded_rags:
            file_path = os.path.join(UPLOAD_DIR, uploaded_rag.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_rag.getbuffer())
            
            with st.spinner(f"Processing and embedding {uploaded_rag.name}..."):
                try:
                    ingest_file(file_path)
                    st.success(f"Successfully processed {uploaded_rag.name}")
                except Exception as e:
                    st.error(f"Error processing {uploaded_rag.name}: {e}")
        time.sleep(1)
        st.rerun()

    st.markdown('<div class="section-title">Uploaded Documents</div>', unsafe_allow_html=True)
    docs = get_files_by_ext((".pdf", ".txt"))
    
    if not docs:
        st.markdown("""
        <div style="text-align: center; padding: 4rem; background: white; border-radius: 0.75rem; border: 1px solid #e2e8f0; color: #94a3b8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
            <p style="font-size: 1.125rem;">No documents uploaded yet.<br>Drag & drop a PDF or TXT file above to get started.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="table-header-row">
            <div class="table-col" style="flex: 2;">File Name</div>
            <div class="table-col">File Type</div>
            <div class="table-col">Upload Date</div>
            <div class="table-col-action">Actions</div>
        </div>
        """, unsafe_allow_html=True)
        
        for doc in docs:
            ext = doc.split('.')[-1].upper()
            stat = os.stat(os.path.join(UPLOAD_DIR, doc))
            upload_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_ctime))
            
            cols = st.columns([2, 1, 1, 1])
            cols[0].markdown(f"<div style='padding-top:0.5rem; font-weight:500; color:#1e293b;'>{doc}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div style='padding-top:0.5rem;'><span style='background:#f1f5f9; color:#475569; padding:0.25rem 0.75rem; border-radius:9999px; font-size:0.75rem; font-weight:600;'>{ext}</span></div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div style='padding-top:0.5rem; color:#64748b; font-size:0.875rem;'>{upload_date}</div>", unsafe_allow_html=True)
            
            with cols[3]:
                if st.button("🗑️ Delete", key=f"del_doc_{doc}", use_container_width=True):
                    delete_documents_by_source(doc)
                    os.remove(os.path.join(UPLOAD_DIR, doc))
                    st.success(f"Deleted {doc}")
                    time.sleep(1)
                    st.rerun()
            st.markdown("<hr style='margin: 0.5rem 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

# --- PAGE 3: SQL DATABASES ---
elif page == "SQL Databases":
    st.markdown('<div class="section-title">Upload Database</div>', unsafe_allow_html=True)
    
    with st.form("sql_upload_form", clear_on_submit=True):
        uploaded_sqls = st.file_uploader("Drag and drop .db or .sqlite here", type=["db", "sqlite"], accept_multiple_files=True, label_visibility="collapsed")
        submit_sql = st.form_submit_button("Upload Database(s)")
        
    if submit_sql and uploaded_sqls:
        for uploaded_sql in uploaded_sqls:
            file_path = os.path.join(UPLOAD_DIR, uploaded_sql.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_sql.getbuffer())
            st.success(f"Successfully uploaded {uploaded_sql.name}. Schema will be dynamically extracted on next query.")
        time.sleep(1)
        st.rerun()

    st.markdown('<div class="section-title">Uploaded Databases</div>', unsafe_allow_html=True)
    dbs = get_files_by_ext((".db", ".sqlite"))
    
    if not dbs:
        st.markdown("""
        <div style="text-align: center; padding: 4rem; background: white; border-radius: 0.75rem; border: 1px solid #e2e8f0; color: #94a3b8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🗄️</div>
            <p style="font-size: 1.125rem;">No databases uploaded yet.<br>Drag & drop a SQLite DB above to get started.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="table-header-row">
            <div class="table-col" style="flex: 2;">Database Name</div>
            <div class="table-col">File Size</div>
            <div class="table-col">Upload Date</div>
            <div class="table-col-action">Actions</div>
        </div>
        """, unsafe_allow_html=True)
        
        for db in dbs:
            stat = os.stat(os.path.join(UPLOAD_DIR, db))
            size_mb = stat.st_size / (1024 * 1024)
            upload_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_ctime))
            
            cols = st.columns([2, 1, 1, 1])
            cols[0].markdown(f"<div style='padding-top:0.5rem; font-weight:500; color:#1e293b;'>{db}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div style='padding-top:0.5rem; color:#64748b; font-size:0.875rem;'>{size_mb:.2f} MB</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div style='padding-top:0.5rem; color:#64748b; font-size:0.875rem;'>{upload_date}</div>", unsafe_allow_html=True)
            with cols[3]:
                if st.button("🗑️ Delete", key=f"del_db_{db}", use_container_width=True):
                    os.remove(os.path.join(UPLOAD_DIR, db))
                    st.success(f"Deleted {db}")
                    time.sleep(1)
                    st.rerun()
            st.markdown("<hr style='margin: 0.5rem 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

# --- PAGE 4: LATENCY ---
elif page == "Latency":
    st.markdown('<div class="section-title">Recent Queries & Latency</div>', unsafe_allow_html=True)
    
    queries = get_recent_queries(30)
    
    if not queries:
        st.markdown("""
        <div style="text-align: center; padding: 4rem; background: white; border-radius: 0.75rem; border: 1px solid #e2e8f0; color: #94a3b8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⏱️</div>
            <p style="font-size: 1.125rem;">No queries logged yet.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="table-header-row">
            <div class="table-col" style="flex: 2;">Query</div>
            <div class="table-col" style="flex: 3;">Answer</div>
            <div class="table-col-action" style="flex: 1; text-align: right; min-width: 120px;">Time Taken (ms)</div>
        </div>
        """, unsafe_allow_html=True)
        
        for idx, q in enumerate(queries):
            query_text = q['query'] or ""
            answer_text = q['answer'] or ""
            latency = q['latency'] or 0.0
            q_type = q['type'] or "text"
            
            icon = "💬" if q_type == "text" else "🎙️"
            
            if len(query_text) > 60: query_text = query_text[:57] + "..."
            if len(answer_text) > 80: answer_text = answer_text[:77] + "..."
            
            bg_color = "#fef08a" # yellow
            if latency < 500:
                bg_color = "#dcfce7" # green
            elif latency > 1000:
                bg_color = "#ffedd5" # orange
                
            cols = st.columns([2, 3, 1])
            cols[0].markdown(f"<div style='padding-top:0.5rem; font-size:0.875rem; color:#1e293b; font-weight:500;'>{icon} {query_text}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div style='padding-top:0.5rem; font-size:0.875rem; color:#475569;'>{answer_text}</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div style='background-color:{bg_color}; padding:0.5rem; border-radius:0.25rem; font-size:0.875rem; color:#1e293b; text-align:right; font-weight: 500;'>{latency:.0f} ms</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 0.25rem 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

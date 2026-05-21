import os
import uuid
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Danışmanlık Otomasyonu CRM",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design
st.markdown("""
<style>
    /* Dark Theme Base & Spacing */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Header Gradient styling */
    .header-container {
        padding: 20px 0px 10px 0px;
        margin-bottom: 25px;
        border-bottom: 1px solid #334155;
    }
    
    .main-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .gold-text {
        background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 5px;
    }

    /* Cards Style */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(251, 191, 36, 0.4);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 5px;
    }
    
    .metric-value-gold {
        color: #fbbf24 !important;
    }
    
    /* Toast styles */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Load database configurations
load_dotenv()
# Fallback to Next.js project directory .env if database url not found in local env
if not os.getenv("DATABASE_URL"):
    load_dotenv("nextjs_space/.env")

# Database Connection Helper
def init_db(conn):
    try:
        with conn.cursor() as cur:
            # Create Customer table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "Customer" (
                    id VARCHAR(255) PRIMARY KEY,
                    "companyName" VARCHAR(255) NOT NULL,
                    "contactPerson" VARCHAR(255) NOT NULL,
                    phone VARCHAR(255),
                    email VARCHAR(255),
                    address TEXT,
                    sector VARCHAR(255),
                    notes TEXT,
                    "createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
                    "updatedAt" TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """)
            # Create Project table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "Project" (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'TEKLIF',
                    "startDate" TIMESTAMP,
                    "endDate" TIMESTAMP,
                    budget DOUBLE PRECISION,
                    "customerId" VARCHAR(255) NOT NULL,
                    "createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
                    "updatedAt" TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_customer FOREIGN KEY ("customerId") REFERENCES "Customer" (id) ON DELETE CASCADE
                );
            """)
    except Exception as e:
        st.warning(f"Tablolar otomatik oluşturulurken uyarı alındı: {e}")

@st.cache_resource
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL bulunamadı. Lütfen .env dosyasını veya nextjs_space/.env dosyasını kontrol edin.")
        st.stop()
    try:
        # PostgreSQL connection (psycopg2 auto-parses connection URLs)
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        init_db(conn)
        return conn
    except Exception as e:
        st.error(f"Veritabanı bağlantısı kurulamadı: {e}")
        st.info("Kütüphanelerin kurulu olduğundan emin olun: pip install psycopg2-binary")
        st.stop()

# Helper to format currency
def fmt_currency(val):
    if val is None:
        return "₺0.00"
    return f"₺{val:,.2f}".replace(",", ".")

# Project Status Mapping
STATUS_LABELS = {
    'TEKLIF': 'Teklif',
    'DEVAM': 'Devam Ediyor',
    'TAMAMLANDI': 'Tamamlandı',
    'IPTAL': 'İptal Edildi',
    'BEKLEMEDE': 'Beklemede'
}

STATUS_COLORS = {
    'TEKLIF': '#60B5FF',       # Light Blue
    'DEVAM': '#FF9149',        # Orange
    'TAMAMLANDI': '#80D8C3',   # Teal
    'IPTAL': '#FF6363',        # Red
    'BEKLEMEDE': '#A19AD3'     # Purple
}

# Database Query Runners
def run_query(query, params=None):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        try:
            return cur.fetchall()
        except psycopg2.ProgrammingError:
            return None

def run_insert_or_update(query, params):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)

# Sidebar Navigation
st.sidebar.markdown("""
<div style='text-align: center; padding-bottom: 20px;'>
    <h2 style='color: #fbbf24; font-weight: 800; margin-bottom: 0px;'>CRM PANEL</h2>
    <small style='color: #94a3b8;'>Danışmanlık Otomasyonu</small>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("Sayfalar", ["📊 Genel Bakış", "👥 Müşteriler", "💼 Projeler"])

# Main Header
def render_header(title, highlight_word, subtitle_text):
    st.markdown(f"""
    <div class="header-container">
        <h1 class="main-title">{title} <span class="gold-text">{highlight_word}</span></h1>
        <p class="subtitle">{subtitle_text}</p>
    </div>
    """, unsafe_allow_html=True)

# ----------------- PAGE 1: DASHBOARD -----------------
if page == "📊 Genel Bakış":
    render_header("Genel", "Bakış", "Danışmanlık operasyonlarınızın anlık özeti.")
    
    # Fetch Stats
    try:
        # Total customers
        c_count = run_query('SELECT COUNT(*) as count FROM "Customer"')[0]['count']
        
        # Project counts and budgets
        projects = run_query('SELECT status, budget FROM "Project"')
        p_df = pd.DataFrame(projects) if projects else pd.DataFrame(columns=['status', 'budget'])
        
        total_projects = len(p_df)
        active_projects = len(p_df[p_df['status'] == 'DEVAM']) if total_projects > 0 else 0
        completed_projects = len(p_df[p_df['status'] == 'TAMAMLANDI']) if total_projects > 0 else 0
        
        total_budget = p_df['budget'].sum() if total_projects > 0 else 0.0
        active_budget = p_df[p_df['status'] == 'DEVAM']['budget'].sum() if total_projects > 0 else 0.0
        
        # Recent Customers
        recent_cust = run_query('SELECT id, "companyName", "contactPerson", sector, "createdAt" FROM "Customer" ORDER BY "createdAt" DESC LIMIT 5')
        
        # Recent Projects
        recent_proj = run_query("""
            SELECT p.id, p.name, p.status, p."startDate", c."companyName" 
            FROM "Project" p 
            JOIN "Customer" c ON p."customerId" = c.id 
            ORDER BY p."createdAt" DESC LIMIT 5
        """)
        
        # Display Stats Metrics Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Toplam Müşteri</div>
                <div class="metric-value">{c_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Aktif Proje</div>
                <div class="metric-value">{active_projects}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Toplam Proje</div>
                <div class="metric-value">{total_projects}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Tamamlanan</div>
                <div class="metric-value">{completed_projects}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: Budget Summary and Project distribution chart
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.markdown("""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 25px; height: 100%;">
                <h3 style="margin-top:0px; font-size:1.2rem; font-weight:700;">Bütçe Özeti</h3>
                <p style="color:#94a3b8; font-size:0.8rem; margin-bottom: 25px;">Tüm projeler üzerinden hesaplanmıştır.</p>
                <div style="margin-bottom: 20px;">
                    <div style="font-size:0.8rem; color:#94a3b8;">TOPLAM BÜTÇE</div>
                    <div style="font-size:1.8rem; font-weight:700; color:#fbbf24;">""" + fmt_currency(total_budget) + """</div>
                </div>
                <div>
                    <div style="font-size:0.8rem; color:#94a3b8;">AKTİF PROJE BÜTÇESİ</div>
                    <div style="font-size:1.5rem; font-weight:600; color:#f8fafc;">""" + fmt_currency(active_budget) + """</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_right:
            st.markdown("<div style='background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0px; font-size:1.2rem; font-weight:700;'>Proje Durum Dağılımı</h3>", unsafe_allow_html=True)
            
            if total_projects > 0:
                # Group and map labels
                status_counts = p_df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                status_counts['Durum'] = status_counts['Status'].map(STATUS_LABELS)
                
                # Colors map
                colors_list = [STATUS_COLORS.get(status, '#cbd5e1') for status in status_counts['Status']]
                
                fig = px.pie(
                    status_counts, 
                    values='Count', 
                    names='Durum',
                    hole=0.4,
                    color_discrete_sequence=colors_list
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#f8fafc',
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=200,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Henüz proje bulunmuyor.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 3: Recent items
        col_c, col_p = st.columns(2)
        
        with col_c:
            st.markdown("<div style='background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; height:100%;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0px; font-size:1.1rem; font-weight:700;'>Son Eklenen Müşteriler</h3>", unsafe_allow_html=True)
            
            if recent_cust:
                for c in recent_cust:
                    st.markdown(f"""
                    <div style="padding: 10px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight:600; font-size:0.95rem;">🏢 {c['companyName']}</div>
                            <div style="font-size:0.8rem; color:#94a3b8;">Kişi: {c['contactPerson']} {f'• Sektör: {c["sector"]}' if c['sector'] else ''}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.text("Müşteri bulunamadı.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_p:
            st.markdown("<div style='background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; height:100%;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0px; font-size:1.1rem; font-weight:700;'>Son Eklenen Projeler</h3>", unsafe_allow_html=True)
            
            if recent_proj:
                for p in recent_proj:
                    status_lbl = STATUS_LABELS.get(p['status'], p['status'])
                    status_color = STATUS_COLORS.get(p['status'], '#fff')
                    
                    st.markdown(f"""
                    <div style="padding: 10px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight:600; font-size:0.95rem;">💼 {p['name']}</div>
                            <div style="font-size:0.8rem; color:#94a3b8;">Firma: {p['companyName']}</div>
                        </div>
                        <span style="background-color: {status_color}22; color: {status_color}; font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px; font-weight: 600;">
                            {status_lbl}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.text("Proje bulunamadı.")
            st.markdown("</div>", unsafe_allow_html=True)
            
    except Exception as ex:
        st.error(f"Gösterge paneli yüklenirken bir hata oluştu: {ex}")

# ----------------- PAGE 2: CUSTOMERS -----------------
elif page == "👥 Müşteriler":
    render_header("Müşteri", "Yönetimi", "Firmalarınızı ve iletişim bilgilerini yönetin.")
    
    # 1. New Customer Form (Expander)
    with st.expander("➕ Yeni Müşteri Ekle", expanded=False):
        with st.form("new_customer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("Firma Adı *")
                contact_person = st.text_input("Yetkili İsim *")
                sector = st.text_input("Sektör")
            with col2:
                phone = st.text_input("Telefon Numarası")
                email = st.text_input("E-posta Adresi")
                address = st.text_input("Firma Adresi")
                
            notes = st.text_area("Müşteri Notları")
            
            submitted = st.form_submit_button("Müşteriyi Kaydet")
            if submitted:
                if not company_name or not contact_person:
                    st.warning("Firma Adı ve Yetkili Kişi zorunludur!")
                else:
                    try:
                        c_id = f"py_{uuid.uuid4().hex[:20]}"
                        query = """
                            INSERT INTO "Customer" (id, "companyName", "contactPerson", phone, email, address, sector, notes, "createdAt", "updatedAt") 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """
                        run_insert_or_update(query, (c_id, company_name, contact_person, phone or None, email or None, address or None, sector or None, notes or None))
                        st.success("Müşteri başarıyla eklendi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ekleme başarısız: {e}")

    # Fetch and filter customers
    try:
        cust_list = run_query("""
            SELECT c.id, c."companyName", c."contactPerson", c.phone, c.email, c.address, c.sector, c.notes,
                   (SELECT COUNT(*) FROM "Project" WHERE "customerId" = c.id) as project_count
            FROM "Customer" c
            ORDER BY c."createdAt" DESC
        """)
        
        if cust_list:
            df_cust = pd.DataFrame(cust_list)
            
            # Filters
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_q = st.text_input("🔍 İsim, yetkili, e-posta veya telefon ile arayın")
            with col_s2:
                sectors_list = ["Tümü"] + list(df_cust['sector'].dropna().unique())
                sector_filter = st.selectbox("Sektör Filtresi", sectors_list)
            
            # Apply Filters
            filtered_df = df_cust.copy()
            if search_q:
                mask = (
                    filtered_df['companyName'].str.contains(search_q, case=False, na=False) |
                    filtered_df['contactPerson'].str.contains(search_q, case=False, na=False) |
                    filtered_df['email'].str.contains(search_q, case=False, na=False) |
                    filtered_df['phone'].str.contains(search_q, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
                
            if sector_filter != "Tümü":
                filtered_df = filtered_df[filtered_df['sector'] == sector_filter]
                
            # Display Customers Cards
            if not filtered_df.empty:
                for idx, row in filtered_df.iterrows():
                    st.markdown(f"""
                    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap;">
                            <div>
                                <h3 style="margin: 0px 0px 5px 0px; font-size:1.15rem; font-weight:700; color: #f8fafc;">🏢 {row['companyName']}</h3>
                                <p style="margin:0px; color:#cbd5e1; font-size:0.85rem;"><strong>Yetkili:</strong> {row['contactPerson']}</p>
                            </div>
                            <span style="background-color: #fbbf2415; color: #fbbf24; font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px; font-weight: 600;">
                                {row['sector'] or 'Belirtilmedi'}
                            </span>
                        </div>
                        <div style="margin-top: 10px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 0.8rem; color:#94a3b8;">
                            <div>📞 {row['phone'] or '-'}</div>
                            <div>✉️ {row['email'] or '-'}</div>
                            <div>📍 {row['address'] or '-'}</div>
                            <div>💼 {row['project_count']} Proje</div>
                        </div>
                        {f'<div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed #334155; font-size: 0.8rem; color:#cbd5e1;">📝 <strong>Not:</strong> {row["notes"]}</div>' if row['notes'] else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Delete action per customer
                    col_del, _ = st.columns([1, 10])
                    with col_del:
                        if st.button("Sil 🗑️", key=f"del_c_{row['id']}"):
                            if st.warning("Bu müşteriyi silmek istediğinize emin misiniz? (Tüm bağlı projeleri de silinecektir.)"):
                                pass
                            else:
                                try:
                                    run_insert_or_update('DELETE FROM "Customer" WHERE id = %s', (row['id'],))
                                    st.success("Müşteri silindi!")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Silme başarısız: {err}")
            else:
                st.info("Arama veya filtreleme ölçütlerinize uygun müşteri bulunamadı.")
        else:
            st.info("Veritabanında henüz müşteri kaydı bulunmuyor.")
    except Exception as ex:
        st.error(f"Müşteriler yüklenemedi: {ex}")

# ----------------- PAGE 3: PROJECTS -----------------
elif page == "💼 Projeler":
    render_header("Proje", "Yönetimi", "Tüm danışmanlık projelerinizi takip edin.")
    
    # Fetch customers first for Project Form selection
    cust_options = run_query('SELECT id, "companyName" FROM "Customer" ORDER BY "companyName"')
    
    # 1. New Project Form (Expander)
    with st.expander("➕ Yeni Proje Ekle", expanded=False):
        if not cust_options:
            st.warning("Proje eklemek için önce en az bir müşteri oluşturmalısınız!")
        else:
            with st.form("new_project_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    p_name = st.text_input("Proje Adı *")
                    cust_idx = st.selectbox(
                        "Müşteri Firma *", 
                        options=range(len(cust_options)), 
                        format_func=lambda x: cust_options[x]['companyName']
                    )
                    selected_cust_id = cust_options[cust_idx]['id']
                    
                    status = st.selectbox("Durum", list(STATUS_LABELS.keys()), format_func=lambda x: STATUS_LABELS[x])
                with col2:
                    budget = st.number_input("Bütçe (₺)", min_value=0.0, step=1000.0)
                    start_date = st.date_input("Başlangıç Tarihi", value=None)
                    end_date = st.date_input("Bitiş Tarihi", value=None)
                    
                p_desc = st.text_area("Açıklama")
                
                submitted_p = st.form_submit_button("Projeyi Kaydet")
                if submitted_p:
                    if not p_name:
                        st.warning("Proje adı zorunludur!")
                    else:
                        try:
                            p_id = f"py_{uuid.uuid4().hex[:20]}"
                            
                            # Convert dates
                            s_date = start_date.strftime("%Y-%m-%d") if start_date else None
                            e_date = end_date.strftime("%Y-%m-%d") if end_date else None
                            
                            query_p = """
                                INSERT INTO "Project" (id, name, description, status, "startDate", "endDate", budget, "customerId", "createdAt", "updatedAt")
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """
                            run_insert_or_update(query_p, (p_id, p_name, p_desc or None, status, s_date, e_date, budget or None, selected_cust_id))
                            st.success("Proje başarıyla eklendi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Proje ekleme başarısız: {e}")

    # Fetch and filter projects
    try:
        projects_list = run_query("""
            SELECT p.id, p.name, p.description, p.status, p."startDate", p."endDate", p.budget, p."customerId", c."companyName"
            FROM "Project" p
            JOIN "Customer" c ON p."customerId" = c.id
            ORDER BY p."createdAt" DESC
        """)
        
        if projects_list:
            df_proj = pd.DataFrame(projects_list)
            
            # Filter UI
            col_pf1, col_pf2 = st.columns([2, 1])
            with col_pf1:
                proj_search = st.text_input("🔍 Proje veya Müşteri adıyla ara")
            with col_pf2:
                status_filter_list = ["Tümü"] + list(STATUS_LABELS.keys())
                proj_status_filter = st.selectbox(
                    "Durum Filtresi", 
                    status_filter_list,
                    format_func=lambda x: STATUS_LABELS[x] if x in STATUS_LABELS else x
                )
                
            # Apply Filters
            f_df_proj = df_proj.copy()
            if proj_search:
                mask = (
                    f_df_proj['name'].str.contains(proj_search, case=False, na=False) |
                    f_df_proj['companyName'].str.contains(proj_search, case=False, na=False)
                )
                f_df_proj = f_df_proj[mask]
                
            if proj_status_filter != "Tümü":
                f_df_proj = f_df_proj[f_df_proj['status'] == proj_status_filter]
                
            # Table display using dataframe/markdown
            if not f_df_proj.empty:
                for idx, row in f_df_proj.iterrows():
                    s_label = STATUS_LABELS.get(row['status'], row['status'])
                    s_color = STATUS_COLORS.get(row['status'], '#94a3b8')
                    
                    st.markdown(f"""
                    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap;">
                            <div>
                                <h3 style="margin: 0px 0px 5px 0px; font-size:1.15rem; font-weight:700; color: #f8fafc;">💼 {row['name']}</h3>
                                <p style="margin:0px; color:#cbd5e1; font-size:0.85rem;"><strong>Müşteri:</strong> {row['companyName']}</p>
                            </div>
                            <span style="background-color: {s_color}22; color: {s_color}; font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px; font-weight: 600;">
                                {s_label}
                            </span>
                        </div>
                        <div style="margin-top: 10px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 0.8rem; color:#94a3b8;">
                            <div>📅 Başlangıç: {row['startDate'].strftime('%d.%m.%Y') if row['startDate'] else '-'}</div>
                            <div>📅 Bitiş: {row['endDate'].strftime('%d.%m.%Y') if row['endDate'] else '-'}</div>
                            <div style="font-weight:600; color: #fbbf24;">💰 Bütçe: {fmt_currency(row['budget'])}</div>
                        </div>
                        {f'<div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed #334155; font-size: 0.8rem; color:#cbd5e1;">📝 <strong>Açıklama:</strong> {row["description"]}</div>' if row['description'] else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Edit status and Delete row controls
                    col_status, col_delete, _ = st.columns([2, 1, 6])
                    
                    with col_status:
                        # Direct status updater selectbox
                        status_choices = list(STATUS_LABELS.keys())
                        current_status_idx = status_choices.index(row['status']) if row['status'] in status_choices else 0
                        
                        new_status = st.selectbox(
                            "Durumu Güncelle", 
                            status_choices, 
                            index=current_status_idx,
                            format_func=lambda x: STATUS_LABELS[x],
                            key=f"status_sel_{row['id']}"
                        )
                        
                        if new_status != row['status']:
                            try:
                                run_insert_or_update('UPDATE "Project" SET status = %s, "updatedAt" = NOW() WHERE id = %s', (new_status, row['id']))
                                st.success("Durum güncellendi!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Güncelleme başarısız: {err}")
                                
                    with col_delete:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("Sil 🗑️", key=f"del_p_{row['id']}"):
                            try:
                                run_insert_or_update('DELETE FROM "Project" WHERE id = %s', (row['id'],))
                                st.success("Proje silindi!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Silme başarısız: {err}")
            else:
                st.info("Arama veya filtreleme kriterlerine uygun proje bulunamadı.")
        else:
            st.info("Kayıtlı proje bulunmamaktadır.")
    except Exception as ex:
        st.error(f"Projeler yüklenemedi: {ex}")

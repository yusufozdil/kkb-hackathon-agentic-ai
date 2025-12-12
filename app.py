import streamlit as st
import json
from datetime import datetime, date
from main import run_orchestrator

st.set_page_config(
    page_title="Şirket Risk Analizi",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Şirket Risk Analizi Sistemi")
st.markdown("---")

# Sidebar for inputs
with st.sidebar:
    st.header("Arama Parametreleri")
    
    company_name = st.text_input(
        "Şirket Adı",
        placeholder="Örn: ACME Teknoloji A.Ş.",
        help="Analiz yapmak istediğiniz şirketin adını girin"
    )
    
    st.subheader("Tarih Aralığı")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Başlangıç",
            value=date(2024, 11, 1),
            help="Tarama başlangıç tarihi"
        )
    
    with col2:
        end_date = st.date_input(
            "Bitiş",
            value=date.today(),
            help="Tarama bitiş tarihi"
        )
    
    st.markdown("---")
    
    analyze_button = st.button(
        "🚀 Analizi Başlat",
        type="primary",
        use_container_width=True
    )

# Main content area
if analyze_button:
    if not company_name:
        st.error("⚠️ Lütfen bir şirket adı girin!")
    elif start_date > end_date:
        st.error("⚠️ Başlangıç tarihi bitiş tarihinden önce olmalı!")
    else:
        # Convert dates to YYYYMMDD format
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        with st.spinner(f"🔄 {company_name} için analiz yapılıyor... Bu işlem birkaç dakika sürebilir."):
            try:
                # Run the orchestrator
                result = run_orchestrator(company_name, start_str, end_str)
                
                st.success("✅ Analiz tamamlandı!")
                st.markdown("---")
                
                # Try to parse as JSON
                try:
                    report_data = json.loads(result)
                    
                    # Display results in organized sections
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Yasak Durumu",
                            "YASAKLİ ⛔" if report_data.get("is_banned") else "TEMİZ ✅"
                        )
                    
                    with col2:
                        confidence = report_data.get("confidence_score", 0)
                        st.metric("Güven Skoru", f"{confidence}/100")
                    
                    with col3:
                        sources = report_data.get("sources", [])
                        st.metric("Kaynak Sayısı", len(sources))
                    
                    st.markdown("---")
                    
                    # Report text
                    st.subheader("📄 Risk Raporu")
                    st.info(report_data.get("report_text", "Rapor metni bulunamadı."))
                    
                    # Sources
                    if sources:
                        st.subheader("📚 Kullanılan Kaynaklar")
                        for source in sources:
                            st.badge(source)
                    
                    # Status
                    status = report_data.get("status", "UNKNOWN")
                    if status == "SUCCESS":
                        st.success(f"Durum: {status}")
                    else:
                        st.warning(f"Durum: {status}")
                    
                    # Show raw JSON in expander
                    with st.expander("🔧 Ham JSON Çıktısı"):
                        st.json(report_data)
                
                except json.JSONDecodeError:
                    # If not valid JSON, show as text
                    st.subheader("📄 Analiz Sonucu")
                    st.text_area("Rapor", result, height=400)
                    
                    with st.expander("⚠️ JSON Parse Hatası"):
                        st.warning("Çıktı geçerli JSON formatında değil. Ham metin olarak gösteriliyor.")
            
            except Exception as e:
                st.error(f"❌ Analiz sırasında hata oluştu: {str(e)}")
                with st.expander("Hata Detayları"):
                    st.exception(e)

else:
    # Welcome screen
    st.info("👈 Sol taraftan şirket adı ve tarih aralığını girerek analizi başlatın.")
    
    st.markdown("### 📋 Sistem Özellikleri")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🚫 Yasak Listesi Kontrolü**
        - Resmi Gazete taraması
        - OCR ile otomatik veri çıkarma
        - Veritabanı önbellekleme
        """)
    
    with col2:
        st.markdown("""
        **📰 Haber Analizi**
        - Google News taraması
        - Türkçe kaynak filtreleme
        - Tarih bazlı sıralama
        """)
    
    with col3:
        st.markdown("""
        **🏢 Ticaret Sicili**
        - TOBB entegrasyonu
        - Şirket bilgileri
        - İlan takibi
        """)
    
    st.markdown("---")
    st.markdown("### 🤖 AI Teknolojisi")
    st.markdown("""
    Bu sistem **CrewAI** framework'ü kullanarak:
    - Lead Researcher: Veri toplama ve doğrulama
    - Reporting Analyst: Risk analizi ve raporlama
    
    AI ajanları koordineli çalışarak kapsamlı due diligence gerçekleştirir.
    """)

# Footer
st.markdown("---")
st.caption("🔐 KKB Hackathon - Agentic AI | Powered by CrewAI & Ollama")

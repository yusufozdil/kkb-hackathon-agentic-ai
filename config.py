"""
KKB Kloudeks API Konfigürasyonu
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# .env dosyasını yükle
load_dotenv()

# API anahtarlarını ve ayarları çek
KKB_API_KEY = os.getenv("KKB_API_KEY")
KKB_BASE_URL = os.getenv("KKB_BASE_URL", "https://mia.csp.kloudeks.com/v1")
KKB_MODEL = os.getenv("KKB_MODEL", "gpt-oss-120b")
KKB_EMBEDDING_MODEL = os.getenv("KKB_EMBEDDING_MODEL", "qwen3-embedding-8b")

# CrewAI/LiteLLM için standart OpenAI ortam değişkenlerini ayarla
# Farklı kütüphaneler farklı isimler kullanabilir, hepsini ayarlayalım
if KKB_API_KEY:
    os.environ["OPENAI_API_KEY"] = KKB_API_KEY
    os.environ["OPENAI_API_BASE"] = KKB_BASE_URL
    os.environ["OPENAI_BASE_URL"] = KKB_BASE_URL
    # LiteLLM için de ayarla
    os.environ["OPENAI_API_BASE_URL"] = KKB_BASE_URL


def get_kloudeks_llm(temperature=0.7, max_tokens=8192):
    """
    Kloudeks API'si için LLM instance'ı oluşturur.
    CrewAI agent'larında kullanım için.
    
    Args:
        temperature (float): Model sıcaklığı (0-1 arası)
        max_tokens (int): Maksimum token sayısı (default: 8192 - uzun raporlar için)
    
    Returns:
        ChatOpenAI: LangChain uyumlu LLM instance'ı
    """
    if not KKB_API_KEY or KKB_API_KEY == "sk-.....":
        raise ValueError(
            "KKB_API_KEY bulunamadı! Lütfen .env dosyasına geçerli bir API key ekleyin."
        )
    
    return ChatOpenAI(
        model=KKB_MODEL,
        openai_api_key=KKB_API_KEY,
        openai_api_base=KKB_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_openai_client():
    """
    Doğrudan OpenAI client kullanımı için
    (test veya embedding amaçlı)
    """
    from openai import OpenAI
    
    if not KKB_API_KEY or KKB_API_KEY == "sk-.....":
        raise ValueError(
            "KKB_API_KEY bulunamadı! Lütfen .env dosyasına geçerli bir API key ekleyin."
        )
    
    return OpenAI(
        base_url=KKB_BASE_URL,
        api_key=KKB_API_KEY
    )


# Test fonksiyonu
if __name__ == "__main__":
    print("🔧 Kloudeks API Konfigürasyonu Test Ediliyor...")
    print(f"Base URL: {KKB_BASE_URL}")
    print(f"Model: {KKB_MODEL}")
    print(f"API Key: {'✅ Ayarlanmış' if KKB_API_KEY and KKB_API_KEY != 'sk-.....' else '❌ Eksik'}")
    
    try:
        client = get_openai_client()
        print("\n📡 Mevcut modeller kontrol ediliyor...")
        models = client.models.list()
        print("✅ Kullanılabilir modeller:")
        for m in models:
            print(f"  - {m.id}")
        
        print("\n💬 Test mesajı gönderiliyor...")
        resp = client.chat.completions.create(
            model=KKB_MODEL,
            messages=[{"role": "user", "content": "Merhaba! Kendini tanıt."}],
        )
        print(f"✅ Yanıt: {resp.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")


from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import json
import os


def sanitize_text(text):
    """
    PDF oluşturulurken sorun çıkaran karakterleri temizler.
    Özellikle tire işaretlerini (-) standart ASCII tireye dönüştürür.
    """
    if not isinstance(text, str):
        return text
    
    # Tire işaretlerini düzelt
    text = text.replace('–', '-')  # en-dash
    text = text.replace('—', '-')  # em-dash
    text = text.replace('―', '-')  # horizontal bar
    
    # Tırnak işaretlerini düzelt
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text


def register_turkish_font():
    """
    Türkçe karakter desteği için font kaydı.
    macOS, Windows ve Linux sistemlerde çalışır.
    """
    import platform
    system = platform.system()
    
    try:
        if system == 'Darwin':  # macOS
            # macOS sistem fontları
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial.ttf',
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
            ]
            bold_paths = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/Library/Fonts/Arial Bold.ttf',
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
                        # Bold font
                        for bold_path in bold_paths:
                            if os.path.exists(bold_path):
                                pdfmetrics.registerFont(TTFont('TurkishFont-Bold', bold_path))
                                break
                        else:
                            pdfmetrics.registerFont(TTFont('TurkishFont-Bold', font_path))
                        return 'TurkishFont'
                    except:
                        continue
                        
        elif system == 'Windows':
            # Windows Arial font
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('TurkishFont-Bold', bold_path))
                else:
                    pdfmetrics.registerFont(TTFont('TurkishFont-Bold', font_path))
                return 'TurkishFont'
                
        elif system == 'Linux':
            # Linux fontları
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            ]
            bold_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            ]
            
            for i, font_path in enumerate(font_paths):
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
                    if i < len(bold_paths) and os.path.exists(bold_paths[i]):
                        pdfmetrics.registerFont(TTFont('TurkishFont-Bold', bold_paths[i]))
                    else:
                        pdfmetrics.registerFont(TTFont('TurkishFont-Bold', font_path))
                    return 'TurkishFont'
                    
    except Exception as e:
        print(f"Font kaydı hatası: {e}")
    
    # Fallback: Helvetica (Türkçe karakter desteği sınırlı)
    return 'Helvetica'


def json_to_pdf(json_data, output_path, company_name, start_date, end_date):
    """
    JSON risk raporunu PDF'e çevirir.
    
    Args:
        json_data: Dict veya JSON string
        output_path: PDF dosya yolu
        company_name: Şirket adı
        start_date: Başlangıç tarihi (YYYYMMDD)
        end_date: Bitiş tarihi (YYYYMMDD)
    """
    # JSON parse
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    # Font kaydı
    font_family = register_turkish_font()
    
    # PDF oluştur
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Stiller
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=f'{font_family}-Bold' if font_family == 'TurkishFont' else 'Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=f'{font_family}-Bold' if font_family == 'TurkishFont' else 'Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=font_family if font_family == 'TurkishFont' else 'Helvetica',
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=16
    )
    
    # İçerik
    story = []
    
    # Başlık
    story.append(Paragraph("ŞİRKET RİSK ANALİZ RAPORU", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Tarih bilgisi
    report_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph(f"<i>Rapor Tarihi: {report_date}</i>", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Şirket bilgileri tablosu
    story.append(Paragraph("Şirket Bilgileri", heading_style))
    
    # Tarihleri formatla
    start_formatted = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    end_formatted = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    
    company_data = [
        ["Şirket Adı:", company_name],
        ["Analiz Dönemi:", f"{start_formatted} / {end_formatted}"],
        ["Durum:", data.get("status", "N/A")]
    ]
    
    company_table = Table(company_data, colWidths=[5*cm, 12*cm])
    company_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), f'{font_family}-Bold' if font_family == 'TurkishFont' else 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), font_family if font_family == 'TurkishFont' else 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(company_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Risk metrikleri
    story.append(Paragraph("Risk Değerlendirmesi", heading_style))
    
    is_banned = data.get("is_banned", False)
    confidence = data.get("confidence_score", 0)
    
    risk_color = colors.red if is_banned else colors.green
    ban_status = "YASAKLI" if is_banned else "TEMİZ"
    
    risk_data = [
        ["Yasak Durumu:", ban_status],
        ["Güven Skoru:", f"{confidence}/100"],
        ["Kaynak Sayısı:", str(len(data.get("sources", [])))]
    ]
    
    risk_table = Table(risk_data, colWidths=[5*cm, 12*cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('BACKGROUND', (1, 0), (1, 0), risk_color if is_banned else colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), f'{font_family}-Bold' if font_family == 'TurkishFont' else 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), f'{font_family}-Bold' if font_family == 'TurkishFont' else 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(risk_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Rapor Metni
    story.append(Paragraph("Detaylı Analiz", heading_style))
    report_text = data.get("report_text", "Rapor metni bulunamadı.")
    
    # Uzun metni paragraflara böl
    paragraphs = report_text.split('\n')
    for para in paragraphs:
        if para.strip():
            # Metni temizle (tire sorunları için)
            clean_para = sanitize_text(para.strip())
            story.append(Paragraph(clean_para, body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Kaynaklar
    sources = data.get("sources", [])
    if sources:
        story.append(Paragraph("Kullanılan Kaynaklar", heading_style))
        
        # Kaynakları listele - URL'leri ayır
        for i, source in enumerate(sources, 1):
            if source.startswith('http'):
                # URL ise kısalt ve tıklanabilir yap
                display_text = source if len(source) <= 80 else source[:77] + "..."
                source_para = Paragraph(f"{i}. <link href='{source}'>{display_text}</link>", body_style)
            else:
                # Normal kaynak (örn: 'gazette', 'news')
                source_para = Paragraph(f"{i}. {source.title()}", body_style)
            story.append(source_para)
    
    # Footer
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=font_family if font_family == 'TurkishFont' else 'Helvetica',
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Bu rapor AI destekli sistemler tarafından otomatik olarak oluşturulmuştur.", footer_style))
    story.append(Paragraph("KKB Hackathon - Agentic AI", footer_style))
    
    # PDF oluştur
    doc.build(story)
    return output_path


if __name__ == "__main__":
    # Test
    sample_json = {
        "report_text": "Şirket analizi sonuçları: Düşük risk profili tespit edilmiştir. Resmi Gazete kayıtlarında herhangi bir yasak bulunmamaktadır.",
        "is_banned": False,
        "confidence_score": 85,
        "sources": ["news", "gazette"],
        "status": "SUCCESS"
    }
    
    json_to_pdf(
        sample_json,
        "test_report.pdf",
        "ACME Teknoloji A.Ş.",
        "20241101",
        "20241130"
    )
    print("PDF oluşturuldu: test_report.pdf")

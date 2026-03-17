"""
PDF генератор для дизайн-брифа
Создаёт красивый PDF-документ с результатами анализа
"""

import os
import asyncio
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Цвета
DARK = HexColor("#0D0D0D")
ACCENT = HexColor("#C8A96E")
LIGHT_GRAY = HexColor("#F5F5F0")
MID_GRAY = HexColor("#888888")
WHITE = HexColor("#FFFFFF")


def parse_hex_colors(colors_str: str) -> list:
    """Извлекает hex-цвета из строки"""
    import re
    hexes = re.findall(r'#[0-9A-Fa-f]{6}', colors_str)
    return hexes[:3] if hexes else ["#1A1A1A", "#888888", "#F5F5F0"]


async def generate_brief_pdf(data: dict, analysis: dict, moodboard_text: str, user_id: int) -> str:
    """Генерирует PDF-бриф и возвращает путь к файлу"""

    os.makedirs("/tmp/briefs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = f"/tmp/briefs/brief_{user_id}_{timestamp}.pdf"

    params = analysis.get("params", {})
    brand_name = data.get('brand_name', 'Brand Brief')

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    # Кастомные стили
    title_style = ParagraphStyle(
        'CustomTitle',
        fontSize=32,
        textColor=DARK,
        spaceAfter=4,
        spaceBefore=0,
        leading=36,
        fontName='Helvetica-Bold',
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        fontSize=11,
        textColor=MID_GRAY,
        spaceAfter=20,
        fontName='Helvetica',
        letterSpacing=2,
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        fontSize=8,
        textColor=ACCENT,
        spaceBefore=20,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        letterSpacing=3,
    )

    body_style = ParagraphStyle(
        'Body',
        fontSize=10,
        textColor=DARK,
        spaceAfter=6,
        fontName='Helvetica',
        leading=16,
    )

    label_style = ParagraphStyle(
        'Label',
        fontSize=8,
        textColor=MID_GRAY,
        spaceAfter=2,
        fontName='Helvetica',
        letterSpacing=1,
    )

    value_style = ParagraphStyle(
        'Value',
        fontSize=10,
        textColor=DARK,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        leading=14,
    )

    story = []

    # ── Шапка ──────────────────────────────────────────────────────────────
    story.append(Paragraph("DESIGN BRIEF", subtitle_style))
    story.append(Paragraph(brand_name.upper(), title_style))
    story.append(Paragraph(
        f"{params.get('ARCHETYPE', '')}  ·  {datetime.now().strftime('%d.%m.%Y')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=20))

    # ── Позиционирование ───────────────────────────────────────────────────
    if params.get('POSITIONING'):
        story.append(Paragraph("ПОЗИЦИОНИРОВАНИЕ", section_style))
        story.append(Paragraph(params.get('POSITIONING', ''), body_style))

    if params.get('INSIGHT'):
        story.append(Paragraph("КЛЮЧЕВОЙ ИНСАЙТ", section_style))
        story.append(Paragraph(params.get('INSIGHT', ''), body_style))

    # ── Концепция ──────────────────────────────────────────────────────────
    story.append(Paragraph("ВИЗУАЛЬНАЯ КОНЦЕПЦИЯ", section_style))
    story.append(Paragraph(
        f"<b>{params.get('CONCEPT_NAME', '')}</b>",
        ParagraphStyle('ConceptName', fontSize=14, textColor=DARK, spaceAfter=6, fontName='Helvetica-Bold')
    ))
    story.append(Paragraph(params.get('CONCEPT_ESSENCE', ''), body_style))

    # ── Цветовая палитра ───────────────────────────────────────────────────
    story.append(Paragraph("ЦВЕТОВАЯ ПАЛИТРА", section_style))

    primary_colors = parse_hex_colors(params.get('COLORS_PRIMARY', '#1A1A1A #888888 #F5F5F0'))
    accent_colors = parse_hex_colors(params.get('COLORS_ACCENT', '#C8A96E'))
    all_colors = (primary_colors + accent_colors)[:5]

    # Таблица цветов
    color_cells = []
    color_labels = []
    for hex_color in all_colors:
        try:
            c = HexColor(hex_color)
            color_cells.append('')
            color_labels.append(hex_color.upper())
        except:
            pass

    if color_cells:
        # Цветные блоки
        palette_data = [color_cells, color_labels]
        col_width = (170*mm) / max(len(color_cells), 1)
        palette_table = Table(
            palette_data,
            colWidths=[col_width] * len(color_cells),
            rowHeights=[18*mm, 6*mm]
        )
        table_style = [
            ('GRID', (0,0), (-1,-1), 0, white),
            ('FONTSIZE', (0,1), (-1,1), 7),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TEXTCOLOR', (0,1), (-1,1), MID_GRAY),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]
        for i, hex_color in enumerate(all_colors):
            try:
                table_style.append(('BACKGROUND', (i,0), (i,0), HexColor(hex_color)))
            except:
                pass

        palette_table.setStyle(TableStyle(table_style))
        story.append(palette_table)
        story.append(Spacer(1, 4*mm))

    story.append(Paragraph(params.get('COLORS_MOOD', ''), body_style))

    # ── Типографика ────────────────────────────────────────────────────────
    story.append(Paragraph("ТИПОГРАФИКА", section_style))

    typo_data = [
        ["ЗАГОЛОВКИ", params.get('TYPOGRAPHY_DISPLAY', '—')],
        ["ТЕКСТ", params.get('TYPOGRAPHY_BODY', '—')],
        ["СТИЛЬ", params.get('TYPOGRAPHY_STYLE', '—')],
    ]
    typo_table = Table(typo_data, colWidths=[35*mm, 135*mm])
    typo_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('TEXTCOLOR', (0,0), (0,-1), MID_GRAY),
        ('TEXTCOLOR', (1,0), (1,-1), DARK),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(typo_table)

    # ── Образный ряд ───────────────────────────────────────────────────────
    story.append(Paragraph("ОБРАЗНЫЙ РЯД", section_style))
    story.append(Paragraph(params.get('IMAGERY_STYLE', ''), body_style))

    if params.get('IMAGERY_SCENES'):
        scenes = params.get('IMAGERY_SCENES', '').split(',')
        for scene in scenes[:5]:
            story.append(Paragraph(f"→ {scene.strip()}", body_style))

    if params.get('IMAGERY_AVOID'):
        story.append(Paragraph("ИЗБЕГАТЬ:", section_style))
        story.append(Paragraph(params.get('IMAGERY_AVOID', ''), body_style))

    # ── Референсы ──────────────────────────────────────────────────────────
    story.append(Paragraph("РЕФЕРЕНСЫ", section_style))
    story.append(Paragraph(params.get('REFERENCES', ''), body_style))

    # ── Слоганы ────────────────────────────────────────────────────────────
    if params.get('TAGLINE_IDEAS'):
        story.append(Paragraph("ИДЕИ СЛОГАНОВ", section_style))
        taglines = params.get('TAGLINE_IDEAS', '').split('|')
        for tl in taglines:
            story.append(Paragraph(
                f"«{tl.strip()}»",
                ParagraphStyle('Tagline', fontSize=11, textColor=DARK, spaceAfter=6,
                              fontName='Helvetica-BoldOblique', leading=16)
            ))

    # ── Ключевая эмоция ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=16, spaceAfter=12))
    story.append(Paragraph("КЛЮЧЕВОЕ ПОСЛАНИЕ", section_style))
    story.append(Paragraph(
        params.get('EMOTION_TRIGGER', ''),
        ParagraphStyle('EmotionKey', fontSize=13, textColor=DARK, spaceAfter=20,
                      fontName='Helvetica-BoldOblique', leading=20)
    ))

    # ── Бриф сырой (для дизайнера) ─────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=12))
    story.append(Paragraph("ОТВЕТЫ ЗАКАЗЧИКА", section_style))

    qa_pairs = [
        ("Бренд", data.get('brand_name', '—')),
        ("Сфера", data.get('brand_sphere', '—')),
        ("Продукт", data.get('brand_product', '—')),
        ("Миссия", data.get('brand_mission', '—')),
        ("Ценности", data.get('brand_values', '—')),
        ("История", data.get('brand_story', '—')),
        ("ЦА портрет", data.get('audience_who', '—')),
        ("Боль ЦА", data.get('audience_pain', '—')),
        ("Мечта ЦА", data.get('audience_desire', '—')),
        ("Конкуренты", data.get('competitors_who', '—')),
        ("Отличие", data.get('competitors_diff', '—')),
        ("Нравится", data.get('visual_like', '—')),
        ("Не нравится", data.get('visual_dislike', '—')),
        ("Настроение", data.get('visual_mood', '—')),
        ("Слова", data.get('assoc_words', '—')),
        ("Персонаж", data.get('assoc_person', '—')),
        ("Место", data.get('assoc_place', '—')),
        ("Чувство", data.get('assoc_feeling', '—')),
        ("Заметки", data.get('extra_notes', '—')),
    ]

    for label, value in qa_pairs:
        if value and value != '—':
            story.append(Paragraph(label.upper(), label_style))
            story.append(Paragraph(value, value_style))

    # ── Генерируем PDF ─────────────────────────────────────────────────────
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: doc.build(story))

    return pdf_path

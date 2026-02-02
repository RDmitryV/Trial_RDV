"""PDF report exporter using ReportLab."""

from typing import Dict, Any, List, Optional
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, KeepTogether
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents

from .gost_formatter import GOSTFormatter


class PDFExporter:
    """
    PDF report exporter using ReportLab.

    Exports report to PDF format with GOST 7.32-2017 formatting.
    """

    def __init__(self):
        self.formatter = GOSTFormatter()
        self.story = []
        self.styles = None
        self.figure_counter = 0
        self.table_counter = 0

        # Try to register Times New Roman font (fallback to default if not available)
        try:
            pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
            self.font_name = 'TimesNewRoman'
        except:
            # Use default font if Times New Roman is not available
            self.font_name = 'Times-Roman'

    def create_document(self, report_data: Dict[str, Any]) -> bytes:
        """
        Create PDF document from report data.

        Args:
            report_data: Dictionary with report content

        Returns:
            PDF file bytes
        """
        buffer = io.BytesIO()

        # Create document with GOST margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=30*mm,
            rightMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
            title=report_data.get("title_page", {}).get("title", "Отчет"),
            author=report_data.get("title_page", {}).get("organization", "")
        )

        # Setup styles
        self._setup_styles()

        # Build story
        self._add_title_page(report_data.get("title_page", {}))
        self._add_abstract(report_data.get("abstract", {}))
        self._add_table_of_contents()
        self._add_introduction(report_data.get("introduction", {}))
        self._add_main_sections(report_data.get("main_sections", []))
        self._add_conclusion(report_data.get("conclusion", {}))
        self._add_bibliography(report_data.get("bibliography", []))
        self._add_appendices(report_data.get("appendices", []))

        # Build PDF
        doc.build(self.story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)

        buffer.seek(0)
        return buffer.read()

    def _setup_styles(self) -> None:
        """Setup document styles according to GOST."""
        self.styles = getSampleStyleSheet()

        # GOST Normal style
        self.styles.add(ParagraphStyle(
            name='GOSTNormal',
            fontName=self.font_name,
            fontSize=14,
            leading=21,  # 1.5 line spacing
            alignment=TA_JUSTIFY,
            firstLineIndent=12.5*mm,
            spaceAfter=6,
        ))

        # GOST Heading 0 (structural elements)
        self.styles.add(ParagraphStyle(
            name='GOSTHeading0',
            fontName=self.font_name,
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=12,
            fontWeight='bold',
        ))

        # GOST Heading 1 (sections)
        self.styles.add(ParagraphStyle(
            name='GOSTHeading1',
            fontName=self.font_name,
            fontSize=14,
            leading=16,
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=12,
            fontWeight='bold',
        ))

        # GOST Heading 2 (subsections)
        self.styles.add(ParagraphStyle(
            name='GOSTHeading2',
            fontName=self.font_name,
            fontSize=14,
            leading=16,
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=6,
            fontWeight='bold',
        ))

        # Caption style
        self.styles.add(ParagraphStyle(
            name='Caption',
            fontName=self.font_name,
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=6,
        ))

        # Bibliography style
        self.styles.add(ParagraphStyle(
            name='Bibliography',
            fontName=self.font_name,
            fontSize=14,
            leading=21,
            alignment=TA_LEFT,
            leftIndent=10*mm,
            firstLineIndent=-10*mm,
            spaceAfter=6,
        ))

    def _add_page_number(self, canvas, doc) -> None:
        """Add page number to footer."""
        canvas.saveState()
        canvas.setFont(self.font_name, 12)
        page_number = canvas.getPageNumber()
        if page_number > 1:  # Don't number title page
            text = str(page_number)
            canvas.drawCentredString(A4[0] / 2, 15*mm, text)
        canvas.restoreState()

    def _add_title_page(self, data: Dict[str, Any]) -> None:
        """Add title page."""
        # Organization name
        org = Paragraph(
            f"<b>{data.get('organization', '')}</b>",
            self.styles['GOSTHeading0']
        )
        self.story.append(org)
        self.story.append(Spacer(1, 10*cm))

        # Report type
        report_type = Paragraph(
            f"<b>{data.get('report_type', '').upper()}</b>",
            self.styles['GOSTHeading0']
        )
        self.story.append(report_type)
        self.story.append(Spacer(1, 1*cm))

        # Title
        title = Paragraph(
            f"<b>{data.get('title', '')}</b>",
            self.styles['GOSTHeading0']
        )
        self.story.append(title)
        self.story.append(Spacer(1, 10*cm))

        # Date
        date = Paragraph(
            data.get('date', ''),
            self.styles['GOSTHeading0']
        )
        self.story.append(date)
        self.story.append(PageBreak())

    def _add_abstract(self, data: Dict[str, Any]) -> None:
        """Add abstract section."""
        # Heading
        heading = Paragraph("<b>РЕФЕРАТ</b>", self.styles['GOSTHeading0'])
        self.story.append(heading)
        self.story.append(Spacer(1, 1*cm))

        # Statistics
        stats = data.get("statistics", {})
        stats_text = (
            f"Отчет содержит {stats.get('pages', 0)} страниц, "
            f"{stats.get('figures', 0)} рисунков, "
            f"{stats.get('tables', 0)} таблиц, "
            f"{stats.get('sources', 0)} источников, "
            f"{stats.get('appendices', 0)} приложений."
        )
        self.story.append(Paragraph(stats_text, self.styles['GOSTNormal']))
        self.story.append(Spacer(1, 0.5*cm))

        # Keywords
        keywords = data.get("keywords", [])
        if keywords:
            keywords_text = f"<b>КЛЮЧЕВЫЕ СЛОВА:</b> {', '.join(keywords).upper()}"
            self.story.append(Paragraph(keywords_text, self.styles['GOSTNormal']))
            self.story.append(Spacer(1, 0.5*cm))

        # Summary
        summary = data.get("summary", "")
        self.story.append(Paragraph(summary, self.styles['GOSTNormal']))
        self.story.append(PageBreak())

    def _add_table_of_contents(self) -> None:
        """Add table of contents."""
        # Heading
        heading = Paragraph("<b>СОДЕРЖАНИЕ</b>", self.styles['GOSTHeading0'])
        self.story.append(heading)
        self.story.append(Spacer(1, 1*cm))

        # Add TOC (simplified version)
        # Note: For full TOC support, ReportLab requires additional setup
        toc_text = "ВВЕДЕНИЕ .......... 3"
        self.story.append(Paragraph(toc_text, self.styles['GOSTNormal']))

        self.story.append(PageBreak())

    def _add_introduction(self, data: Dict[str, Any]) -> None:
        """Add introduction section."""
        # Heading
        heading = Paragraph("<b>ВВЕДЕНИЕ</b>", self.styles['GOSTHeading0'])
        self.story.append(heading)
        self.story.append(Spacer(1, 0.5*cm))

        # Content
        text = data.get("text", "")
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                self.story.append(Paragraph(para, self.styles['GOSTNormal']))
                self.story.append(Spacer(1, 0.3*cm))

        self.story.append(PageBreak())

    def _add_main_sections(self, sections: List[Dict[str, Any]]) -> None:
        """Add main sections."""
        for i, section in enumerate(sections, 1):
            # Section heading
            title = f"<b>{i} {section.get('title', '').upper()}</b>"
            heading = Paragraph(title, self.styles['GOSTHeading1'])
            self.story.append(heading)
            self.story.append(Spacer(1, 0.5*cm))

            # Section content
            content = section.get("content", "")
            if content:
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        self.story.append(Paragraph(para, self.styles['GOSTNormal']))
                        self.story.append(Spacer(1, 0.3*cm))

            # Add subsections
            for j, subsection in enumerate(section.get("subsections", []), 1):
                # Subsection heading
                subtitle = f"<b>{i}.{j} {subsection.get('title', '')}</b>"
                subheading = Paragraph(subtitle, self.styles['GOSTHeading2'])
                self.story.append(subheading)
                self.story.append(Spacer(1, 0.3*cm))

                # Subsection content
                subcontent = subsection.get("content", "")
                if subcontent:
                    paragraphs = subcontent.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            self.story.append(Paragraph(para, self.styles['GOSTNormal']))
                            self.story.append(Spacer(1, 0.3*cm))

                # Add figures
                for figure in subsection.get("figures", []):
                    self._add_figure(figure)

                # Add tables
                for table in subsection.get("tables", []):
                    self._add_table(table)

            self.story.append(PageBreak())

    def _add_figure(self, figure_data: Dict[str, Any]) -> None:
        """Add figure to document."""
        self.figure_counter += 1

        # Add image if available
        image_bytes = figure_data.get("image_bytes")
        if image_bytes:
            try:
                image_stream = io.BytesIO(image_bytes)
                img = Image(image_stream, width=15*cm, height=10*cm, kind='proportional')
                self.story.append(img)
            except Exception:
                # Skip if image cannot be loaded
                pass

        # Add caption
        caption = self.formatter.format_figure_caption(
            self.figure_counter,
            figure_data.get("title", "")
        )
        self.story.append(Paragraph(caption, self.styles['Caption']))
        self.story.append(Spacer(1, 0.5*cm))

    def _add_table(self, table_data: Dict[str, Any]) -> None:
        """Add table to document."""
        self.table_counter += 1

        # Add caption
        caption = self.formatter.format_table_caption(
            self.table_counter,
            table_data.get("title", "")
        )
        self.story.append(Paragraph(caption, self.styles['GOSTNormal']))
        self.story.append(Spacer(1, 0.3*cm))

        # Create table
        data = table_data.get("data", [])
        headers = table_data.get("headers", [])

        if data and headers:
            table_data_list = [headers] + data

            table = Table(table_data_list, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))

            self.story.append(table)

        self.story.append(Spacer(1, 0.5*cm))

    def _add_conclusion(self, data: Dict[str, Any]) -> None:
        """Add conclusion section."""
        # Heading
        heading = Paragraph("<b>ЗАКЛЮЧЕНИЕ</b>", self.styles['GOSTHeading0'])
        self.story.append(heading)
        self.story.append(Spacer(1, 0.5*cm))

        # Content
        text = data.get("text", "")
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                self.story.append(Paragraph(para, self.styles['GOSTNormal']))
                self.story.append(Spacer(1, 0.3*cm))

        self.story.append(PageBreak())

    def _add_bibliography(self, bibliography: List[Dict[str, Any]]) -> None:
        """Add bibliography section."""
        # Heading
        heading = Paragraph("<b>СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ</b>", self.styles['GOSTHeading0'])
        self.story.append(heading)
        self.story.append(Spacer(1, 0.5*cm))

        # Bibliography entries
        for i, entry in enumerate(bibliography, 1):
            entry_text = self._format_bibliography_entry(entry)
            full_text = f"{i}. {entry_text}"
            self.story.append(Paragraph(full_text, self.styles['Bibliography']))

        self.story.append(PageBreak())

    def _format_bibliography_entry(self, entry: Dict[str, Any]) -> str:
        """Format bibliography entry."""
        entry_type = entry.get("type", "website")

        if entry_type == "website":
            title = entry.get("title", "")
            url = entry.get("url", "")
            access_date = entry.get("access_date", "")

            text = f"{title}"
            if url:
                text += f". – URL: {url}"
            if access_date:
                text += f" (дата обращения: {access_date})"

            return text

        return entry.get("title", "")

    def _add_appendices(self, appendices: List[Dict[str, Any]]) -> None:
        """Add appendices."""
        if not appendices:
            return

        for appendix in appendices:
            # Heading
            heading = Paragraph(
                f"<b>ПРИЛОЖЕНИЕ {appendix.get('letter', 'А')}</b>",
                self.styles['GOSTHeading0']
            )
            self.story.append(heading)
            self.story.append(Spacer(1, 0.3*cm))

            # Title
            title = Paragraph(appendix.get('title', ''), self.styles['GOSTHeading0'])
            self.story.append(title)
            self.story.append(Spacer(1, 0.5*cm))

            # Content
            content = appendix.get("content", "")
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    self.story.append(Paragraph(para, self.styles['GOSTNormal']))
                    self.story.append(Spacer(1, 0.3*cm))

            self.story.append(PageBreak())

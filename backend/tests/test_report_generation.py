"""Tests for report generation module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from app.services.report_generation.gost_formatter import GOSTFormatter, GOSTPageSettings, GOSTNumberingRules
from app.services.report_generation.content_generator import ContentGenerator
from app.services.report_generation.visualization import VisualizationService
from app.services.report_generation.docx_exporter import DOCXExporter
from app.services.report_generation.pdf_exporter import PDFExporter
from app.services.report_generation.report_generator import ReportGenerator
from app.models.research import Research, ResearchStatus
from app.models.report import Report, ReportFormat, ReportStatus


class TestGOSTFormatter:
    """Tests for GOST formatter."""

    def test_format_heading_structural_element(self):
        """Test formatting structural element heading."""
        formatter = GOSTFormatter()
        result = formatter.format_heading("ВВЕДЕНИЕ", 0)

        assert result["text"] == "ВВЕДЕНИЕ"
        assert result["bold"] is True
        assert result["alignment"] == "center"
        assert result["page_break_before"] is True

    def test_format_heading_section(self):
        """Test formatting section heading."""
        formatter = GOSTFormatter()
        result = formatter.format_heading("Анализ рынка", 1)

        assert result["text"] == "АНАЛИЗ РЫНКА"
        assert result["bold"] is True
        assert result["alignment"] == "left"

    def test_format_figure_caption(self):
        """Test formatting figure caption."""
        formatter = GOSTFormatter()
        caption = formatter.format_figure_caption(1, "График динамики рынка")

        assert caption == "Рисунок 1 – График динамики рынка"

    def test_format_table_caption(self):
        """Test formatting table caption."""
        formatter = GOSTFormatter()
        caption = formatter.format_table_caption(2, "Сравнение конкурентов")

        assert caption == "Таблица 2 – Сравнение конкурентов"

    def test_format_reference(self):
        """Test formatting reference."""
        formatter = GOSTFormatter()

        ref1 = formatter.format_reference(5)
        assert ref1 == "[5]"

        ref2 = formatter.format_reference(10, 25)
        assert ref2 == "[10, с. 25]"

    def test_validate_structure_valid(self):
        """Test structure validation with valid structure."""
        formatter = GOSTFormatter()
        sections = [
            "ТИТУЛЬНЫЙ ЛИСТ",
            "РЕФЕРАТ",
            "СОДЕРЖАНИЕ",
            "ВВЕДЕНИЕ",
            "1 ОСНОВНАЯ ЧАСТЬ",
            "ЗАКЛЮЧЕНИЕ",
            "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        ]

        assert formatter.validate_structure(sections) is True

    def test_validate_structure_invalid(self):
        """Test structure validation with invalid structure."""
        formatter = GOSTFormatter()
        sections = [
            "ТИТУЛЬНЫЙ ЛИСТ",
            "РЕФЕРАТ",
        ]

        assert formatter.validate_structure(sections) is False

    def test_format_bibliography_entry_website(self):
        """Test formatting bibliography entry for website."""
        formatter = GOSTFormatter()
        entry = formatter.format_bibliography_entry(
            entry_type="website",
            authors=[],
            title="Росстат: Статистика по регионам",
            year=2024,
            url="https://rosstat.gov.ru",
            access_date="01.01.2024"
        )

        assert "Росстат" in entry
        assert "https://rosstat.gov.ru" in entry
        assert "01.01.2024" in entry


class TestVisualizationService:
    """Tests for visualization service."""

    def test_create_bar_chart(self):
        """Test creating bar chart."""
        service = VisualizationService()
        data = {"Product A": 100, "Product B": 200, "Product C": 150}

        image_bytes = service.create_bar_chart(
            data=data,
            title="Product Sales",
            xlabel="Products",
            ylabel="Sales"
        )

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_create_pie_chart(self):
        """Test creating pie chart."""
        service = VisualizationService()
        data = {"Category A": 30, "Category B": 40, "Category C": 30}

        image_bytes = service.create_pie_chart(
            data=data,
            title="Market Share"
        )

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_create_swot_diagram(self):
        """Test creating SWOT diagram."""
        service = VisualizationService()

        image_bytes = service.create_swot_diagram(
            strengths=["Strong brand", "High quality"],
            weaknesses=["High price", "Limited distribution"],
            opportunities=["Market growth", "New technologies"],
            threats=["New competitors", "Economic downturn"],
            title="SWOT Analysis"
        )

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_figure_counter(self):
        """Test figure counter increment."""
        service = VisualizationService()

        assert service.figure_counter == 0
        assert service.increment_figure_counter() == 1
        assert service.increment_figure_counter() == 2

        service.reset_counters()
        assert service.figure_counter == 0


class TestContentGenerator:
    """Tests for content generator."""

    @pytest.mark.asyncio
    async def test_generate_title_page(self):
        """Test generating title page."""
        db = Mock()
        generator = ContentGenerator(db)

        research = Mock(spec=Research)
        research.title = "Анализ рынка продуктов питания"
        research.product_description = "Органические продукты питания"
        research.industry = "Пищевая промышленность"
        research.region = "Москва"

        title_page = await generator.generate_title_page(research)

        assert title_page["title"] == research.title
        assert title_page["industry"] == research.industry
        assert title_page["region"] == research.region
        assert "organization" in title_page
        assert "date" in title_page

    @pytest.mark.asyncio
    async def test_generate_abstract(self):
        """Test generating abstract."""
        db = Mock()
        generator = ContentGenerator(db)

        research = Mock(spec=Research)
        research.product_description = "Органические продукты питания"
        research.industry = "Пищевая промышленность"
        research.region = "Москва"

        with patch.object(generator.llm_service, 'generate_text', return_value="Test summary"):
            abstract = await generator.generate_abstract(research, [])

            assert "keywords" in abstract
            assert "summary" in abstract
            assert "statistics" in abstract
            assert isinstance(abstract["keywords"], list)

    @pytest.mark.asyncio
    async def test_generate_bibliography(self):
        """Test generating bibliography."""
        db = Mock()
        generator = ContentGenerator(db)

        collected_data = [
            Mock(
                source_url="https://example.com/1",
                title="Source 1",
                collected_at=datetime.now()
            ),
            Mock(
                source_url="https://example.com/2",
                title="Source 2",
                collected_at=datetime.now()
            ),
        ]

        bibliography = await generator.generate_bibliography(collected_data, [])

        assert len(bibliography) == 2
        assert bibliography[0]["url"] == "https://example.com/1"
        assert bibliography[1]["url"] == "https://example.com/2"


class TestDOCXExporter:
    """Tests for DOCX exporter."""

    def test_create_document_basic(self):
        """Test creating basic DOCX document."""
        exporter = DOCXExporter()

        report_data = {
            "title_page": {
                "organization": "Test Org",
                "report_type": "Test Report",
                "title": "Test Title",
                "date": "01.01.2024",
            },
            "abstract": {
                "statistics": {"pages": 10, "figures": 5, "tables": 3, "sources": 15, "appendices": 0},
                "keywords": ["test", "report"],
                "summary": "Test summary",
            },
            "sections": [],
            "introduction": {"text": "Test introduction"},
            "main_sections": [],
            "conclusion": {"text": "Test conclusion"},
            "bibliography": [],
            "appendices": [],
        }

        docx_bytes = exporter.create_document(report_data)

        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0


class TestPDFExporter:
    """Tests for PDF exporter."""

    def test_create_document_basic(self):
        """Test creating basic PDF document."""
        exporter = PDFExporter()

        report_data = {
            "title_page": {
                "organization": "Test Org",
                "report_type": "Test Report",
                "title": "Test Title",
                "date": "01.01.2024",
            },
            "abstract": {
                "statistics": {"pages": 10, "figures": 5, "tables": 3, "sources": 15, "appendices": 0},
                "keywords": ["test", "report"],
                "summary": "Test summary",
            },
            "sections": [],
            "introduction": {"text": "Test introduction"},
            "main_sections": [],
            "conclusion": {"text": "Test conclusion"},
            "bibliography": [],
            "appendices": [],
        }

        pdf_bytes = exporter.create_document(report_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF files start with %PDF
        assert pdf_bytes.startswith(b'%PDF')


class TestReportGenerator:
    """Tests for report generator."""

    @pytest.mark.asyncio
    async def test_generate_report_preview(self):
        """Test generating report preview."""
        db = Mock()
        generator = ReportGenerator(db)

        research = Mock(spec=Research)
        research.title = "Test Research"
        research.industry = "Test Industry"
        research.region = "Test Region"

        preview = await generator.generate_report_preview(research)

        assert preview["title"] == research.title
        assert preview["industry"] == research.industry
        assert preview["region"] == research.region
        assert "sections" in preview
        assert "estimated_pages" in preview

    def test_estimate_page_count(self):
        """Test estimating page count."""
        db = Mock()
        generator = ReportGenerator(db)

        sections = [
            {
                "content": " ".join(["word"] * 1000),  # ~1000 words = 2 pages
                "subsections": [],
                "figures": [],
                "tables": [],
            },
            {
                "content": " ".join(["word"] * 500),  # ~500 words = 1 page
                "subsections": [],
                "figures": [{"title": "Fig 1"}] * 4,  # 4 figures = 2 pages
                "tables": [],
            },
        ]

        page_count = generator._estimate_page_count(sections)

        # Should be at least 10 pages (minimum)
        assert page_count >= 10

"""Main report generator orchestrator."""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models.research import Research
from app.models.report import Report, ReportFormat, ReportStatus
from app.models.analysis_result import AnalysisResult
from app.models.competitor import Competitor
from app.models.collected_data import CollectedData
from app.models.source_verification import SourceVerification

from .content_generator import ContentGenerator
from .visualization import VisualizationService
from .gost_formatter import GOSTFormatter
from .docx_exporter import DOCXExporter
from .pdf_exporter import PDFExporter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Main report generator orchestrator.

    Coordinates all report generation components to create complete
    marketing research reports according to GOST 7.32-2017.
    """

    def __init__(self, db: Session):
        self.db = db
        self.content_generator = ContentGenerator(db)
        self.visualization_service = VisualizationService()
        self.formatter = GOSTFormatter()
        self.docx_exporter = DOCXExporter()
        self.pdf_exporter = PDFExporter()

    async def generate_report(
        self,
        research: Research,
        format: ReportFormat = ReportFormat.PDF
    ) -> Report:
        """
        Generate complete report for research.

        Args:
            research: Research instance
            format: Report format (PDF or DOCX)

        Returns:
            Generated Report instance
        """
        try:
            logger.info(f"Starting report generation for research {research.id}")

            # Create report record
            report = Report(
                research_id=research.id,
                title=research.title,
                format=format,
                status=ReportStatus.GENERATING
            )
            self.db.add(report)
            self.db.commit()

            # Collect data from database
            analysis_results = self.db.query(AnalysisResult).filter(
                AnalysisResult.research_id == research.id
            ).all()

            competitors = self.db.query(Competitor).filter(
                Competitor.research_id == research.id
            ).all()

            collected_data = self.db.query(CollectedData).filter(
                CollectedData.research_id == research.id
            ).all()

            source_verifications = self.db.query(SourceVerification).join(
                CollectedData
            ).filter(
                CollectedData.research_id == research.id
            ).all()

            # Generate report content
            logger.info("Generating report content...")
            report_data = await self._generate_report_content(
                research,
                analysis_results,
                competitors,
                collected_data,
                source_verifications
            )

            # Export to requested format
            logger.info(f"Exporting report to {format} format...")
            if format == ReportFormat.PDF:
                file_bytes = self.pdf_exporter.create_document(report_data)
                file_extension = "pdf"
            elif format == ReportFormat.DOCX:
                file_bytes = self.docx_exporter.create_document(report_data)
                file_extension = "docx"
            else:
                raise ValueError(f"Unsupported format: {format}")

            # Save file
            file_path = await self._save_report_file(
                research.id,
                report.id,
                file_bytes,
                file_extension
            )

            # Update report record
            report.content = report_data
            report.file_path = str(file_path)
            report.file_size = len(file_bytes)
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Report generated successfully: {report.id}")
            return report

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)

            if report:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                self.db.commit()

            raise

    async def _generate_report_content(
        self,
        research: Research,
        analysis_results: list,
        competitors: list,
        collected_data: list,
        source_verifications: list
    ) -> Dict[str, Any]:
        """Generate complete report content."""
        logger.info("Generating title page...")
        title_page = await self.content_generator.generate_title_page(research)

        logger.info("Generating abstract...")
        abstract = await self.content_generator.generate_abstract(
            research,
            analysis_results
        )

        logger.info("Generating introduction...")
        introduction = await self.content_generator.generate_introduction(
            research,
            analysis_results
        )

        logger.info("Generating main sections...")
        main_sections = await self._generate_main_sections(
            research,
            analysis_results,
            competitors,
            collected_data
        )

        logger.info("Generating conclusion...")
        conclusion = await self.content_generator.generate_conclusion(
            research,
            {
                "title_page": title_page,
                "introduction": introduction,
                "main_sections": main_sections,
            }
        )

        logger.info("Generating bibliography...")
        bibliography = await self.content_generator.generate_bibliography(
            collected_data,
            source_verifications
        )

        # Update abstract statistics
        abstract["statistics"] = {
            "pages": self._estimate_page_count(main_sections),
            "figures": self.visualization_service.figure_counter,
            "tables": self.visualization_service.table_counter,
            "sources": len(bibliography),
            "appendices": 0,
        }

        return {
            "title_page": title_page,
            "abstract": abstract,
            "sections": [s["title"] for s in main_sections],
            "introduction": introduction,
            "main_sections": main_sections,
            "conclusion": conclusion,
            "bibliography": bibliography,
            "appendices": [],
        }

    async def _generate_main_sections(
        self,
        research: Research,
        analysis_results: list,
        competitors: list,
        collected_data: list
    ) -> list:
        """Generate all main sections of the report."""
        sections = []

        # Section 1: Industry Analysis
        logger.info("Generating industry analysis section...")
        industry_analysis = await self.content_generator.generate_industry_analysis(
            research,
            collected_data
        )
        sections.append({
            "id": "industry",
            "title": "Анализ отрасли",
            "content": industry_analysis["text"],
            "subsections": [],
        })

        # Section 2: Regional Analysis
        logger.info("Generating regional analysis section...")
        regional_analysis = await self.content_generator.generate_regional_analysis(
            research,
            analysis_results
        )
        sections.append({
            "id": "regional",
            "title": "Региональный анализ",
            "content": regional_analysis["text"],
            "subsections": [],
        })

        # Section 3: Competitor Analysis
        logger.info("Generating competitor analysis section...")
        competitor_analysis = await self.content_generator.generate_competitor_analysis(
            research,
            competitors
        )

        # Add SWOT visualization if we have competitors
        figures = []
        if competitors:
            # Create SWOT diagram for top competitor
            top_competitor = competitors[0]
            if top_competitor.strengths and top_competitor.weaknesses:
                try:
                    swot_image = self.visualization_service.create_swot_diagram(
                        strengths=top_competitor.strengths or [],
                        weaknesses=top_competitor.weaknesses or [],
                        opportunities=top_competitor.opportunities or [],
                        threats=top_competitor.threats or [],
                        title=f"SWOT-анализ: {top_competitor.name}"
                    )
                    figures.append({
                        "title": f"SWOT-анализ конкурента {top_competitor.name}",
                        "image_bytes": swot_image,
                    })
                except Exception as e:
                    logger.warning(f"Failed to create SWOT diagram: {e}")

        sections.append({
            "id": "competitors",
            "title": "Конкурентный анализ",
            "content": competitor_analysis["text"],
            "subsections": [],
            "figures": figures,
        })

        # Section 4: Trend Analysis
        logger.info("Generating trend analysis section...")
        trend_analysis = await self.content_generator.generate_trend_analysis(
            research,
            analysis_results
        )
        sections.append({
            "id": "trends",
            "title": "Анализ смежных отраслей и трендов",
            "content": trend_analysis["text"],
            "subsections": [],
        })

        return sections

    async def _save_report_file(
        self,
        research_id: str,
        report_id: str,
        file_bytes: bytes,
        extension: str
    ) -> Path:
        """Save report file to disk."""
        # Create reports directory if it doesn't exist
        reports_dir = Path("./reports")
        reports_dir.mkdir(exist_ok=True)

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{research_id}_{report_id}_{timestamp}.{extension}"
        file_path = reports_dir / filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Report file saved to {file_path}")
        return file_path

    def _estimate_page_count(self, sections: list) -> int:
        """Estimate total page count."""
        # Simple estimation: ~500 words per page
        total_words = 0

        for section in sections:
            content = section.get("content", "")
            total_words += len(content.split())

            for subsection in section.get("subsections", []):
                subcontent = subsection.get("content", "")
                total_words += len(subcontent.split())

        # Add pages for figures and tables
        total_figures = sum(
            len(section.get("figures", [])) +
            sum(len(sub.get("figures", [])) for sub in section.get("subsections", []))
            for section in sections
        )

        total_tables = sum(
            len(section.get("tables", [])) +
            sum(len(sub.get("tables", [])) for sub in section.get("subsections", []))
            for section in sections
        )

        # Estimate: 500 words/page + 1 page per 2 figures/tables + fixed pages (title, abstract, etc.)
        estimated_pages = (total_words // 500) + (total_figures + total_tables) // 2 + 10

        return max(estimated_pages, 10)  # Minimum 10 pages

    async def generate_report_preview(
        self,
        research: Research
    ) -> Dict[str, Any]:
        """
        Generate report preview (structure only, no full content).

        Args:
            research: Research instance

        Returns:
            Dictionary with report preview data
        """
        title_page = await self.content_generator.generate_title_page(research)

        return {
            "title": research.title,
            "organization": title_page["organization"],
            "industry": research.industry,
            "region": research.region,
            "date": title_page["date"],
            "sections": [
                "Анализ отрасли",
                "Региональный анализ",
                "Конкурентный анализ",
                "Анализ смежных отраслей и трендов",
            ],
            "estimated_pages": 20,
        }

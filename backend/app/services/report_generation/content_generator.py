"""Report content generation service."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.research import Research
from app.models.analysis_result import AnalysisResult
from app.models.competitor import Competitor
from app.models.collected_data import CollectedData
from app.models.source_verification import SourceVerification
from app.services.llm_service import LLMService


class ContentGenerator:
    """
    Content generator for marketing research reports.

    Generates all sections of the report based on research data.
    """

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def generate_title_page(self, research: Research) -> Dict[str, Any]:
        """
        Generate title page content.

        Args:
            research: Research instance

        Returns:
            Dictionary with title page data
        """
        return {
            "organization": "Искусанный Интеллектом Маркетолух",
            "report_type": "Маркетинговое исследование",
            "title": research.title,
            "product_description": research.product_description,
            "industry": research.industry,
            "region": research.region,
            "date": datetime.now().strftime("%d.%m.%Y"),
            "year": datetime.now().year,
        }

    async def generate_abstract(
        self,
        research: Research,
        analysis_results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate abstract (реферат) section.

        Args:
            research: Research instance
            analysis_results: List of analysis results

        Returns:
            Dictionary with abstract data
        """
        # Collect statistics
        stats = await self._collect_report_statistics(research)

        # Generate keywords
        keywords = await self._generate_keywords(research, analysis_results)

        # Generate summary text
        summary = await self._generate_summary(research, analysis_results)

        return {
            "statistics": stats,
            "keywords": keywords,
            "summary": summary,
        }

    async def generate_introduction(
        self,
        research: Research,
        analysis_results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate introduction section.

        Args:
            research: Research instance
            analysis_results: List of analysis results

        Returns:
            Dictionary with introduction data
        """
        prompt = f"""
Создай введение для маркетингового исследования на основе следующих данных:

Продукт/Услуга: {research.product_description}
Отрасль: {research.industry}
Регион: {research.region}

Введение должно содержать:
1. Описание продукта/услуги и его особенностей
2. Цель исследования
3. Регион и временные рамки исследования
4. Краткое описание методологии

Объем: 1-2 страницы.
"""

        introduction_text = await self.llm_service.generate_text(prompt)

        return {
            "text": introduction_text,
            "product_description": research.product_description,
            "industry": research.industry,
            "region": research.region,
            "research_goal": f"Анализ рыночных возможностей для запуска продукта в регионе {research.region}",
            "methodology": "Исследование проведено с использованием ИИ-агента с применением методов анализа открытых данных, конкурентного анализа и трендового анализа.",
        }

    async def generate_industry_analysis(
        self,
        research: Research,
        collected_data: List[CollectedData]
    ) -> Dict[str, Any]:
        """
        Generate industry analysis section.

        Args:
            research: Research instance
            collected_data: List of collected data

        Returns:
            Dictionary with industry analysis data
        """
        # Filter industry-related data
        industry_data = [
            d for d in collected_data
            if d.data_type in ["market_statistics", "industry_report", "regulatory_info"]
        ]

        prompt = f"""
Создай анализ отрасли на основе собранных данных:

Отрасль: {research.industry}
Регион: {research.region}

Количество источников: {len(industry_data)}

Раздел должен содержать:
1. Общая характеристика рынка
2. Объем и динамика рынка
3. Ключевые тренды
4. Нормативно-правовое регулирование

Объем: 2-3 страницы.
"""

        analysis_text = await self.llm_service.generate_text(prompt)

        return {
            "text": analysis_text,
            "market_size": None,  # To be filled with actual data
            "market_growth": None,  # To be filled with actual data
            "key_trends": [],  # To be filled with actual data
            "regulations": [],  # To be filled with actual data
            "data_sources": [d.source_url for d in industry_data if d.source_url],
        }

    async def generate_regional_analysis(
        self,
        research: Research,
        analysis_results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate regional analysis section.

        Args:
            research: Research instance
            analysis_results: List of analysis results

        Returns:
            Dictionary with regional analysis data
        """
        # Filter regional analysis results
        regional_results = [
            r for r in analysis_results
            if r.analysis_type == "regional"
        ]

        prompt = f"""
Создай региональный анализ на основе данных:

Регион: {research.region}
Продукт/Услуга: {research.product_description}

Раздел должен содержать:
1. Демографические характеристики региона
2. Экономические показатели региона
3. Особенности потребительского поведения
4. Конкурентная среда в регионе

Объем: 2-3 страницы.
"""

        analysis_text = await self.llm_service.generate_text(prompt)

        return {
            "text": analysis_text,
            "demographics": {},  # To be filled with actual data
            "economics": {},  # To be filled with actual data
            "consumer_behavior": {},  # To be filled with actual data
            "data_sources": [],
        }

    async def generate_competitor_analysis(
        self,
        research: Research,
        competitors: List[Competitor]
    ) -> Dict[str, Any]:
        """
        Generate competitor analysis section.

        Args:
            research: Research instance
            competitors: List of competitors

        Returns:
            Dictionary with competitor analysis data
        """
        competitors_info = "\n".join([
            f"- {c.name}: {c.description}" for c in competitors[:10]
        ])

        prompt = f"""
Создай конкурентный анализ на основе данных:

Количество конкурентов: {len(competitors)}
Основные конкуренты:
{competitors_info}

Раздел должен содержать:
1. Идентификация ключевых конкурентов
2. SWOT-анализ основных конкурентов
3. Анализ позиционирования
4. Ценовой анализ

Объем: 3-4 страницы.
"""

        analysis_text = await self.llm_service.generate_text(prompt)

        return {
            "text": analysis_text,
            "competitors": [
                {
                    "name": c.name,
                    "description": c.description,
                    "strengths": c.strengths,
                    "weaknesses": c.weaknesses,
                    "market_share": c.market_share,
                }
                for c in competitors
            ],
            "swot_analysis": {},  # To be filled with structured data
        }

    async def generate_trend_analysis(
        self,
        research: Research,
        analysis_results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate trend analysis section.

        Args:
            research: Research instance
            analysis_results: List of analysis results

        Returns:
            Dictionary with trend analysis data
        """
        # Filter trend analysis results
        trend_results = [
            r for r in analysis_results
            if r.analysis_type == "trend"
        ]

        prompt = f"""
Создай анализ трендов на основе данных:

Отрасль: {research.industry}

Раздел должен содержать:
1. Смежные отрасли и их влияние
2. Технологические тренды
3. Социальные и культурные тренды
4. Прогноз развития рынка

Объем: 2-3 страницы.
"""

        analysis_text = await self.llm_service.generate_text(prompt)

        return {
            "text": analysis_text,
            "trends": [],  # To be filled with actual trends
            "forecast": "",  # To be filled with forecast
        }

    async def generate_conclusion(
        self,
        research: Research,
        all_sections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate conclusion section.

        Args:
            research: Research instance
            all_sections: Dictionary with all generated sections

        Returns:
            Dictionary with conclusion data
        """
        prompt = f"""
Создай заключение для маркетингового исследования на основе всех разделов отчета.

Продукт/Услуга: {research.product_description}
Отрасль: {research.industry}
Регион: {research.region}

Заключение должно содержать:
1. Основные выводы исследования
2. Оценку рыночных возможностей
3. Риски и барьеры
4. Рекомендации по запуску продукта

Объем: 1-2 страницы.
"""

        conclusion_text = await self.llm_service.generate_text(prompt)

        return {
            "text": conclusion_text,
            "key_findings": [],  # To be extracted from text
            "opportunities": [],
            "risks": [],
            "recommendations": [],
        }

    async def generate_bibliography(
        self,
        collected_data: List[CollectedData],
        source_verifications: List[SourceVerification]
    ) -> List[Dict[str, Any]]:
        """
        Generate bibliography section.

        Args:
            collected_data: List of collected data
            source_verifications: List of source verifications

        Returns:
            List of bibliography entries
        """
        # Collect unique sources
        sources = {}
        for data in collected_data:
            if data.source_url and data.source_url not in sources:
                # Find verification for this source
                verification = next(
                    (v for v in source_verifications if v.source_url == data.source_url),
                    None
                )

                sources[data.source_url] = {
                    "url": data.source_url,
                    "title": data.title or "Без названия",
                    "access_date": data.collected_at.strftime("%d.%m.%Y"),
                    "reliability_score": verification.reliability_score if verification else None,
                    "is_verified": verification.is_verified if verification else False,
                }

        # Convert to list and sort by title
        bibliography = list(sources.values())
        bibliography.sort(key=lambda x: x["title"])

        return bibliography

    async def _collect_report_statistics(self, research: Research) -> Dict[str, int]:
        """Collect report statistics for abstract."""
        # This will be calculated during report generation
        return {
            "pages": 0,  # To be filled
            "figures": 0,  # To be filled
            "tables": 0,  # To be filled
            "sources": 0,  # To be filled
            "appendices": 0,  # To be filled
        }

    async def _generate_keywords(
        self,
        research: Research,
        analysis_results: List[AnalysisResult]
    ) -> List[str]:
        """Generate keywords for abstract."""
        keywords = [
            research.industry.lower(),
            research.region.lower(),
            "маркетинговое исследование",
            "конкурентный анализ",
            "рыночный анализ",
        ]

        # Add product-specific keywords
        product_words = research.product_description.lower().split()[:3]
        keywords.extend(product_words)

        # Remove duplicates and limit to 15
        keywords = list(dict.fromkeys(keywords))[:15]

        return keywords

    async def _generate_summary(
        self,
        research: Research,
        analysis_results: List[AnalysisResult]
    ) -> str:
        """Generate summary text for abstract."""
        prompt = f"""
Создай краткое резюме (не более 500 слов) для маркетингового исследования:

Продукт/Услуга: {research.product_description}
Отрасль: {research.industry}
Регион: {research.region}

Резюме должно кратко описать цель исследования, основные выводы и рекомендации.
"""

        summary = await self.llm_service.generate_text(prompt)
        return summary

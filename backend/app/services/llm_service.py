"""LLM Service for market analysis."""

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from app.core.config import settings


class LLMService:
    """Service for LLM-based analysis."""

    def __init__(self):
        """Initialize LLM service."""
        self.provider = settings.default_llm_provider

        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4",
                temperature=0.7,
            )
        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.llm = ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-opus-20240229",
                temperature=0.7,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def analyze_market(
        self,
        product_description: str,
        industry: str,
        region: str,
    ) -> str:
        """Analyze market for the given product."""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Ты - профессиональный маркетинговый аналитик.
            Твоя задача - провести анализ рынка для нового продукта.
            Предоставь структурированный анализ, включающий:
            1. Обзор рынка
            2. Целевая аудитория
            3. Конкуренты
            4. Возможности и угрозы
            5. Рекомендации

            Ответ должен быть на русском языке, профессиональным и основанным на логических предпосылках."""),
            ("human", """Продукт: {product_description}
            Отрасль: {industry}
            Регион: {region}

            Проведи комплексный маркетинговый анализ."""),
        ])

        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        try:
            result = await chain.ainvoke({
                "product_description": product_description,
                "industry": industry,
                "region": region,
            })
            return result["text"]
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}")

    async def analyze_market_with_data(
        self,
        product_description: str,
        industry: str,
        region: str,
        collected_data: str,
    ) -> str:
        """
        Analyze market using real collected data.

        Args:
            product_description: Product description
            industry: Industry sector
            region: Region
            collected_data: Formatted collected data from multiple sources

        Returns:
            Market analysis based on real data
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Ты - профессиональный маркетинговый аналитик.
            Твоя задача - провести анализ рынка для нового продукта на основе РЕАЛЬНЫХ данных.

            ВАЖНО: Используй ТОЛЬКО предоставленные данные для анализа. Не придумывай факты.
            Если данных недостаточно, укажи это в анализе.

            Предоставь структурированный анализ, включающий:
            1. Обзор рынка (на основе собранных данных)
            2. Целевая аудитория (на основе рыночных трендов)
            3. Конкуренты (на основе найденной информации о конкурентах)
            4. Возможности и угрозы (на основе новостей и трендов)
            5. Рекомендации (на основе проанализированных данных)

            Указывай источники данных в анализе, где это уместно.
            Ответ должен быть на русском языке, профессиональным и основанным на фактах."""),
            ("human", """Продукт: {product_description}
            Отрасль: {industry}
            Регион: {region}

            Собранные данные из реальных источников:
            {collected_data}

            Проведи комплексный маркетинговый анализ на основе этих данных."""),
        ])

        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        try:
            result = await chain.ainvoke({
                "product_description": product_description,
                "industry": industry,
                "region": region,
                "collected_data": collected_data,
            })
            return result["text"]
        except Exception as e:
            raise Exception(f"LLM analysis with data failed: {str(e)}")

    async def generate_report_section(
        self,
        section_type: str,
        data: dict,
    ) -> str:
        """Generate a specific section of the report."""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", f"""Ты - эксперт по составлению маркетинговых отчетов по ГОСТ 7.32-2017.
            Создай раздел отчета типа: {section_type}.
            Текст должен быть структурированным, профессиональным и соответствовать стандарту."""),
            ("human", "Данные для раздела: {data}"),
        ])

        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        try:
            result = await chain.ainvoke({"data": str(data)})
            return result["text"]
        except Exception as e:
            raise Exception(f"Report generation failed: {str(e)}")

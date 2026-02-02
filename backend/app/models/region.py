"""Region model for Russian Federation."""

from sqlalchemy import Column, String, Text, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Region(Base):
    """Russian Federation region model."""

    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)  # OKATO or OKTMO code
    federal_district = Column(String, nullable=False)  # Federal district

    # Geographic data
    area_km2 = Column(Float, nullable=True)
    capital = Column(String, nullable=True)

    # Demographic data
    population = Column(Integer, nullable=True)
    population_density = Column(Float, nullable=True)
    urban_population_percent = Column(Float, nullable=True)

    # Economic indicators
    gdp = Column(Float, nullable=True)  # Regional GDP
    gdp_per_capita = Column(Float, nullable=True)
    unemployment_rate = Column(Float, nullable=True)
    average_income = Column(Float, nullable=True)

    # Business environment
    business_activity_index = Column(Float, nullable=True)  # Custom metric
    number_of_businesses = Column(Integer, nullable=True)
    investment_attractiveness = Column(Float, nullable=True)  # Rating 0-10

    # Additional data
    key_industries = Column(JSON, nullable=True)  # List of key industries
    regional_features = Column(Text, nullable=True)  # Special characteristics
    extra_metadata = Column(JSON, nullable=True)  # Additional structured data

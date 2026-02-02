"""GOST 7.32-2017 formatting rules and utilities."""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class GOSTPageSettings:
    """GOST page settings."""
    # Page format
    page_width_mm: float = 210  # A4 width
    page_height_mm: float = 297  # A4 height

    # Margins (in mm)
    left_margin: int = 30
    right_margin: int = 15
    top_margin: int = 20
    bottom_margin: int = 20

    # Text formatting
    font_name: str = "Times New Roman"
    font_size: int = 14
    line_spacing: float = 1.5
    text_align: str = "justify"


@dataclass
class GOSTNumberingRules:
    """GOST numbering rules."""
    # Page numbering
    page_number_position: str = "bottom_center"
    page_number_format: str = "arabic"
    start_page_number: int = 1

    # Section numbering
    section_number_format: str = "{number}"
    subsection_number_format: str = "{section}.{number}"
    subsubsection_number_format: str = "{section}.{subsection}.{number}"

    # Figure and table numbering
    figure_number_format: str = "Рисунок {number} – {title}"
    table_number_format: str = "Таблица {number} – {title}"
    formula_number_format: str = "({section}.{number})"


class GOSTFormatter:
    """
    GOST 7.32-2017 formatter.

    Handles all formatting rules according to GOST 7.32-2017 standard.
    """

    def __init__(self):
        self.page_settings = GOSTPageSettings()
        self.numbering_rules = GOSTNumberingRules()

    def format_heading(self, text: str, level: int) -> Dict[str, Any]:
        """
        Format heading according to GOST rules.

        Args:
            text: Heading text
            level: Heading level (0=structural element, 1=section, 2=subsection, 3=subsubsection)

        Returns:
            Dictionary with formatting parameters
        """
        if level == 0:
            # Structural elements (РЕФЕРАТ, СОДЕРЖАНИЕ, etc.)
            return {
                "text": text.upper(),
                "bold": True,
                "alignment": "center",
                "font_size": self.page_settings.font_size,
                "spacing_before": 0,
                "spacing_after": 12,
                "keep_with_next": True,
                "page_break_before": True,
            }
        elif level == 1:
            # Sections
            return {
                "text": text.upper(),
                "bold": True,
                "alignment": "left",
                "font_size": self.page_settings.font_size,
                "spacing_before": 12,
                "spacing_after": 12,
                "keep_with_next": True,
            }
        elif level == 2:
            # Subsections
            return {
                "text": text.capitalize() if not text[0].isupper() else text,
                "bold": True,
                "alignment": "left",
                "font_size": self.page_settings.font_size,
                "spacing_before": 12,
                "spacing_after": 6,
                "keep_with_next": True,
            }
        else:
            # Subsubsections
            return {
                "text": text.capitalize() if not text[0].isupper() else text,
                "bold": False,
                "alignment": "left",
                "font_size": self.page_settings.font_size,
                "spacing_before": 6,
                "spacing_after": 6,
                "keep_with_next": True,
            }

    def format_paragraph(self, text: str) -> Dict[str, Any]:
        """
        Format paragraph according to GOST rules.

        Args:
            text: Paragraph text

        Returns:
            Dictionary with formatting parameters
        """
        return {
            "text": text,
            "alignment": self.page_settings.text_align,
            "font_size": self.page_settings.font_size,
            "line_spacing": self.page_settings.line_spacing,
            "first_line_indent": 12.5,  # 1.25 cm indent
        }

    def format_figure_caption(self, number: int, title: str) -> str:
        """
        Format figure caption according to GOST rules.

        Args:
            number: Figure number
            title: Figure title

        Returns:
            Formatted caption
        """
        return self.numbering_rules.figure_number_format.format(
            number=number,
            title=title
        )

    def format_table_caption(self, number: int, title: str) -> str:
        """
        Format table caption according to GOST rules.

        Args:
            number: Table number
            title: Table title

        Returns:
            Formatted caption
        """
        return self.numbering_rules.table_number_format.format(
            number=number,
            title=title
        )

    def format_formula_number(self, section: int, number: int) -> str:
        """
        Format formula number according to GOST rules.

        Args:
            section: Section number
            number: Formula number within section

        Returns:
            Formatted formula number
        """
        return self.numbering_rules.formula_number_format.format(
            section=section,
            number=number
        )

    def format_reference(self, number: int, page: int = None) -> str:
        """
        Format reference citation according to GOST rules.

        Args:
            number: Reference number
            page: Page number (optional)

        Returns:
            Formatted reference citation
        """
        if page:
            return f"[{number}, с. {page}]"
        return f"[{number}]"

    def format_list_item(self, text: str, marker: str = "–") -> Dict[str, Any]:
        """
        Format list item according to GOST rules.

        Args:
            text: List item text
            marker: List marker (default: em dash)

        Returns:
            Dictionary with formatting parameters
        """
        return {
            "text": text,
            "marker": marker,
            "alignment": self.page_settings.text_align,
            "font_size": self.page_settings.font_size,
            "line_spacing": self.page_settings.line_spacing,
            "left_indent": 12.5,
        }

    def get_structural_elements_order(self) -> List[str]:
        """
        Get the order of structural elements according to GOST.

        Returns:
            List of structural element names in order
        """
        return [
            "ТИТУЛЬНЫЙ ЛИСТ",
            "РЕФЕРАТ",
            "СОДЕРЖАНИЕ",
            "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
            "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
            "ВВЕДЕНИЕ",
            "ОСНОВНАЯ ЧАСТЬ",
            "ЗАКЛЮЧЕНИЕ",
            "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
            "ПРИЛОЖЕНИЯ",
        ]

    def validate_structure(self, sections: List[str]) -> bool:
        """
        Validate report structure according to GOST.

        Args:
            sections: List of section names in the report

        Returns:
            True if structure is valid, False otherwise
        """
        required_sections = {
            "ТИТУЛЬНЫЙ ЛИСТ",
            "РЕФЕРАТ",
            "СОДЕРЖАНИЕ",
            "ВВЕДЕНИЕ",
            "ЗАКЛЮЧЕНИЕ",
            "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        }

        # Check if all required sections are present
        sections_set = set(sections)
        return required_sections.issubset(sections_set)

    def format_bibliography_entry(
        self,
        entry_type: str,
        authors: List[str],
        title: str,
        year: int,
        **kwargs
    ) -> str:
        """
        Format bibliography entry according to GOST 7.1.

        Args:
            entry_type: Type of entry (book, article, website, etc.)
            authors: List of authors
            title: Title of the work
            year: Publication year
            **kwargs: Additional parameters depending on entry type

        Returns:
            Formatted bibliography entry
        """
        if entry_type == "book":
            authors_str = ", ".join(authors[:3])
            if len(authors) > 3:
                authors_str += " и др."

            publisher = kwargs.get("publisher", "")
            pages = kwargs.get("pages", "")

            entry = f"{authors_str} {title}. – {publisher}, {year}."
            if pages:
                entry += f" – {pages} с."
            return entry

        elif entry_type == "article":
            authors_str = ", ".join(authors[:3])
            if len(authors) > 3:
                authors_str += " и др."

            journal = kwargs.get("journal", "")
            volume = kwargs.get("volume", "")
            number = kwargs.get("number", "")
            pages = kwargs.get("pages", "")

            entry = f"{authors_str} {title} // {journal}. – {year}."
            if volume:
                entry += f" – Т. {volume}."
            if number:
                entry += f" – № {number}."
            if pages:
                entry += f" – С. {pages}."
            return entry

        elif entry_type == "website":
            url = kwargs.get("url", "")
            access_date = kwargs.get("access_date", "")

            entry = f"{title}. – URL: {url}"
            if access_date:
                entry += f" (дата обращения: {access_date})"
            return entry

        else:
            # Default format
            authors_str = ", ".join(authors) if authors else ""
            return f"{authors_str} {title}. – {year}."

"""Data visualization service for reports."""

from typing import Dict, Any, List, Optional
import io
import base64
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.figure import Figure

# Use non-interactive backend
matplotlib.use('Agg')

# Set Russian font support
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class VisualizationService:
    """
    Service for creating data visualizations for reports.

    Generates charts, diagrams, and tables according to GOST standards.
    """

    def __init__(self):
        self.figure_counter = 0
        self.table_counter = 0
        self.default_figsize = (10, 6)
        self.default_dpi = 300

        # Set seaborn style
        sns.set_style("whitegrid")
        sns.set_palette("husl")

    def create_bar_chart(
        self,
        data: Dict[str, float],
        title: str,
        xlabel: str,
        ylabel: str,
        **kwargs
    ) -> bytes:
        """
        Create a bar chart.

        Args:
            data: Dictionary with labels as keys and values as values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            **kwargs: Additional matplotlib parameters

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        labels = list(data.keys())
        values = list(data.values())

        ax.bar(labels, values, **kwargs)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def create_line_chart(
        self,
        data: Dict[str, List[float]],
        x_labels: List[str],
        title: str,
        xlabel: str,
        ylabel: str,
        **kwargs
    ) -> bytes:
        """
        Create a line chart.

        Args:
            data: Dictionary with series names as keys and lists of values
            x_labels: Labels for x-axis
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            **kwargs: Additional matplotlib parameters

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        for series_name, values in data.items():
            ax.plot(x_labels, values, marker='o', label=series_name, **kwargs)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def create_pie_chart(
        self,
        data: Dict[str, float],
        title: str,
        **kwargs
    ) -> bytes:
        """
        Create a pie chart.

        Args:
            data: Dictionary with labels as keys and values as values
            title: Chart title
            **kwargs: Additional matplotlib parameters

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        labels = list(data.keys())
        values = list(data.values())

        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, **kwargs)
        ax.set_title(title)
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def create_swot_diagram(
        self,
        strengths: List[str],
        weaknesses: List[str],
        opportunities: List[str],
        threats: List[str],
        title: str = "SWOT-анализ"
    ) -> bytes:
        """
        Create a SWOT analysis diagram.

        Args:
            strengths: List of strengths
            weaknesses: List of weaknesses
            opportunities: List of opportunities
            threats: List of threats
            title: Diagram title

        Returns:
            Image bytes (PNG format)
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        # Strengths (top-left)
        self._draw_swot_quadrant(
            axes[0, 0],
            "Сильные стороны (Strengths)",
            strengths,
            '#90EE90'  # Light green
        )

        # Weaknesses (top-right)
        self._draw_swot_quadrant(
            axes[0, 1],
            "Слабые стороны (Weaknesses)",
            weaknesses,
            '#FFB6C6'  # Light red
        )

        # Opportunities (bottom-left)
        self._draw_swot_quadrant(
            axes[1, 0],
            "Возможности (Opportunities)",
            opportunities,
            '#87CEEB'  # Light blue
        )

        # Threats (bottom-right)
        self._draw_swot_quadrant(
            axes[1, 1],
            "Угрозы (Threats)",
            threats,
            '#FFD700'  # Light yellow
        )

        plt.tight_layout()
        return self._figure_to_bytes(fig)

    def create_comparison_table(
        self,
        data: pd.DataFrame,
        title: str
    ) -> bytes:
        """
        Create a comparison table visualization.

        Args:
            data: DataFrame with comparison data
            title: Table title

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=(12, len(data) * 0.5 + 2))
        ax.axis('tight')
        ax.axis('off')

        table = ax.table(
            cellText=data.values,
            colLabels=data.columns,
            rowLabels=data.index,
            cellLoc='left',
            loc='center'
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        # Style header
        for i in range(len(data.columns)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def create_heatmap(
        self,
        data: pd.DataFrame,
        title: str,
        **kwargs
    ) -> bytes:
        """
        Create a heatmap.

        Args:
            data: DataFrame with numerical data
            title: Heatmap title
            **kwargs: Additional seaborn parameters

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        sns.heatmap(data, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax, **kwargs)
        ax.set_title(title)
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def create_trend_chart(
        self,
        data: pd.DataFrame,
        title: str,
        xlabel: str = "Период",
        ylabel: str = "Значение"
    ) -> bytes:
        """
        Create a trend chart with moving average.

        Args:
            data: DataFrame with time series data
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        # Plot original data
        for column in data.columns:
            ax.plot(data.index, data[column], marker='o', label=column, alpha=0.7)

            # Add moving average if enough data points
            if len(data) > 3:
                ma = data[column].rolling(window=3).mean()
                ax.plot(data.index, ma, linestyle='--', label=f'{column} (скользящее среднее)')

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def create_scatter_plot(
        self,
        x_data: List[float],
        y_data: List[float],
        labels: Optional[List[str]],
        title: str,
        xlabel: str,
        ylabel: str,
        **kwargs
    ) -> bytes:
        """
        Create a scatter plot.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            labels: Point labels (optional)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            **kwargs: Additional matplotlib parameters

        Returns:
            Image bytes (PNG format)
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)

        ax.scatter(x_data, y_data, **kwargs)

        if labels:
            for i, label in enumerate(labels):
                ax.annotate(label, (x_data[i], y_data[i]),
                          textcoords="offset points", xytext=(5, 5), ha='left')

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return self._figure_to_bytes(fig)

    def _draw_swot_quadrant(
        self,
        ax: plt.Axes,
        title: str,
        items: List[str],
        color: str
    ) -> None:
        """Draw a single SWOT quadrant."""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Background
        rect = plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=0.3)
        ax.add_patch(rect)

        # Title
        ax.text(0.5, 0.95, title, ha='center', va='top',
               fontsize=12, fontweight='bold')

        # Items
        y_pos = 0.85
        for item in items[:5]:  # Limit to 5 items per quadrant
            wrapped_text = self._wrap_text(item, 40)
            ax.text(0.05, y_pos, f"• {wrapped_text}", ha='left', va='top',
                   fontsize=10, wrap=True)
            y_pos -= 0.15

    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return '\n  '.join(lines)

    def _figure_to_bytes(self, fig: Figure) -> bytes:
        """
        Convert matplotlib figure to bytes.

        Args:
            fig: Matplotlib figure

        Returns:
            Image bytes (PNG format)
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=self.default_dpi, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def increment_figure_counter(self) -> int:
        """Increment and return figure counter."""
        self.figure_counter += 1
        return self.figure_counter

    def increment_table_counter(self) -> int:
        """Increment and return table counter."""
        self.table_counter += 1
        return self.table_counter

    def reset_counters(self) -> None:
        """Reset figure and table counters."""
        self.figure_counter = 0
        self.table_counter = 0

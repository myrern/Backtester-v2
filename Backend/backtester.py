import os
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class Backtester:
    """
    Core backtester that handles data loading and visualization.
    Designed for loading market data and displaying charts.
    """

    def __init__(self, symbol: str, bar_size: str, data_folder: str = "data"):
        """
        Initialize backtester with market data parameters.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'MSFT')
            bar_size: Bar size for data (e.g., '1 hour', '1 day')
            data_folder: Folder containing CSV data files
        """
        self.symbol = symbol.upper()
        self.bar_size = bar_size
        self.data_folder = data_folder

        # Core data storage
        self.raw_data: Optional[pd.DataFrame] = None

        # Chart configuration
        self.chart_width = 2500
        self.chart_height = 1200

    def load_data(self) -> bool:
        """
        Load OHLCV data from CSV file and prepare for analysis.

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        csv_filename = os.path.join(
            self.data_folder,
            f'{self.symbol}_{self.bar_size.replace(" ", "_")}.csv',
        )

        try:
            self.raw_data = pd.read_csv(
                csv_filename, index_col="date", parse_dates=True
            )
            self.raw_data.sort_index(inplace=True)  # Ensure chronological order

            # Calculate cumulative returns for buy and hold strategy
            self.raw_data["returns"] = (
                self.raw_data["close"] / self.raw_data["close"].iloc[0]
            ) - 1

            print(f"✓ Loaded {len(self.raw_data)} bars for {self.symbol}")
            print(
                f"  Date range: {self.raw_data.index[0]} to {self.raw_data.index[-1]}"
            )
            print(f"\nDataFrame tail:")
            print(self.raw_data.tail())
            return True

        except FileNotFoundError:
            print(f"❌ CSV file not found: {csv_filename}")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def get_data(self) -> Optional[pd.DataFrame]:
        """
        Get the raw OHLCV data.

        Returns:
            DataFrame with OHLCV data or None if not loaded
        """
        return self.raw_data.copy() if self.raw_data is not None else None

    def display_chart(self) -> None:
        """Display interactive candlestick chart with returns subchart."""
        if self.raw_data is None:
            print("❌ No chart data available. Call load_data() first.")
            return

        # Create subplots with volume chart
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(
                f"{self.symbol} - Price Chart",
                "Volume",
                "Buy & Hold Returns (%)",
            ),
            row_heights=[0.5, 0.25, 0.25],
        )

        # Add candlestick chart with enhanced styling
        fig.add_trace(
            go.Candlestick(
                x=self.raw_data.index,
                open=self.raw_data["open"],
                high=self.raw_data["high"],
                low=self.raw_data["low"],
                close=self.raw_data["close"],
                name="Price",
                increasing=dict(
                    fillcolor="#228B22",  # Solid forest green for up candles
                    line=dict(color="#006400", width=2),  # Darker green border
                ),
                decreasing=dict(
                    fillcolor="#FF3333",  # Bright red for down candles
                    line=dict(color="#CC0000", width=2),  # Darker red border
                ),
            ),
            row=1,
            col=1,
        )

        # Add volume bar chart
        # Create volume colors based on price movement
        volume_colors = []
        for i in range(len(self.raw_data)):
            if self.raw_data.iloc[i]["close"] >= self.raw_data.iloc[i]["open"]:
                volume_colors.append("#228B22")  # Green for up days
            else:
                volume_colors.append("#FF3333")  # Red for down days

        fig.add_trace(
            go.Bar(
                x=self.raw_data.index,
                y=self.raw_data["volume"],
                name="Volume",
                marker_color=volume_colors,
                opacity=1.0,  # Make bars fully opaque
                showlegend=False,
                marker=dict(line=dict(width=0)),  # Remove bar borders for cleaner look
            ),
            row=2,
            col=1,
        )

        # Add returns line chart
        fig.add_trace(
            go.Scatter(
                x=self.raw_data.index,
                y=self.raw_data["returns"] * 100,  # Convert to percentage
                mode="lines",
                name="Returns (%)",
                line=dict(color="blue", width=2),
            ),
            row=3,
            col=1,
        )

        # Update layout
        fig.update_layout(
            title=f"{self.symbol} - Trading Chart",
            width=self.chart_width,
            height=self.chart_height,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            # Improve the overall appearance
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12),
            # Reduce margins to maximize chart space
            margin=dict(l=40, r=40, t=60, b=40),
            autosize=True,
        )

        # Update axes
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Returns (%)", row=3, col=1)
        fig.update_xaxes(title_text="Date", row=3, col=1)

        # Configure x-axes for all subplots to ensure synchronization
        fig.update_xaxes(
            showgrid=True, gridcolor="lightgray", gridwidth=1, row=1, col=1
        )
        fig.update_xaxes(
            showgrid=True, gridcolor="lightgray", gridwidth=1, row=2, col=1
        )
        fig.update_xaxes(
            showgrid=True, gridcolor="lightgray", gridwidth=1, row=3, col=1
        )

        # Show the chart
        fig.show()

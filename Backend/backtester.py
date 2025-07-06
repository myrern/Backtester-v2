import pandas as pd
import os
from typing import Optional
from lightweight_charts import Chart


class Backtester:
    """
    Core backtester that handles data loading and visualization.
    Designed for loading market data and displaying charts.
    """
    
    def __init__(self, symbol: str, duration: str, bar_size: str, data_folder: str = 'data'):
        """
        Initialize backtester with market data parameters.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'MSFT')
            duration: Time duration for data (e.g., '50 D', '1 Y')
            bar_size: Bar size for data (e.g., '1 hour', '1 day')
            data_folder: Folder containing CSV data files
        """
        self.symbol = symbol.upper()
        self.duration = duration
        self.bar_size = bar_size
        self.data_folder = data_folder
        
        # Core data storage
        self.raw_data: Optional[pd.DataFrame] = None
        self.chart_data: Optional[pd.DataFrame] = None
        
        # Chart configuration
        self.chart_width = 1200
        self.chart_height = 800
    
    def load_data(self) -> bool:
        """
        Load OHLCV data from CSV file and prepare for analysis.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        csv_filename = os.path.join(
            self.data_folder,
            f'{self.symbol}_{self.duration.replace(" ", "_")}_{self.bar_size.replace(" ", "_")}.csv'
        )
        
        try:
            self.raw_data = pd.read_csv(csv_filename, index_col='date', parse_dates=True)
            self.raw_data.sort_index(inplace=True)  # Ensure chronological order
            
            # Calculate cumulative returns for buy and hold strategy
            self.raw_data['returns'] = (self.raw_data['close'] / self.raw_data['close'].iloc[0]) - 1
            
            # Prepare chart-ready data
            self._format_chart_data()
            
            print(f"✓ Loaded {len(self.raw_data)} bars for {self.symbol}")
            print(f"  Date range: {self.raw_data.index[0]} to {self.raw_data.index[-1]}")
            print(f"\nDataFrame tail:")
            print(self.raw_data.tail())
            return True
            
        except FileNotFoundError:
            print(f"❌ CSV file not found: {csv_filename}")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def _format_chart_data(self) -> None:
        """Format OHLCV data for lightweight-charts consumption."""
        if self.raw_data is None:
            return
            
        ohlc = self.raw_data[['open', 'high', 'low', 'close', 'volume']].copy()
        ohlc['time'] = ohlc.index.strftime('%Y-%m-%dT%H:%M:%S')
        self.chart_data = ohlc[['time', 'open', 'high', 'low', 'close', 'volume']].reset_index(drop=True)
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """
        Get the raw OHLCV data.
        
        Returns:
            DataFrame with OHLCV data or None if not loaded
        """
        return self.raw_data.copy() if self.raw_data is not None else None
    
    def display_chart(self) -> None:
        """Display interactive candlestick chart with returns subchart and trading signals."""
        if self.chart_data is None:
            print("❌ No chart data available. Call load_data() first.")
            return
        
        # Generate trading signals before displaying chart
        self.add_trading_signals()
        
        # Create main chart with specific inner dimensions
        chart = Chart(toolbox=True, width=self.chart_width, height=self.chart_height, 
                     inner_width=1.0, inner_height=0.6)
        chart.watermark(f"{self.symbol} - Price Chart")
        
        # Create subchart for returns - this automatically syncs with main chart
        returns_chart = chart.create_subchart(position='bottom', width=1.0, height=0.4)
        returns_chart.watermark('Buy & Hold Returns (%)')
        
        # Set candlestick data on main chart
        chart.set(self.chart_data)
        
        # Add trading signal markers to the main chart (one by one)
        if hasattr(self, 'trading_signals') and self.trading_signals:
            for signal in self.trading_signals:
                chart.marker(
                    time=signal['time'],
                    position=signal['position'],
                    color=signal['color'],
                    shape=signal['shape'],
                    text=signal['text']
                )
            print(f"✓ Added {len(self.trading_signals)} trading signals to chart")
        
        # Prepare returns data for line chart
        returns_data = pd.DataFrame({
            'time': self.raw_data.index.strftime('%Y-%m-%dT%H:%M:%S'),
            'Returns (%)': self.raw_data['returns'] * 100  # Convert to percentage
        }).reset_index(drop=True)
        
        # Create line chart on subchart and set data
        returns_line = returns_chart.create_line(name='Returns (%)')
        returns_line.set(returns_data)
        
        chart.show(block=True)
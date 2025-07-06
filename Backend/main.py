from backtester import Backtester


def main():
    """Entry point for the backtester."""
    # Create backtester instance
    backtester = Backtester(symbol="AAPL", bar_size="1 hour")

    # Load data and display chart
    if backtester.load_data():
        # Display chart
        backtester.display_chart()


if __name__ == "__main__":
    main()

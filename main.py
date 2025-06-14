from src.fetch_data import ICLRDataCollector
import os

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    
    # Initialize collector
    collector = ICLRDataCollector()

    # Collect data for ICLR 2018–2024 (change range if needed)
    #collector.collect_multiple_years(list(range(2018, 2025)))
    collector.collect_multiple_years([2024])

    print("\nAll year-wise data saved in 'output/' folder")

try:
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
except ImportError:
    print("Pandas NOT FOUND")
except Exception as e:
    print(f"Error importing pandas: {e}")

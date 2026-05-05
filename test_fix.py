import os
import sys
import pandas as pd
from datetime import datetime

# Set path
sys.path.append(os.path.abspath("backend"))

try:
    from main import apply_filters, load_data, get_kpis
    print("Import main success")
    
    df = load_data()
    print("Load data success, records:", len(df))
    
    # Simulate problematic filter
    start_date = "2014-01-03"
    end_date = "2017-12-30"
    
    # Test apply_filters directly
    try:
        filtered = apply_filters(df, start_date=start_date, end_date=end_date)
        print("Apply filters success, records:", len(filtered))
        
        if not filtered.empty:
            print("KPI check (total sales):", filtered["Sales"].sum())
        else:
            print("Filtered result is EMPTY")
            
    except Exception as e:
        print("Apply filters FAILED:", str(e))
        import traceback
        traceback.print_exc()

except Exception as e:
    print("Import or basic load FAILED:", str(e))
    import traceback
    traceback.print_exc()

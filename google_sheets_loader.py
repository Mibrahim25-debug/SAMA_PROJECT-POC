import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import traceback

def load_to_google_sheets(df, sheet_id):
    """
    Pushes a cleaned pandas DataFrame securely to a Google Sheet.
    """
    print(f"Authenticating with Google Cloud...")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        credentials = Credentials.from_service_account_file(
            "service_account.json", scopes=scopes
        )
        client = gspread.authorize(credentials)
        
        print(f"Connecting to Google Sheet ID: {sheet_id}...")
        spreadsheet = client.open_by_key(sheet_id)
        
        # BULLETPROOF FIX: Get the first tab automatically, no matter what it is named
        worksheet = spreadsheet.sheet1
        
        print(f"🧹 Clearing old data...")
        worksheet.clear()
        
        clean_df = df.fillna("")
        data_to_upload = [clean_df.columns.values.tolist()] + clean_df.values.tolist()
        
        print(f"Uploading {len(clean_df)} rows of data...")
        worksheet.update(data_to_upload)
        
        print("Data successfully loaded to Google Sheets!")
        
    except gspread.exceptions.APIError as e:
        print(f"\n GOOGLE API ERROR: Google blocked the request. Did you enable the Sheets/Drive APIs in Google Cloud?")
        print(f"Exact Error: {e}")
    except Exception as e:
        print("\n DIAGNOSTIC ERROR REPORT:")
        print(repr(e))
        traceback.print_exc()

# ==========================================
# PIPELINE INTEGRATION TEST
# ==========================================
if __name__ == "__main__":
    data = {
        'Indicator': ['Inflation Rate', 'GDP Growth', 'Interest Rate'],
        'Q1 2026': ['2.1%', '3.4%', '5.5%'],
        'Q2 2026': ['2.3%', '3.6%', '5.5%']
    }
    test_df = pd.DataFrame(data)
    
    SHEET_ID = "15EZgNqiq9MCCSS3aD-I3gzwt1SDPB4ARCjRtJIG8iqA"
    
    print("\n--- Testing Google Sheets Integration ---")
    load_to_google_sheets(test_df, SHEET_ID)
    print("---------------------------------------\n")
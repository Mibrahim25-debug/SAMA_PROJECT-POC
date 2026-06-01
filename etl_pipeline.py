import os
import re
import datetime
import pdfplumber
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import traceback

def extract_date_from_filename(filename):
    """Strips SAMA boilerplate to isolate the date string."""
    clean_name = filename.replace('.pdf', '')
    prefixes = ["Weekly_Points_of_Sale_Transactions_Report_", "POS_Report_", "Weekly_POS_"]
    for prefix in prefixes:
        clean_name = clean_name.replace(prefix, '')
    return clean_name if clean_name else "Unknown_Date"

def clean_sector_name(text):
    """
    ENTERPRISE FILTER: 
    Strictly removes all Arabic text and invisible PDF characters.
    Leaves only standard English alphabet characters and spaces.
    """
    if pd.isna(text) or not text:
        return None
        
    text = str(text).replace('\n', ' ').replace('\r', '')
    # Regex: Keep ONLY standard ASCII (English letters, symbols). Removes Arabic entirely.
    english_only = re.sub(r'[^\x00-\x7F]+', '', text)
    clean_text = " ".join(english_only.split()).strip()
    
    return clean_text if clean_text else None

def clean_financial_number(value):
    """Strips commas and converts string numbers to clean integers."""
    if pd.isna(value) or not value:
        return 0
    clean_val = str(value).replace(',', '').replace('\n', '').strip()
    try:
        return int(float(clean_val))
    except ValueError:
        return 0

def process_enterprise_pdfs(folder_path):
    print(f"📂 Scanning Data Lake Directory: {folder_path}...")
    
    all_rows = []
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDFs found in the specified folder.")
        return None
        
    print(f"🔍 Found {len(pdf_files)} reports. Extracting FULL raw financial payload...")
    ingestion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for count, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(folder_path, filename)
        report_week = extract_date_from_filename(filename)
        
        try:
            with pdfplumber.open(file_path) as pdf:
                table = pdf.pages[0].extract_table()
                
                if table:
                    df = pd.DataFrame(table)
                    # Slice off the top 3 rows (ignoring SAMA's messy multi-language headers)
                    data_df = df.iloc[3:].copy()
                    
                    for index, row in data_df.iterrows():
                        raw_sector = row[0]
                        clean_sector = clean_sector_name(raw_sector)
                        
                        # Skip empty rows or the summary "Total" rows at the bottom
                        if not clean_sector or "Total" in clean_sector or "Sector" in clean_sector:
                            continue
                            
                        try:
                            # POSITIONAL TARGETING:
                            # By counting backwards, we perfectly target the facts every time.
                            # Indices -1 and -2 are percentages (Ignored for DB integrity).
                            raw_curr_count = row.iloc[-4]
                            raw_curr_value = row.iloc[-3]
                            raw_prev_count = row.iloc[-6]
                            raw_prev_value = row.iloc[-5]
                            
                            # Multiply by 1000 to correct SAMA's "In Thousands" formatting
                            curr_count = clean_financial_number(raw_curr_count) * 1000
                            curr_value_sar = clean_financial_number(raw_curr_value) * 1000
                            prev_count = clean_financial_number(raw_prev_count) * 1000
                            prev_value_sar = clean_financial_number(raw_prev_value) * 1000
                            
                            all_rows.append({
                                "ingestion_timestamp": ingestion_time,
                                "source_filename": filename,
                                "report_week": report_week,
                                "business_sector": clean_sector,
                                "current_tx_count": curr_count,
                                "current_tx_value_sar": curr_value_sar,
                                "previous_tx_count": prev_count,
                                "previous_tx_value_sar": prev_value_sar
                            })
                        except IndexError:
                            pass # Skip rows that are fundamentally broken in the PDF
                            
                    print(f"   ✅ [{count}/{len(pdf_files)}] Processed: {filename}")
                else:
                    print(f"   ⚠️ [{count}/{len(pdf_files)}] No table found.")
                    
        except Exception as e:
            print(f"   ❌ Failed to read {filename}: {e}")

    if all_rows:
        print("\n⏳ Constructing Enterprise Staging Table...")
        master_df = pd.DataFrame(all_rows)
        print(f"✅ DATA PIPELINE COMPLETE! Master dataset contains {len(master_df)} pristine rows.")
        return master_df
    else:
        return None

def load_to_google_sheets(df, sheet_id):
    print(f"\n🔄 Authenticating with Google Cloud Identity...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    try:
        credentials = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(credentials)
        worksheet = client.open_by_key(sheet_id).sheet1
        
        print(f"🧹 Truncating old staging table...")
        worksheet.clear()
        
        clean_df = df.fillna("").astype(str)
        data_to_upload = [clean_df.columns.values.tolist()] + clean_df.values.tolist()
        
        print(f"⬆️ Uploading expanded data payload ({len(clean_df)} rows) to Google Sheets...")
        worksheet.update(data_to_upload)
        
        # Apply basic formatting for the new wider table
        worksheet.format("A1:H1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })
        
        print("✅ STAGE 1 COMPLETE: Enterprise Data Warehouse is live!")
        
    except Exception as e:
        print("\n❌ UPLOAD ERROR:")
        traceback.print_exc()

# ==========================================
# MASTER PIPELINE EXECUTION
# ==========================================
if __name__ == "__main__":
    FOLDER_NAME = "sama_pos_pdfs" 
    YOUR_SHEET_ID = "15EZgNqiq9MCCSS3aD-I3gzwt1SDPB4ARCjRtJIG8iqA" 
    
    master_dataset = process_enterprise_pdfs(FOLDER_NAME)
    if master_dataset is not None:
        load_to_google_sheets(master_dataset, YOUR_SHEET_ID)
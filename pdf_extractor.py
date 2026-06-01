import pdfplumber
import pandas as pd
import os

def extract_financial_table(pdf_path, page_number=0):
    """
    Extracts the first table found on a specific page of a PDF 
    and converts it to a pandas DataFrame.
    """
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found at {pdf_path}")
        return None

    print(f"📄 Analyzing {pdf_path} (Page {page_number + 1})...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_number >= len(pdf.pages):
                print(f"❌ Error: Page number out of range.")
                return None
                
            page = pdf.pages[page_number]
            table = page.extract_table()
            
            if not table:
                print(f"⚠️ No tabular data found on this page.")
                return None
                
            # The first row is usually the header
            headers = table[0]
            # The remaining rows are the data
            data = table[1:]
            
            # Convert to a pandas DataFrame for structured handling
            df = pd.DataFrame(data, columns=headers)
            
            # Optional: Drop rows where all columns are entirely empty/None
            df.dropna(how='all', inplace=True)
            
            print("✅ Table extracted successfully!")
            return df
            
    except Exception as e:
        print(f"❌ Failed to parse PDF: {e}")
        return None

# ==========================================
# TEST EXECUTION
# ==========================================
if __name__ == "__main__":
    # TODO: Place a sample 2026 SAMA PDF in the same folder and rename this variable
    SAMPLE_PDF = "sama_2026_sample.pdf" 
    TARGET_PAGE = 0 # Remember: Page 0 is the 1st page, Page 1 is the 2nd page, etc.
    
    df = extract_financial_table(SAMPLE_PDF, TARGET_PAGE)
    
    if df is not None:
        print("\n--- Data Preview ---")
        print(df.head())
        print("--------------------\n")
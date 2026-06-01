# SAMA POS Data Warehouse - ETL Pipeline (Milestone 1) 

## Overview
This is **Milestone 1** of an Proof of Concept (POC) I am building to automate financial data ingestion. 

The goal of this pipeline is to automatically scrape, extract, and clean weekly Point of Sale (POS) transaction reports from the Saudi Central Bank (SAMA) portal and stage them in a normalized Google Sheet, ready for AI/BI integration.

I built this because doing this manually for 52 weeks of PDF reports is impossible, and SAMA's website relies heavily on dynamic JavaScript and complex PDF structures that break standard scrapers.

## Tech Stack 🛠️
* **Python 3.x**
* **Web Scraping:** `Selenium` (Headless Chrome), `requests`, `BeautifulSoup4`
* **Data Extraction:** `pdfplumber`
* **Data Transformation:** `pandas`
* **Cloud Integration:** `gspread`, `google-auth` (Google Sheets API)

## How It Works (The Architecture) 🏗️

This pipeline is split into three main engines:

### 1. The Headless Scraper
SAMA's portal is built on Microsoft SharePoint and hides its PDF links behind JavaScript and pagination. I used **Selenium** to launch an invisible browser that:
* Waits for the JS to render.
* Uses a forced JavaScript execution click (`arguments[0].click()`) to bypass cookie banners and sticky footers that block the "Next Page" button.
* Scans for specific years (e.g., 2025) and dynamically stops when it reaches older data.
* Passes the secure browser session cookies over to `requests` for high-speed, anti-ban PDF downloading.

### 2. The Positional PDF Extractor (The Hard Part)
SAMA's PDFs are a data engineering nightmare. They have merged headers, hidden line-breaks, and mix Arabic and English in the same cells. 
* Instead of trying to read the messy headers, I engineered a **Positional Targeting** script. 
* It slices off the top 3 rows, scans backwards from the end of the table (Index -3, -4, etc.), and mathematically isolates the Current Week and Previous Week's financial facts.
* I used Regex (`re.sub`) to completely strip the Arabic text, leaving a clean English sector name.

### 3. The Google Sheets Loader
The script normalizes the data into a strict "tall" database schema (Tidy Data format). It applies standard `snake_case` column headers, adds an `ingestion_timestamp`, and pushes the final payload to a Google Sheet using a Service Account key. (Note: The `service_account.json` is safely `.gitignore`'d!).

## How to Run It 💻

1. **Clone the repo:**
   ```bash
   git clone [https://github.com/YOUR-USERNAME/sama-etl-pipeline.git](https://github.com/YOUR-USERNAME/sama-etl-pipeline.git)
   cd sama-etl-pipeline

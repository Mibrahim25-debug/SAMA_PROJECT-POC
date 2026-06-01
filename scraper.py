import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def download_full_year_reports(target_url, target_year="2025", download_folder="sama_pos_pdfs"):
    print(f"🤖 Starting SAMA Scraper | Target: Full Year {target_year}...")
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    
    print("⚙️ Initializing ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    target_pdf_links = set()
    page_number = 1
    MAX_PAGES = 25 # Increased safety limit since we are scanning a full year

    try:
        print(f"🌐 Loading {target_url}...")
        driver.get(target_url)
        print("⏳ Waiting 8 seconds for initial load...")
        time.sleep(8) 
        
        while page_number <= MAX_PAGES:
            print(f"\n📄 Scanning Page {page_number}...")
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            found_previous_year = False
            
            # --- THE FULL YEAR FILTER ---
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if '.pdf' in href:
                    # If it belongs to our target year (2025), keep it!
                    if target_year in href:
                        full_url = urljoin(target_url, link['href'])
                        target_pdf_links.add(full_url)
                    
                    # If we hit 2024, we know we have passed January 2025
                    if str(int(target_year) - 1) in href:
                        found_previous_year = True
                        
            print(f"🎯 {target_year} files found so far: {len(target_pdf_links)}")
            
            # Smart Exit: Stop paginating if we've traveled back in time past our target year
            if found_previous_year and len(target_pdf_links) > 0:
                print(f"🛑 Found {int(target_year) - 1} data. We have successfully collected all of {target_year}. Stopping scan.")
                break
            
            # Click Next Page
            try:
                next_button = driver.find_element(
                    By.XPATH, 
                    "//a[@title='Next' or contains(text(), 'Next') or contains(@title, 'التالي') or @title='Next page']"
                )
                print("➡️ Forcing 'Next Page' click via JavaScript...")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_button)
                
                page_number += 1
                time.sleep(5) 
                
            except NoSuchElementException:
                print("\n🛑 Reached the end of SAMA's database.")
                break
            except Exception as e:
                print(f"⚠️ Unexpected error clicking 'Next': {e}")
                break

        # --- THE SECURE DOWNLOADER ---
        if len(target_pdf_links) == 0:
            print(f"\n⚠️ No files found for {target_year}.")
        else:
            print(f"\n⬇️ Preparing secure download session...")
            
            session = requests.Session()
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
                
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": target_url,
                "Accept": "application/pdf,application/octet-stream"
            })

            print(f"⬇️ Starting download of {len(target_pdf_links)} files for {target_year}...")
            
            for count, pdf_url in enumerate(list(target_pdf_links), 1):
                file_name = pdf_url.split('/')[-1].split('?')[0]
                file_path = os.path.join(download_folder, file_name)
                
                if os.path.exists(file_path):
                    print(f"⏭️ Skipping {file_name} (Already downloaded)")
                    continue
                    
                print(f"📥 Downloading [{count}/{len(target_pdf_links)}]: {file_name}...")
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        time.sleep(1.5) # Polite pause to prevent IP blocking
                        response = session.get(pdf_url, timeout=15)
                        response.raise_for_status() 
                        
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        print("   ✅ Success!")
                        break 
                        
                    except Exception as e:
                        print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                        if attempt == max_retries - 1:
                            print(f"   ❌ Could not download {file_name} after {max_retries} attempts.")
                            
            print(f"\n✅ {target_year} BULK DOWNLOAD COMPLETE! You should have approximately 52 files.")

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
    finally:
        driver.quit()
        print("🛑 Browser closed.")

if __name__ == "__main__":
    SAMA_URL = "https://www.sama.gov.sa/en-us/statistics/indices/pages/pos.aspx"
    download_full_year_reports(SAMA_URL)
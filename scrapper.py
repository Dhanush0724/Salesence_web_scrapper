"""
FAST Single-Session Seller Scraper with Excel Export
Optimized for speed by reusing the same browser session

Features:
- Reads URLs from SQLite database
- Updates status in database
- Exports to Excel file
- Reuses browser session for speed
- No Google Sheets API needed

Expected speed: 15-25 seconds per product
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import sqlite3
import time
import traceback
import os
from datetime import datetime


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
DATABASE_FILE = 'product_urls.db'
EXCEL_FILE = 'seller_data.xlsx'
BATCH_SIZE = 100
CATEGORY_FILTER = None  # Set to category name to filter, or None for all


# -------------------------------------------------
# DATABASE FUNCTIONS
# -------------------------------------------------

def get_pending_urls(db_path, limit=100, category=None):
    """Get URLs that need to be processed"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if category:
        cursor.execute('''
            SELECT id, url, category 
            FROM product_urls 
            WHERE status = 'pending' AND category = ?
            LIMIT ?
        ''', (category, limit))
    else:
        cursor.execute('''
            SELECT id, url, category 
            FROM product_urls 
            WHERE status = 'pending'
            LIMIT ?
        ''', (limit,))
    
    results = [{'id': row[0], 'url': row[1], 'category': row[2]} for row in cursor.fetchall()]
    conn.close()
    
    return results


def update_status(db_path, url_id, status):
    """Update URL status in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE product_urls SET status = ? WHERE id = ?', (status, url_id))
    conn.commit()
    conn.close()


def get_stats(db_path):
    """Get processing statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT status, COUNT(*) FROM product_urls GROUP BY status')
    stats = dict(cursor.fetchall())
    
    cursor.execute('SELECT COUNT(*) FROM product_urls')
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'pending': stats.get('pending', 0),
        'processing': stats.get('processing', 0),
        'completed': stats.get('completed', 0),
        'failed': stats.get('failed', 0)
    }


# -------------------------------------------------
# EXCEL FUNCTIONS
# -------------------------------------------------

def save_to_excel(results, excel_file):
    """Save or append results to Excel file"""
    if not results:
        print("⚠ No results to save")
        return
    
    new_df = pd.DataFrame(results)
    
    if os.path.exists(excel_file):
        try:
            # Load existing data and append
            existing_df = pd.read_excel(excel_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_excel(excel_file, index=False)
            print(f"✓ Appended {len(results)} rows to existing '{excel_file}'")
        except Exception as e:
            print(f"Error reading existing file: {e}")
            new_df.to_excel(excel_file, index=False)
            print(f"✓ Created new '{excel_file}'")
    else:
        # Create new file
        new_df.to_excel(excel_file, index=False)
        print(f"✓ Created new '{excel_file}'")


# -------------------------------------------------
# DRIVER SETUP
# -------------------------------------------------

def setup_driver():
    """Setup optimized Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(r"--user-data-dir=C:\selenium_profiles\trendyol")
    
    # Suppress logs
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    driver.set_page_load_timeout(60)
    
    return driver


# -------------------------------------------------
# SAFE EXTRACT HELPER
# -------------------------------------------------

def safe_extract(driver, xpath_list, timeout=5):
    """Quickly extract data using multiple XPath strategies"""
    for xpath in xpath_list:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            value = element.text.strip()
            if value and value != ":" and len(value) > 1:
                return value
        except:
            continue
    return "Not found"


# -------------------------------------------------
# PROCESS SINGLE PRODUCT (OPTIMIZED)
# -------------------------------------------------

def process_product(driver, wait, product_url, category, is_first=False):
    """Process a single product with optimizations"""
    
    try:
        # Navigate to product
        driver.get(product_url)
        time.sleep(1)  # Give page time to load

        # Handle cookies only on first product
        if is_first:
            try:
                reject_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(., 'Reddet') or contains(., 'Reject')]")
                    )
                )
                reject_btn.click()
                time.sleep(1)
            except:
                pass

        # Remove overlay
        driver.execute_script("""
            const overlay = document.querySelector('[data-testid="overlay"]');
            if (overlay) overlay.remove();
        """)

        # Click Buy Now
        buy_now_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[normalize-space()='Şimdi Al'] or normalize-space()='Şimdi Al']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", buy_now_btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", buy_now_btn)

        # Wait for checkout
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Sipariş') or contains(text(),'Özet')]")
            )
        )
        time.sleep(0.5)

        # Open contract
        contract = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Mesafeli Satış Sözleşmesi')]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", contract)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", contract)
        time.sleep(1.5)

        # Extract data
        seller_name = safe_extract(driver, [
            "//strong[contains(text(), 'Ticaret Unvanı')]/ancestor::tr/td[last()]",
            "//td[contains(text(), 'Ticaret Unvanı')]/following-sibling::td"
        ], timeout=5)

        seller_phone = safe_extract(driver, [
            "//strong[contains(text(), 'Satıcının Telefonu')]/ancestor::tr/td[last()]",
            "//td[contains(text(), 'Telefon')]/following-sibling::td"
        ], timeout=5)

        seller_email = safe_extract(driver, [
            "//td[contains(text(), 'KEP') and contains(text(), 'E-posta')]/following-sibling::td",
            "//strong[contains(text(), 'KEP')]/ancestor::tr/td[last()]",
            "//*[contains(text(), '@kep.tr')]",
            "//*[contains(text(), '@hs')]"
        ], timeout=5)

        return {
            "Product Link": product_url,
            "Category": category,
            "Seller Name": seller_name,
            "Seller Phone": seller_phone,
            "Seller Email": seller_email,
            "Processed Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success": True
        }

    except Exception as e:
        print(f"    ✗ Error: {str(e)[:100]}")
        return {
            "Product Link": product_url,
            "Category": category,
            "Seller Name": "Failed",
            "Seller Phone": "Failed",
            "Seller Email": "Failed",
            "Processed Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Error": str(e)[:200],
            "success": False
        }


# -------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------

def main():
    print("\n" + "="*80)
    print("FAST SELLER SCRAPER WITH EXCEL EXPORT")
    print("="*80 + "\n")
    
    # Check if database exists
    if not os.path.exists(DATABASE_FILE):
        print(f"✗ Database file '{DATABASE_FILE}' not found!")
        print("Please make sure the database file exists in the same directory.")
        input("\nPress ENTER to exit...")
        return
    
    # Get initial stats
    stats = get_stats(DATABASE_FILE)
    print(f"Database: {DATABASE_FILE}")
    print(f"Excel File: {EXCEL_FILE}")
    print(f"\nDatabase Stats:")
    print(f"  Total URLs: {stats['total']:,}")
    print(f"  Pending: {stats['pending']:,}")
    print(f"  Completed: {stats['completed']:,}")
    print(f"  Failed: {stats['failed']:,}")
    
    if stats['pending'] == 0:
        print("\n⚠ No pending URLs to process!")
        input("\nPress ENTER to exit...")
        return
    
    # Get URLs to process
    url_items = get_pending_urls(DATABASE_FILE, limit=BATCH_SIZE, category=CATEGORY_FILTER)
    
    if not url_items:
        print("\n⚠ No URLs found!")
        input("\nPress ENTER to exit...")
        return
    
    print(f"\n{'='*80}")
    print(f"Processing {len(url_items)} URLs...")
    print(f"{'='*80}\n")
    
    # Setup single browser session
    print("Setting up browser...")
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    
    results = []
    success_count = 0
    failed_count = 0
    
    start_time = time.time()
    
    # Process each URL
    for i, item in enumerate(url_items, 1):
        url_id = item['id']
        url = item['url']
        category = item['category']
        
        product_start_time = time.time()
        
        print(f"\n[{i}/{len(url_items)}] {category}: {url[:70]}...")
        
        # Mark as processing
        update_status(DATABASE_FILE, url_id, 'processing')
        
        # Check if browser is still alive, restart if needed
        try:
            driver.current_url  # Test if driver is responsive
        except:
            print("  ⚠ Browser crashed! Restarting...")
            try:
                driver.quit()
            except:
                pass
            driver = setup_driver()
            wait = WebDriverWait(driver, 20)
            print("  ✓ Browser restarted")
        
        # Process product
        is_first = (i == 1)
        result = process_product(driver, wait, url, category, is_first=is_first)
        
        product_elapsed = time.time() - product_start_time
        
        if result['success']:
            # Remove 'success' key before saving
            result_to_save = {k: v for k, v in result.items() if k != 'success'}
            results.append(result_to_save)
            update_status(DATABASE_FILE, url_id, 'completed')
            success_count += 1
            print(f"  ✓ Seller: {result['Seller Name']} ({product_elapsed:.1f}s)")
        else:
            # Remove 'success' key before saving
            result_to_save = {k: v for k, v in result.items() if k != 'success'}
            results.append(result_to_save)
            update_status(DATABASE_FILE, url_id, 'failed')
            failed_count += 1
            print(f"  ✗ Failed ({product_elapsed:.1f}s)")
        
        # Progress update
        total_processed = success_count + failed_count
        avg_time = (time.time() - start_time) / total_processed
        remaining = len(url_items) - total_processed
        eta_seconds = avg_time * remaining
        eta_minutes = eta_seconds / 60
        
        print(f"  Progress: {total_processed}/{len(url_items)} | Avg: {avg_time:.1f}s/product | ETA: {eta_minutes:.1f} min")
    
    # Close browser
    try:
        driver.quit()
    except:
        pass
    
    elapsed_time = time.time() - start_time
    
    # -------------------------------------------------
    # SAVE RESULTS TO EXCEL
    # -------------------------------------------------
    print(f"\n{'='*80}")
    print("Saving results to Excel...")
    save_to_excel(results, EXCEL_FILE)
    
    # Print summary
    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"⏱  Total Time: {elapsed_time/60:.1f} minutes ({elapsed_time:.0f} seconds)")
    print(f"⚡ Average Speed: {elapsed_time/len(url_items):.1f} seconds/product")
    print(f"\n✓ Successful: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"📊 Excel File: {os.path.abspath(EXCEL_FILE)}")
    
    # Updated stats
    final_stats = get_stats(DATABASE_FILE)
    print(f"\nUpdated Database Stats:")
    print(f"  Pending: {final_stats['pending']:,}")
    print(f"  Completed: {final_stats['completed']:,}")
    print(f"  Failed: {final_stats['failed']:,}")
    print("="*80 + "\n")
    
    input("Press ENTER to exit...")


if __name__ == "__main__":
    main()
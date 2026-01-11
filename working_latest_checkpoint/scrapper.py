"""
FAST Single-Session Seller Scraper - DATABASE VERSION
Fetches URLs from SQLite database and updates status
Compatible with product_urls.db schema
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
from datetime import datetime
import os
import glob


# -------------------------------------------------
# DATABASE FUNCTIONS
# -------------------------------------------------

def ensure_seller_columns(db_path="product_urls.db"):
    """Add seller columns to database if they don't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if seller columns exist
    cursor.execute("PRAGMA table_info(product_urls)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add missing columns
    if 'seller_name' not in columns:
        cursor.execute("ALTER TABLE product_urls ADD COLUMN seller_name TEXT")
    if 'seller_phone' not in columns:
        cursor.execute("ALTER TABLE product_urls ADD COLUMN seller_phone TEXT")
    if 'seller_email' not in columns:
        cursor.execute("ALTER TABLE product_urls ADD COLUMN seller_email TEXT")
    if 'scraped_at' not in columns:
        cursor.execute("ALTER TABLE product_urls ADD COLUMN scraped_at TIMESTAMP")
    
    conn.commit()
    conn.close()


def get_pending_urls(db_path="product_urls.db", limit=None):
    """Fetch pending URLs from database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if limit:
        query = "SELECT id, url, category FROM product_urls WHERE status = 'pending' LIMIT ?"
        cursor.execute(query, (limit,))
    else:
        query = "SELECT id, url, category FROM product_urls WHERE status = 'pending'"
        cursor.execute(query)
    
    urls = cursor.fetchall()
    conn.close()
    return urls


def update_product_status(db_path, product_id, status, seller_data=None):
    """Update product status in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if seller_data and status == "completed":
        cursor.execute("""
            UPDATE product_urls 
            SET status = ?, 
                seller_name = ?,
                seller_phone = ?,
                scraped_at = ?
            WHERE id = ?
        """, (
            status,
            seller_data.get('Seller Name', ''),
            seller_data.get('Seller Phone', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            product_id
        ))
    else:
        cursor.execute("""
            UPDATE product_urls 
            SET status = ?
            WHERE id = ?
        """, (status, product_id))
    
    conn.commit()
    conn.close()


def get_database_stats(db_path="product_urls.db"):
    """Get statistics from database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM product_urls WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_urls WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_urls WHERE status = 'processing'")
    processing = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_urls")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'pending': pending,
        'completed': completed,
        'processing': processing
    }


# -------------------------------------------------
# EXCEL FILE FUNCTIONS
# -------------------------------------------------

def find_existing_excel_files():
    """Find all seller_data Excel files in current directory"""
    excel_files = glob.glob("seller_data_*.xlsx")
    # Sort by modification time (newest first)
    excel_files.sort(key=os.path.getmtime, reverse=True)
    return excel_files


def get_excel_file_choice():
    """Ask user whether to append to existing file or create new one"""
    existing_files = find_existing_excel_files()
    
    if not existing_files:
        print("No existing Excel files found. Will create a new file.")
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"seller_data_{timestamp}.xlsx", "new"
    
    print("\n" + "="*80)
    print("EXCEL FILE OPTIONS")
    print("="*80)
    print("\nExisting Excel files found:")
    for i, file in enumerate(existing_files[:5], 1):  # Show max 5 recent files
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        file_size = os.path.getsize(file)
        try:
            df = pd.read_excel(file)
            row_count = len(df)
            print(f"  {i}. {file} ({row_count} rows, {file_size/1024:.1f}KB, modified: {mod_time.strftime('%Y-%m-%d %H:%M')})")
        except:
            print(f"  {i}. {file} ({file_size/1024:.1f}KB, modified: {mod_time.strftime('%Y-%m-%d %H:%M')})")
    
    print("\nOptions:")
    print("  1. Append to existing Excel file")
    print("  2. Create new Excel file")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            if len(existing_files) == 1:
                selected_file = existing_files[0]
                print(f"Will append to: {selected_file}")
                return selected_file, "append"
            else:
                print("\nSelect file to append to:")
                for i, file in enumerate(existing_files[:5], 1):
                    print(f"  {i}. {file}")
                
                while True:
                    file_choice = input(f"Enter file number (1-{min(5, len(existing_files))}): ").strip()
                    try:
                        file_idx = int(file_choice) - 1
                        if 0 <= file_idx < min(5, len(existing_files)):
                            selected_file = existing_files[file_idx]
                            print(f"Will append to: {selected_file}")
                            return selected_file, "append"
                        else:
                            print("Invalid number. Please try again.")
                    except:
                        print("Invalid input. Please enter a number.")
        
        elif choice == "2":
            timestamp = datetime.now().strftime("%Y%m%d")
            new_file = f"seller_data_{timestamp}.xlsx"
            
            # Check if file with today's date already exists
            if new_file in existing_files:
                counter = 1
                while f"seller_data_{timestamp}_{counter}.xlsx" in existing_files:
                    counter += 1
                new_file = f"seller_data_{timestamp}_{counter}.xlsx"
            
            print(f"Will create new file: {new_file}")
            return new_file, "new"
        
        else:
            print("Invalid choice. Please enter 1 or 2.")


# -------------------------------------------------
# DRIVER SETUP
# -------------------------------------------------

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(r"--user-data-dir=C:\selenium_profiles\trendyol")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.set_page_load_timeout(60)
    return driver


# -------------------------------------------------
# SAFE EXTRACT
# -------------------------------------------------

def safe_extract(driver, xpath_list, timeout=5):
    for xpath in xpath_list:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            text = element.text.strip()
            if text and text != ":" and len(text) > 1:
                return text
        except:
            continue
    return "Not found"


# -------------------------------------------------
# PROCESS SINGLE PRODUCT
# -------------------------------------------------

def process_product(driver, wait, product_id, product_url, category, is_first=False, db_path="product_urls.db"):
    """Process a single product and update database"""
    
    # Update status to processing
    update_product_status(db_path, product_id, "processing")
    
    try:
        driver.get(product_url)

        # Cookie handling (only once)
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

        # Click "Şimdi Al"
        buy_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[normalize-space()='Şimdi Al'] or normalize-space()='Şimdi Al']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", buy_btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", buy_btn)

        # Wait for checkout
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Sipariş') or contains(text(),'Özet')]")
            )
        )

        # Open distance sales contract
        contract = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Mesafeli Satış Sözleşmesi')]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", contract)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", contract)
        time.sleep(1.5)

        # Extract seller data
        seller_name = safe_extract(driver, [
            "//strong[contains(text(), 'Ticaret Unvanı')]/ancestor::tr/td[last()]",
            "//td[contains(text(), 'Ticaret Unvanı')]/following-sibling::td"
        ])

        seller_phone = safe_extract(driver, [
            "//strong[contains(text(), 'Satıcının Telefonu')]/ancestor::tr/td[last()]",
            "//td[contains(text(), 'Telefon')]/following-sibling::td"
        ])

        seller_data = {
            "Product ID": product_id,
            "Product URL": product_url,
            "Category": category,
            "Seller Name": seller_name,
            "Seller Phone": seller_phone,
            "Success": True
        }
        
        # Update database with completed status and seller data
        update_product_status(db_path, product_id, "completed", seller_data)
        
        return seller_data

    except Exception as e:
        # Update database with pending status (to retry later)
        update_product_status(db_path, product_id, "pending")
        
        return {
            "Product ID": product_id,
            "Product URL": product_url,
            "Category": category,
            "Seller Name": "Error",
            "Seller Phone": "Error",
            "Success": False,
            "Error": str(e)[:200]
        }


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    DB_PATH = "product_urls.db"
    
    print("\n" + "="*80)
    print("DATABASE-CONNECTED SELLER SCRAPER")
    print("="*80 + "\n")
    
    # Ensure seller columns exist in database
    print("Checking database schema...")
    ensure_seller_columns(DB_PATH)
    print("✓ Database schema ready\n")
    
    # Get database statistics
    stats = get_database_stats(DB_PATH)
    print(f"Database Statistics:")
    print(f"  Total Products: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Processing: {stats['processing']}")
    print()
    
    if stats['pending'] == 0:
        print("No pending URLs to process!")
        return
    
    # Ask how many to process
    print(f"How many products to scrape? (Press Enter for all {stats['pending']} pending)")
    user_input = input("Number: ").strip()
    
    if user_input:
        try:
            limit = int(user_input)
        except:
            print("Invalid number, processing all pending URLs")
            limit = None
    else:
        limit = None
    
    # Fetch URLs from database
    products = get_pending_urls(DB_PATH, limit)
    
    if not products:
        print("\nNo products to process!")
        return
    
    print(f"\nFetched {len(products)} products from database\n")
    
    # Get Excel file choice (append or new)
    output_file, file_mode = get_excel_file_choice()
    
    print("\n" + "="*80 + "\n")
    
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)

    results = []
    start_time = time.time()

    for i, (product_id, url, category) in enumerate(products, 1):
        print(f"[{i}/{len(products)}] ID: {product_id} | Category: {category}")
        print(f"  URL: {url[:70]}...")
        product_start = time.time()

        data = process_product(driver, wait, product_id, url, category, is_first=(i == 1), db_path=DB_PATH)
        results.append(data)

        elapsed = time.time() - product_start
        status = "✓" if data["Success"] else "✗"
        print(f"  {status} Done in {elapsed:.1f}s | Seller: {data.get('Seller Name')}")
        print()

    driver.quit()

    # -------------------------------------------------
    # SAVE TO EXCEL (APPEND OR NEW)
    # -------------------------------------------------

    df_new = pd.DataFrame(results)
    columns_to_keep = ['Product ID', 'Product URL', 'Category', 'Seller Name', 'Seller Phone']
    df_new_export = df_new[columns_to_keep]
    
    if file_mode == "append" and os.path.exists(output_file):
        try:
            # Read existing data
            df_existing = pd.read_excel(output_file)
            # Append new data
            df_combined = pd.concat([df_existing, df_new_export], ignore_index=True)
            df_combined.to_excel(output_file, index=False)
            print(f"\n✓ Data appended to existing file: {output_file}")
            print(f"  Previous rows: {len(df_existing)}")
            print(f"  New rows: {len(df_new_export)}")
            print(f"  Total rows: {len(df_combined)}")
        except Exception as e:
            print(f"\n✗ Error appending to file: {e}")
            # Fallback: save to new file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"seller_data_{timestamp}.xlsx"
            df_new_export.to_excel(output_file, index=False)
            print(f"  Data saved to new file instead: {output_file}")
    else:
        df_new_export.to_excel(output_file, index=False)
        print(f"\n✓ Data saved to new file: {output_file}")

    total_time = time.time() - start_time
    successful = sum(1 for r in results if r["Success"])

    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"Total Products Processed: {len(products)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(products) - successful}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"Average: {total_time/len(products):.1f}s/product")
    
    # Updated statistics
    final_stats = get_database_stats(DB_PATH)
    print(f"\nUpdated Database Statistics:")
    print(f"  Pending: {final_stats['pending']}")
    print(f"  Completed: {final_stats['completed']}")
    print(f"  Processing: {final_stats['processing']}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
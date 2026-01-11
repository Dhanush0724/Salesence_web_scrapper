"""
Simple Product URL Collector for Trendyol
Collects thousands of product URLs and stores them in SQLite

Usage:
    python collect_urls.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time
import re
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

# SEARCH_TERMS = [
#     "telefon",      # phones
#     "laptop",       # laptops
#     "ayakkabı",     # shoes
#     "elbise",       # dresses
#     "çanta",        # bags
#     "tablet",       # tablets
#     "kulaklık",     # headphones
#     "saat",         # watches
# ]
SEARCH_TERMS = [
    "ev aletleri",        # home appliances
    "bebek ürünleri",     # baby products
    "spor ayakkabı",      # sports shoes
    "erkek tişört",       # men’s apparel
    "kadın ceket",        # women’s jackets
    "mutfak gereçleri",  # kitchen tools
    "oyuncak",            # toys
    "spor ekipmanları",  # sports equipment
    "ev dekorasyonu",    # home decoration
    "kişisel bakım",     # personal care
]

MAX_LINKS_PER_CATEGORY = 35  # URLs to collect per category
MAX_SCROLL_ATTEMPTS = 20      # How many times to scroll
DATABASE_FILE = 'product_urls.db'


# ============================================================================
# DATABASE SETUP
# ============================================================================

def setup_database(db_path):
    """Create database table for storing URLs"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            category TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for fast queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON product_urls(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON product_urls(category)')
    
    # Optimize database
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA synchronous=NORMAL')
    
    conn.commit()
    conn.close()
    print(f"✓ Database ready: {db_path}\n")


def save_urls_batch(db_path, urls, category):
    """Save URLs to database in batch"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    added = 0
    for url in urls:
        try:
            cursor.execute(
                'INSERT INTO product_urls (url, category) VALUES (?, ?)',
                (url, category)
            )
            added += 1
        except sqlite3.IntegrityError:
            # URL already exists, skip
            pass
    
    conn.commit()
    conn.close()
    
    return added


def get_stats(db_path):
    """Get database statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM product_urls')
    total = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT category, COUNT(*) 
        FROM product_urls 
        GROUP BY category
    ''')
    by_category = dict(cursor.fetchall())
    
    conn.close()
    
    return {'total': total, 'by_category': by_category}


# ============================================================================
# SELENIUM SETUP
# ============================================================================

def setup_driver():
    """Setup Selenium WebDriver"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    return driver


def accept_cookies(driver, wait):
    """Accept cookie banner if present"""
    try:
        time.sleep(2)
        cookie_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(@class, 'Button') or contains(text(),'Kabul') or contains(text(),'Accept')]"
            ))
        )
        cookie_button.click()
        print("  ✓ Cookies accepted")
        time.sleep(2)
    except:
        pass


def is_product_url(href):
    """Check if URL is a valid product link"""
    if not href or 'trendyol.com' not in href:
        return False
    
    # Product URL patterns
    patterns = [
        r'/p-[\w-]+',
        r'/[\w-]+-p-\d+',
        r'-p-\d+',
    ]
    
    for pattern in patterns:
        if re.search(pattern, href):
            return True
    
    return False


def collect_product_urls(driver, search_term, max_links):
    """Collect product URLs for a search term"""
    url = f"https://www.trendyol.com/sr?q={search_term}"
    driver.get(url)
    time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"Collecting: {search_term}")
    print(f"{'='*60}")
    
    product_urls = set()
    scroll_attempts = 0
    last_count = 0
    no_new_urls_count = 0
    
    while len(product_urls) < max_links and scroll_attempts < MAX_SCROLL_ATTEMPTS:
        # Find all links on page
        all_anchors = driver.find_elements(By.TAG_NAME, "a")
        
        for anchor in all_anchors:
            try:
                href = anchor.get_attribute("href")
                
                if is_product_url(href):
                    # Clean URL (remove query params)
                    clean_url = href.split('?')[0]
                    product_urls.add(clean_url)
                    
                    if len(product_urls) >= max_links:
                        break
            except:
                continue
        
        current_count = len(product_urls)
        print(f"  Scroll {scroll_attempts + 1:2d}: Found {current_count:4d} URLs", end='')
        
        # Check if we're getting new URLs
        if current_count == last_count:
            no_new_urls_count += 1
            print(" (no new URLs)")
            
            # If no new URLs for 3 consecutive scrolls, stop
            if no_new_urls_count >= 3:
                print(f"  → Stopping: No new URLs found")
                break
        else:
            no_new_urls_count = 0
            new_urls = current_count - last_count
            print(f" (+{new_urls} new)")
        
        last_count = current_count
        
        if current_count >= max_links:
            print(f"  → Target reached: {max_links} URLs")
            break
        
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Try to trigger lazy loading
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", all_anchors[-1])
        except:
            pass
        
        time.sleep(1)
        scroll_attempts += 1
    
    print(f"\n  ✓ Collected {len(product_urls)} URLs for '{search_term}'")
    return list(product_urls)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "="*60)
    print("TRENDYOL PRODUCT URL COLLECTOR")
    print("="*60 + "\n")
    
    # Setup database
    setup_database(DATABASE_FILE)
    
    # Setup Selenium
    print("Setting up browser...")
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)
    
    # Accept cookies once
    print("Loading Trendyol...")
    driver.get("https://www.trendyol.com")
    accept_cookies(driver, wait)
    
    # Collect URLs for each search term
    total_collected = 0
    
    for i, search_term in enumerate(SEARCH_TERMS, 1):
        print(f"\n[{i}/{len(SEARCH_TERMS)}] Processing: {search_term}")
        
        try:
            # Collect URLs
            urls = collect_product_urls(driver, search_term, MAX_LINKS_PER_CATEGORY)
            
            # Save to database
            added = save_urls_batch(DATABASE_FILE, urls, search_term)
            total_collected += added
            
            print(f"  ✓ Saved {added} new URLs to database")
            
            # Small delay between categories
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ Error collecting {search_term}: {e}")
            continue
    
    # Cleanup
    driver.quit()
    
    # Show final statistics
    stats = get_stats(DATABASE_FILE)
    
    print("\n" + "="*60)
    print("COLLECTION COMPLETE!")
    print("="*60)
    print(f"Total URLs in database: {stats['total']:,}")
    print(f"New URLs added: {total_collected:,}")
    print(f"\nURLs by category:")
    
    for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:15s}: {count:,}")
    
    print(f"\n✓ Database saved: {DATABASE_FILE}")
    print("="*60 + "\n")
    
    # Export sample to text file
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM product_urls LIMIT 100')
    sample_urls = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    with open('sample_urls.txt', 'w', encoding='utf-8') as f:
        for url in sample_urls:
            f.write(url + '\n')
    
    print("✓ Sample URLs saved to: sample_urls.txt\n")


if __name__ == "__main__":
    main()
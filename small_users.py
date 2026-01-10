"""
FAST Single-Session Seller Scraper
NO DATABASE | NO PARALLEL PROCESSING
Sequential, optimized scraping using one browser session
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import traceback
from datetime import datetime


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

PRODUCT_URLS = [
    "https://www.trendyol.com/kitchen-queen-home/katlanir-kovali-turuncu-mob-55-cm-kendinden-sikmali-mop-p-900924946",
    "https://www.trendyol.com/agarta/dogal-el-yapimi-bebek-sabunu-150-gr-p-31326231",
    "https://www.trendyol.com/tudors/unisex-slim-fit-dar-kesim-100-pamuk-yumusak-dokulu-siyah-bisiklet-yaka-tisort-p-819588224",
    "https://www.trendyol.com/jbl/tune-525bt-beyaz-multi-connect-wireless-kulak-ustu-kulaklik-p-901305992",
    "https://www.trendyol.com/bgk/5-cift-surat-ifade-desenli-cocuk-corap-p-803414049",
    "https://www.trendyol.com/zuhre-ana/bromelain-ananas-iceren-detox-surubu-p-796088323",
    "https://www.trendyol.com/kiperin/100-saf-ve-dogal-yuksek-biyoaktif-cift-hidrolize-kolajen-peptitler-iceren-diyet-takviyesi-300gr-p-1047194157",
    "https://www.trendyol.com/embeauty/ultra-siyah-dolgunlastirici-maskara-hacim-ve-uzunluk-etkili-p-1016742922",
    "https://www.trendyol.com/lollis/real-look-mascara-with-keratin-keratin-icerikli-real-look-maskara-rimel-p-71180067",
    "https://www.trendyol.com/kenko/pomodoro-ogrenci-saati-kronometreli-ders-calisma-saati-dijital-masa-saati-p-57736809",
    "https://www.trendyol.com/farkli-bi-kagit/56x110cm-turkiye-haritasi-akilli-kagit-pratik-tutunabilir-seffaf-tahta-p-240990191",
    "https://www.trendyol.com/sherlocked/gez-kazi-magnet-turkiye-haritasi-kazinabilir-harita-gezkazi-turkiye-haritasi-magnet-p-945476156"
]


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

def process_product(driver, wait, product_url, is_first=False):
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

        seller_email = safe_extract(driver, [
            "//td[contains(text(), 'KEP')]/following-sibling::td",
            "//strong[contains(text(), 'KEP')]/ancestor::tr/td[last()]",
            "//*[contains(text(), '@kep.tr')]",
            "//*[contains(text(), '@')]"
        ])

        return {
            "Product URL": product_url,
            "Seller Name": seller_name,
            "Seller Phone": seller_phone,
            "Seller Email": seller_email,
            "Success": True
        }

    except Exception as e:
        return {
            "Product URL": product_url,
            "Seller Name": "Error",
            "Seller Phone": "Error",
            "Seller Email": "Error",
            "Success": False,
            "Error": str(e)[:200]
        }


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    print("\nFAST SINGLE-SESSION SELLER SCRAPER\n")

    driver = setup_driver()
    wait = WebDriverWait(driver, 20)

    results = []
    start_time = time.time()

    for i, url in enumerate(PRODUCT_URLS, 1):
        print(f"[{i}/{len(PRODUCT_URLS)}] Processing: {url[:70]}...")
        product_start = time.time()

        data = process_product(driver, wait, url, is_first=(i == 1))
        results.append(data)

        elapsed = time.time() - product_start
        status = "✓" if data["Success"] else "✗"
        print(f"  {status} Done in {elapsed:.1f}s | Seller: {data.get('Seller Name')}")

    driver.quit()

    # -------------------------------------------------
    # SAVE TO EXCEL
    # -------------------------------------------------

    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"seller_data_{timestamp}.xlsx"
    df.to_excel(output_file, index=False)

    total_time = time.time() - start_time

    print("\nPROCESSING COMPLETE")
    print(f"Total Products: {len(PRODUCT_URLS)}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"Average: {total_time/len(PRODUCT_URLS):.1f}s/product")
    print(f"Saved to: {output_file}\n")


if __name__ == "__main__":
    main()

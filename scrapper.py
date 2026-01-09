from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import traceback

# -------------------------------------------------
# 1. PRODUCT LIST (ADD LINKS HERE)
# -------------------------------------------------
PRODUCT_URLS = [
    "https://www.trendyol.com/kitchen-queen-home/katlanir-kovali-turuncu-mob-55-cm-kendinden-sikmali-mop-p-900924946",
    "https://www.trendyol.com/agarta/dogal-el-yapimi-bebek-sabunu-150-gr-p-31326231",
    "https://www.trendyol.com/tudors/unisex-slim-fit-dar-kesim-100-pamuk-yumusak-dokulu-siyah-bisiklet-yaka-tisort-p-819588224",
    "https://www.trendyol.com/jbl/tune-525bt-beyaz-multi-connect-wireless-kulak-ustu-kulaklik-p-901305992",
    "https://www.trendyol.com/bgk/5-cift-surat-ifade-desenli-cocuk-corap-p-803414049"
]

# -------------------------------------------------
# 2. DRIVER SETUP
# -------------------------------------------------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(r"--user-data-dir=C:\selenium_profiles\trendyol")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 30)

# -------------------------------------------------
# 3. SAFE EXTRACT HELPER
# -------------------------------------------------
def safe_extract(xpath_list, field_name):
    for xpath in xpath_list:
        try:
            element = driver.find_element(By.XPATH, xpath)
            value = element.text.strip()
            if value and value != ":" and len(value) > 1:
                return value
        except:
            continue
    return "Not found"

# -------------------------------------------------
# 4. PROCESS SINGLE PRODUCT
# -------------------------------------------------
def process_product(product_url):
    print(f"\nProcessing: {product_url}")

    try:
        driver.get(product_url)

        # Reject cookies if present
        try:
            reject_btn = wait.until(
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
            EC.presence_of_element_located(
                (By.XPATH, "//button[.//span[normalize-space()='Şimdi Al'] or normalize-space()='Şimdi Al']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", buy_now_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", buy_now_btn)

        # Wait checkout
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Sipariş') or contains(text(),'Özet')]")
            )
        )

        # Open distance sales contract
        contract = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Mesafeli Satış Sözleşmesi')]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", contract)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", contract)

        time.sleep(2)

        # -------------------------------------------------
        # EXTRACT DATA (ONLY REQUIRED FIELDS)
        # -------------------------------------------------
        seller_name = safe_extract([
            "//strong[contains(text(), 'Ticaret Unvanı')]/ancestor::tr/td[last()]",
            "//td[contains(text(), 'Ticaret Unvanı')]/following-sibling::td"
        ], "Seller Name")

        seller_phone = safe_extract([
            "//strong[contains(text(), 'Satıcının Telefonu')]/ancestor::tr/td[last()]",
            "//td[contains(text(), 'Telefon')]/following-sibling::td"
        ], "Seller Phone")

        # Fixed: Extract email from KEP section
        seller_email = safe_extract([
            "//td[contains(text(), 'KEP') and contains(text(), 'E-posta')]/following-sibling::td",
            "//strong[contains(text(), 'KEP')]/ancestor::tr/td[last()]",
            "//*[contains(text(), '@kep.tr')]",
            "//*[contains(text(), '@hs')]"
        ], "Seller Email")

        return {
            "Product Link": product_url,
            "Seller Name": seller_name,
            "Seller Phone": seller_phone,
            "Seller Email": seller_email
        }

    except Exception as e:
        print("Failed:", product_url)
        traceback.print_exc()
        return None

# -------------------------------------------------
# 5. LOOP THROUGH ALL PRODUCTS
# -------------------------------------------------
results = []

for url in PRODUCT_URLS:
    data = process_product(url)
    if data:
        results.append(data)

# -------------------------------------------------
# 6. WRITE RESULTS TO FILE
# -------------------------------------------------
with open("seller_data.txt", "w", encoding="utf-8") as f:
    for item in results:
        f.write("====================================\n")
        f.write(f"Product Link: {item['Product Link']}\n")
        f.write(f"Seller Name: {item['Seller Name']}\n")
        f.write(f"Seller Phone: {item['Seller Phone']}\n")
        f.write(f"Seller Email: {item['Seller Email']}\n")
        f.write("====================================\n\n")

print(f"\nCompleted. Extracted data for {len(results)} products.")
print("Saved to seller_data.txt")

input("Press ENTER to close browser...")
driver.quit()
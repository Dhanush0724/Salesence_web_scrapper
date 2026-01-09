from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

PRODUCT_URL = "https://www.trendyol.com/kitchen-queen-home/katlanir-kovali-turuncu-mob-55-cm-kendinden-sikmali-mop-p-900924946"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Persistent profile (login stays)
options.add_argument(r"--user-data-dir=C:\selenium_profiles\trendyol")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 30)

try:
    # -------------------------------------------------
    # 1. OPEN PRODUCT PAGE
    # -------------------------------------------------
    driver.get(PRODUCT_URL)
    print("Product page loaded.")

    # -------------------------------------------------
    # 2. REJECT COOKIES (IF PRESENT)
    # -------------------------------------------------
    try:
        reject_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Reddet') or contains(., 'Reject')]")
            )
        )
        reject_btn.click()
        time.sleep(1)
        print("Cookies rejected.")
    except:
        print("No cookie popup.")

    # -------------------------------------------------
    # 3. REMOVE ONBOARDING OVERLAY
    # -------------------------------------------------
    driver.execute_script("""
        const overlay = document.querySelector('[data-testid="overlay"]');
        if (overlay) overlay.remove();
    """)
    print("Onboarding overlay cleared.")

    # -------------------------------------------------
    # 4. CLICK BUY NOW (ŞİMDİ AL)
    # -------------------------------------------------
    buy_now_btn = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//button[.//span[normalize-space()='Şimdi Al'] or normalize-space()='Şimdi Al']"
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        buy_now_btn
    )
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", buy_now_btn)
    print("Buy Now clicked.")

    # -------------------------------------------------
    # 5. WAIT FOR CHECKOUT PAGE
    # -------------------------------------------------
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Sipariş') or contains(text(),'Özet')]")
        )
    )
    print("Checkout page loaded.")

    # -------------------------------------------------
    # 6. CLICK MESAFELİ SATIŞ SÖZLEŞMESİ (TEXT ONLY)
    # -------------------------------------------------
    distance_sales_text = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Mesafeli Satış Sözleşmesi')]")
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        distance_sales_text
    )
    time.sleep(0.5)

    driver.execute_script(
        "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));",
        distance_sales_text
    )
    print("Mesafeli Satış Sözleşmesi opened.")

    # -------------------------------------------------
    # 7. WAIT FOR MODAL TO APPEAR (NO IFRAME SWITCH!)
    # -------------------------------------------------
    time.sleep(2)

    # Wait for the modal content to be visible
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'p-contracts-modal')]")
        )
    )
    print("Contract modal is visible.")

    # -------------------------------------------------
    # 8. WAIT FOR SELLER INFORMATION TO LOAD
    # -------------------------------------------------
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//strong[text()='Satıcının Ticaret Unvanı / Adı ve Soyadı']")
        )
    )
    print("Seller information loaded in modal.")

    # -------------------------------------------------
    # 9. EXTRACT SELLER DATA (NO IFRAME - MAIN DOCUMENT)
    # -------------------------------------------------
    print("\n========= EXTRACTING SELLER DETAILS =========")
    
    # Helper function to safely extract text
    def safe_extract(xpath_expr, field_name):
        try:
            element = driver.find_element(By.XPATH, xpath_expr)
            value = element.text.strip()
            print(f"{field_name}: {value}")
            return value
        except Exception as e:
            print(f"{field_name}: Not found")
            return "Not found"

    # Extract Seller Name
    seller_name = safe_extract(
        "//strong[text()='Satıcının Ticaret Unvanı / Adı ve Soyadı']/parent::td/following-sibling::td[last()]",
        "Seller Name"
    )

    # Extract Seller Address
    seller_address = safe_extract(
        "//strong[text()='Satıcının Adresi']/parent::td/following-sibling::td[last()]",
        "Seller Address"
    )

    # Extract Seller Phone
    seller_phone = safe_extract(
        "//strong[text()='Satıcının Telefonu']/parent::td/following-sibling::td[last()]",
        "Seller Phone"
    )

    # Extract Product Name
    product_name = safe_extract(
        "//th[text()='Ürün/Hizmet Açıklaması']/ancestor::table//tbody/tr[1]/td[1]",
        "Product Name"
    )

    # Extract Tax ID
    seller_tax_id = safe_extract(
        "//strong[text()='Satıcının Vergi Kimlik Numarası']/parent::td/following-sibling::td[last()]",
        "Seller Tax ID"
    )

    # Extract Email
    seller_email = safe_extract(
        "//strong[text()='Satıcı KEP ve E-posta Bilgileri']/parent::td/following-sibling::td[last()]",
        "Seller Email"
    )

    print("=============================================\n")

    # -------------------------------------------------
    # 10. PRINT FINAL RESULTS
    # -------------------------------------------------
    print("\n========= FINAL EXTRACTED DETAILS =========")
    print(f"Product Name   : {product_name}")
    print(f"Seller Name    : {seller_name}")
    print(f"Seller Address : {seller_address}")
    print(f"Seller Phone   : {seller_phone}")
    print(f"Seller Tax ID  : {seller_tax_id}")
    print(f"Seller Email   : {seller_email}")
    print("==========================================\n")

    # -------------------------------------------------
    # 11. STOP – KEEP BROWSER OPEN
    # -------------------------------------------------
    input("Press ENTER to close browser...")

except Exception as e:
    print("Unexpected error:", e)
    import traceback
    traceback.print_exc()
    
    # Save screenshot for debugging
    try:
        driver.save_screenshot("error_screenshot.png")
        print("Error screenshot saved as 'error_screenshot.png'")
    except:
        pass
    
    input("Press ENTER to close browser...")
finally:
    # Optionally close the driver
    # driver.quit()
    pass
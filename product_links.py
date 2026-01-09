from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

START_URL = "https://www.trendyol.com/sr?q=elbise"
MAX_LINKS = 10

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 30)
driver.get(START_URL)

# -------------------------
# ACCEPT COOKIES (OPTIONAL)
# -------------------------
try:
    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Kabul') or contains(text(),'Accept')]")
        )
    ).click()
except:
    pass

# -------------------------
# WAIT FOR *ANY* PRODUCT LINK
# -------------------------
wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//a[contains(@href,'/p-')]")
    )
)

print("Product links detected in DOM.")

product_links = set()

while len(product_links) < MAX_LINKS:
    anchors = driver.find_elements(
        By.XPATH, "//a[contains(@href,'/p-')]"
    )

    print(f"Anchors found: {len(anchors)}")

    for a in anchors:
        href = a.get_attribute("href")
        if href and "trendyol.com" in href:
            product_links.add(href)
            if len(product_links) >= MAX_LINKS:
                break

    driver.execute_script("window.scrollBy(0, 1200);")
    time.sleep(2)

driver.quit()

with open("trendyol_product_links.txt", "w", encoding="utf-8") as f:
    for link in product_links:
        f.write(link + "\n")

print(f"Collected {len(product_links)} product links.")

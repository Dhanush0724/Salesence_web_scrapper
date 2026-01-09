from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()

# IMPORTANT: persistent profile
options.add_argument(r"--user-data-dir=C:\selenium_profiles\trendyol")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Open Trendyol
driver.get("https://www.trendyol.com")

print("Browser is open.")
print("👉 LOGIN MANUALLY NOW.")
print("👉 After login is complete, come back to terminal.")

# BLOCK SCRIPT — DO NOT REMOVE
input("Press ENTER here ONLY AFTER you have logged in...")

# Do NOT call driver.quit()
print("You can now close the browser manually using X.")

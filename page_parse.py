"""
Uses classes for classes, where a class a scraper method that gets the relevant data from https://asen-jhu.evaluationkit.com/Report/Public/Results
"""

import time
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import urllib.parse
import re


def parse_period(period_string: str) -> str:
    """Processes period_string to ensure consistency

    Args:
        period_string (str): unparsed string

    Raises:
        ValueError: It should fit into one of the 4 periods, if not this is raised.

    Returns:
        str: 'SP'--spring, 'FA'--fall, 'IN'--intersession, 'SU'--summer
    """
    period_string = period_string.lower().strip()
    if period_string == 'sp' or period_string == 'spring':
        return 'SP'
    if period_string == 'fa' or period_string == 'fall':
        return 'FA'
    if period_string == 'in' or period_string == 'intersession':
        return 'IN'
    if period_string == 'su' or period_string == 'summer':
        return 'SU'
    raise ValueError(f'Period String, "{period_string}" should be spring, fall, intersession, or summer')


def parse_year(year_string: str) -> int:
    """Processes year_string to ensure consistency

    Args:
        year_string (str): unparsed string

    Raises:
        ValueError: It should be a valid year, if not this is raised.

    Returns:
        int: integer of year (00 <= year < 100) 
    """
    year_string = year_string.strip()
    if re.match(r"^\d{4}$", year_string):
        return int(year_string) - 2000
    else:
        if re.match(r"^\d{1,2}$", year_string):
            return int(year_string)
        else:
            raise ValueError(f'Year, "{year_string}" is not valid')



def parse_section(section_string: str) -> int:
    """Processes section_string to ensure consistency

    Args:
        section_string (str): unparsed string

    Raises:
        ValueError: It should be a 1-2 digit integer, if not this is raised.

    Returns:
        int: integer of section (00 <= section < 100) 
    """
    if re.match(r"^\d{1,2}$", section_string.strip()):
        return int(section_string)
    else:
        raise ValueError(f'Section, "{section_string}" is not valid')


class SpecificClassScraper():
    """
    holds information of a specific class, and has a method to scrape the data for that class
    """
    def __init__(self, class_code: str, period_string: str, year_string: str, section_string: str):
        pattern = r'^[a-z]{2}\.\d{3}\.\d{3}$'
        if not re.match(pattern, class_code.lower().strip()):
            raise ValueError(f"{class_code} is a invalid class code (should be XX.###.###)")
        
        period = parse_period(period_string)
        year = parse_year(year_string)
        section = parse_section(section_string)
        # at this point, the variables we care about are year, period, section, and class_code, here's how we use them:
        self.specific_class_code = f'{class_code}.{section:02}.{period}{year:02}'

    def scrape_pdf(self):
        from seleniumwire import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        import requests
        import re

        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # optional: remove comment to see browser
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=chrome_options)

        try:
            url = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
            driver.get(url)

            WebDriverWait(driver, 10).until(EC.url_contains("Report/Public"))
            search_input = driver.find_element(By.ID, "Course")
            search_input.send_keys(self.specific_class_code)
            search_input.submit()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.sr-pdf")))
            pdf_button = driver.find_element(By.CSS_SELECTOR, "a.sr-pdf")
            pdf_button.click()

            time.sleep(3)

            for request in driver.requests:
                if (
                    request.response
                    and "Report/Public/Pdf" in request.url
                    and request.response.status_code == 200
                ):
                    print("✅ Found PDF URL:", request.url)
                    response = requests.get(request.url)
                    if response.status_code == 200:
                        file_name = f"{self.specific_class_code.replace('.', '_')}.pdf"
                        with open(file_name, 'wb') as f:
                            f.write(response.content)
                        print(f"Downloaded PDF as {file_name}")
                        return file_name
                    else:
                        print("❌ Failed to download PDF.")
                        return None

            print("❌ No PDF URL found.")
            return None

        finally:
            driver.quit()
            

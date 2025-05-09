"""
Uses classes for classes, where a class a scraper method that gets the relevant data from https://asen-jhu.evaluationkit.com/Report/Public/Results
"""

from datetime import datetime
import json
import os
import time
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import urllib.parse
import re
from CourseCache import CourseCache

import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)  # to avoid some annoying text being printed: "CropBox missing from /Page, defaulting to MediaBox"
import pdfplumber



def _parse_period(period_string: str, expecting_special=False) -> str:
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
        if expecting_special:
            raise ValueError(f'Special period string, "{period_string}" should be intersession or summer')
        return 'SP'
    if period_string == 'fa' or period_string == 'fall':
        if expecting_special:
            raise ValueError(f'Special period string, "{period_string}" should be intersession or summer')
        return 'FA'
    if period_string == 'in' or period_string == 'intersession':
        return 'IN'
    if period_string == 'su' or period_string == 'summer':
        return 'SU'
    if expecting_special:
        raise ValueError(f'Special period string, "{period_string}" should be intersession or summer')
    raise ValueError(f'Period String, "{period_string}" should be spring, fall, intersession, or summer')


def _parse_year(year_string: str) -> int:
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



def _parse_section(section_string: str) -> int:
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
    def __init__(self, class_code: str, period_string: str, year_string: str, section_string: str, course_cache: CourseCache=None):

        pattern = r'^[a-z]{2}\.\d{3}\.\d{3}$'
        if not re.match(pattern, class_code.lower().strip()):
            raise ValueError(f"{class_code} is a invalid class code (should be XX.###.###)")
        
        period = _parse_period(period_string)
        year = _parse_year(year_string)
        section = _parse_section(section_string)
        
        # at this point, the variables we care about are year, period, section, and class_code, here's how we use them:
        self.specific_class_code = f'{class_code}.{section:02}.{period}{year:02}'

        self.pdf_file = None

        # The variables where pdf extracted data will be stored:
        self.course_name = ""
        self.instructor_name = ""
        self.overall_quality_frequency = {}
        self.instructor_effectiveness_frequency = {}
        self.intellectual_challenge_frequency = {}
        self.ta_frequency = {}
        self.ta_names = []  # List of names from question 5.
        self.feedback_frequency = {}
        self.workload_frequency = {}
        
        if course_cache is None:
            self.cache = CourseCache()
        else:
            self.cache = course_cache

        self.cache.ensure_course(course_code=class_code, period=f'{period}{year:02}')

    def scrape_pdf(self, driver):
        # print(f"Checking class code: {self.specific_class_code}:")
        pdf_url_holder = {"url": None}

        # 🛑 Intercept and block the PDF request before Chrome handles it
        def interceptor(request):
            if "Report/Public/Pdf" in request.url:
                # print("🚫 Blocking request to:", request.url)
                pdf_url_holder["url"] = request.url
                request.abort()  # <- prevent download

        driver.request_interceptor = interceptor

        # Check if driver is already on a 'Report/Public/Results' page
        if "Report/Public/Results" in driver.current_url:
            # Directly update the URL with the new course code
            new_url = f"https://asen-jhu.evaluationkit.com/Report/Public/Results?Course={self.specific_class_code}"
            driver.get(new_url)
            WebDriverWait(driver, 10).until(EC.url_contains("Report/Public/Results"))
        else:
            # Follow the original workflow
            url = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
            driver.get(url)

            WebDriverWait(driver, 10).until(EC.url_contains("Report/Public"))
            search_input = driver.find_element(By.ID, "Course")
            search_input.send_keys(self.specific_class_code)
            search_input.submit()

            WebDriverWait(driver, 10).until(EC.url_contains("Report/Public/Results"))
        
        # Check for 'no records found' alert
        try:
            no_results_alert = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-info")
            # print("❌ No records found for this search.")
            return None
        except:
            pass  # If the alert isn't found, continue as normal

        pdf_button = driver.find_element(By.CSS_SELECTOR, "a.sr-pdf")
        pdf_button.click()  # error here represents assumption that pdf button is there being false.

        # Give it a second to be intercepted
        WebDriverWait(driver, 10).until(lambda d: pdf_url_holder["url"] is not None)

        if pdf_url_holder["url"]:
            # print("✅ Found PDF URL:", pdf_url_holder["url"])
            response = requests.get(pdf_url_holder["url"])
            if response.status_code == 200:
                file_name = f"pdfs/{self.specific_class_code.replace('.', '_')}.pdf"
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded PDF as {file_name}")
                self.pdf_file = file_name
                return file_name
            else:
                print(f"❌ Failed to download PDF: {self.specific_class_code}")
                return False
        else:
            print(f"❌ No PDF URL intercepted: {self.specific_class_code}")
            return False

    def parse_pdf(self):
        # Open the PDF and extract full text from all pages.
        text = ""
        with pdfplumber.open(self.pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # Extract Course Name.
        # Looks for a line like: "Course: EN.553.291.03.FA24 : Linear Algebra and Differential Equations"
        course_match = re.search(r"\nCourse:\s*[^:]*:\s(.+)\n", text)
        if course_match:
            self.course_name = course_match.group(1).strip()

        # Extract Instructor Name.
        # This pattern assumes the instructor name appears on a line ending with "Instructor:"
        instructor_match = re.search(r"\nInstructor:\s(.+)\n", text)
        if instructor_match:
            self.instructor_name = instructor_match.group(1).strip()

        # Define helper function to get text of a question section.
        def get_section(header, text):
            header_pattern = re.escape(header)
            m = re.search(header_pattern, text)
            if m:
                start = m.end()
                # Look ahead for the next question header (a digit followed by " - ")
                m2 = re.search(r"\n\s*\d+\s*-\s", text[start:])
                if m2:
                    end = start + m2.start()
                    return text[start:end]
                else:
                    return text[start:]
            return ""

        # Helper function to extract a dictionary of frequencies for given valid labels
        # Looks for lines like "Label (x) frequency ..." and returns {Label: frequency, ...}
        def extract_frequency(section_text, valid_labels):
            freq = {}
            for label in valid_labels:
                # The regex looks for the label, then a parenthesized number, then spaces and the frequency number.
                pattern = re.escape(label) + r"\s*\(\d+\)\s+(\d+)"
                match = re.search(pattern, section_text)
                if match:
                    freq[label] = int(match.group(1))
                else:
                    freq[label] = 0
            return freq

        # Headers for each question
        q1_header = "1 - The overall quality of this course is:"
        q2_header = "2 - The instructor's teaching effectiveness is:"
        q3_header = "3 - The intellectual challenge of this course is:"
        q4_header = "4 - The teaching assistant for this course is:"
        q5_header = "5 - Please enter the name of the TA you evaluated in question 4:"
        q6_header = "6 - Feedback on my work for this course is useful:"
        q7_header = "7 - Compared to other Hopkins courses at this level, the workload for this course is:"

        # Get sections from the text.
        section_q1 = get_section(q1_header, text)
        section_q2 = get_section(q2_header, text)
        section_q3 = get_section(q3_header, text)
        section_q4 = get_section(q4_header, text)
        section_q5 = get_section(q5_header, text)
        section_q6 = get_section(q6_header, text)
        section_q7 = get_section(q7_header, text)

        # Define the valid labels (answer choices) you want to extract frequencies for.
        q1_labels = ["Poor", "Weak", "Satisfactory", "Good", "Excellent"]
        q2_labels = ["Poor", "Weak", "Satisfactory", "Good", "Excellent"]
        q3_labels = ["Poor", "Weak", "Satisfactory", "Good", "Excellent"]
        q4_labels = ["Poor", "Weak", "Satisfactory", "Good", "Excellent"]
        # For question 6, the response options are different.
        q6_labels = ["Disagree strongly", "Disagree somewhat", "Neither agree nor disagree", "Agree somewhat", "Agree strongly"]
        # For question 7, the response options are:
        q7_labels = ["Much lighter", "Somewhat lighter", "Typical", "Somewhat heavier", "Much heavier"]

        # Extract frequency dictionaries.
        self.overall_quality_frequency = extract_frequency(section_q1, q1_labels)
        self.instructor_effectiveness_frequency = extract_frequency(section_q2, q2_labels)
        self.intellectual_challenge_frequency = extract_frequency(section_q3, q3_labels)
        self.ta_frequency = extract_frequency(section_q4, q4_labels)
        self.feedback_frequency = extract_frequency(section_q6, q6_labels)
        self.workload_frequency = extract_frequency(section_q7, q7_labels)

        # Extract TA Names from question 5.
        # It is assumed that each TA name is on a separate line starting with a hyphen.
        self.ta_names = re.findall(r"-\s*(.+)", section_q5)
        self.ta_names = [name.strip() for name in self.ta_names if name.strip()]
        
        # Gather the extracted data into a dictionary.
        data = {
            "course_name": self.course_name,
            "instructor_name": self.instructor_name,
            "overall_quality_frequency": self.overall_quality_frequency,
            "instructor_effectiveness_frequency": self.instructor_effectiveness_frequency,
            "intellectual_challenge_frequency": self.intellectual_challenge_frequency,
            "ta_frequency": self.ta_frequency,
            "ta_names": self.ta_names,
            "feedback_frequency": self.feedback_frequency,
            "workload_frequency": self.workload_frequency
        }

        self.cache.data['.'.join(self.specific_class_code.split('.')[:3])]['data'][self.specific_class_code.split('.')[4]][self.specific_class_code] = data

        self.cache.save()

        os.remove(self.pdf_file)

        return self.cache



class GeneralClassScraper():
    """
    Contains SpecificClassScraper()s for all versions of a class in the last (default=5) years
    """   
    def __init__(self, class_code: str, course_cache: CourseCache=None, years=5, intersession=False, summer=False):
        if course_cache is None:
            self.cache = CourseCache()
        else:
            self.cache = course_cache

        self.years = years
        self.class_code = class_code

        now = datetime.now()
        self.last_year = now.year - 1
        self.last_period = 'FA'
        if now.month > 5:  # past may
            self.last_year += 1  # it will make last year actually this year, but that represents the "last year that we have data from"
            self.last_period = 'SP'
        
        self.date = self.last_period + str(self.last_year)[2:]

        self.cache.ensure_course(course_code=class_code)

        self.intersession = intersession
        self.summer = summer
        if intersession and summer:
            raise ValueError("Summer and Intersession do not go together")
        if intersession or summer:
            self.class_code += '|' + ('IN' if self.intersession else 'SU')

            self.cache.data[class_code]['metadata']['intersession'] = True if intersession else None
            self.cache.data[class_code]['metadata']['summer'] = True if summer else None

            if self.cache.data.get(self.class_code[:-3], False):
                self.cache.data[self.class_code[:-3]]['metadata']['intersession' if intersession else 'summer'] = self.class_code
        


    def scrape_all_pdfs(self):
        skip_first_semester = False
        if self.class_code in self.cache.data:
            course_entry = self.cache.data[self.class_code]

            last_date_gathered = course_entry['metadata']['last_period_gathered']
            if last_date_gathered == self.date:  # if the data is already gathered (at least for FA/SP)
                return self.cache.data[self.class_code]
            else:
                # essentially a ceiling operation, so if it's been 0.5 years (1 semester) since we collected data, we set self.years to 1.
                self.years = (self.last_year - 2000 - int(last_date_gathered[2:])) + int(self.last_period == 'FA' and last_date_gathered[:2] == 'SP')

                # then we will tell the later code to skip the first semester if ceil(years passed) = ((years passed) + 0.5):
                skip_first_semester = self.last_period != last_date_gathered[:2]
                course_entry['metadata']["last_period_gathered"] = self.date
                    

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        })
        driver = webdriver.Chrome(options=chrome_options)

        try:
            dates = []

            start_year = (self.last_year + 1) - self.years

            if self.intersession:
                # possible changes:
                # just search through sections and find it (slow, but not too many intersession courses and minimal work)
                # add separate functionality to let user input section so you don't have to search as much (much more work, annoying for user)
                dates = [("IN", year) for year in range(start_year, self.last_year + 1)]
            elif self.summer:
                spring_offset = -1 if self.last_period == 'SP' else 0
                summer_year_range = range(start_year + spring_offset, self.last_year + spring_offset + 1)
                dates = [("SU", year) for year in summer_year_range]
            else:
                if self.last_period == 'SP':
                    dates.append(('FA', start_year - 1))
                for year in range(start_year, self.last_year + 1):
                    for period in ['SP', 'FA']:
                        dates.append((period, year))
                if self.last_period == 'SP':
                    dates.pop()  # remove fall of last_year since it hasn't happened yet if last period is spring
            

            if skip_first_semester:
                dates.pop(0)  # only can happen when dealing with downloading new evaluations when old evaluations were already downloaded
            for period, year in dates:
                first = True
                for i in range(1, 100):
                    s = SpecificClassScraper(self.class_code.split('|')[0], period, str(year), str(i), self.cache)
                    result = s.scrape_pdf(driver)
                    if result is None:
                        if self.intersession or self.summer:
                            continue  # for special periods, we search through all 100
                        else:
                            break  # default behavior is we stop searching once we don't find a value
                    elif result is False:
                        self.cache.mark_failed(s.specific_class_code)
                        break  # manage_failed_downloads.py already deals with this well,
                               # so if it fails we fully stop this period, continue onwards in solve_simple_failures()
                    
                    self.cache = s.parse_pdf()

                    if first:  # first has 1 purposes: not add to relevant_periods multiple times
                        assert((period + str(year)[2:]) not in self.cache.data[self.class_code]['metadata']["relevant_periods"])  # should really never happen.
                        self.cache.data[self.class_code]['metadata']["relevant_periods"].append(period + str(year)[2:])
                        first = False
            self.cache.save()  # save runs even if they have no valid courses, to save the fact that we already checked that

        
        finally:
            driver.quit()
        
        return self.cache.data[self.class_code]  # will error if there is an exception, which is probably fine.

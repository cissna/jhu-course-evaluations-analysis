from page_parse import SpecificClassScraper
from CourseCache import CourseCache
from typing import List, Dict
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


def _find_courses_to_check_from_failed(cache: CourseCache) -> Dict[str, Dict[str, List[str]]]:

    specific_to_check = {}
    
    for course_code, course_entry in cache.data.items():
        metadata = course_entry['metadata']
        failed = metadata['failed_periods']
        if not failed:
            continue

        specific_to_check[course_code] = {}

        data = course_entry['data']
        for fail in failed:
            if fail in metadata['relevant_periods']:  # this means it failed in such a way that it "mark_failed" was called on it
            
                first_failed = min(key for key, value in data[fail].items() if value is None)

                section = int(first_failed.split('.')[3])
            else:
                # new case I added where the problem is that sections are initialized without the later code actually filling them in, so i leave them in failed until then
                section = 1

            # create list of first specific course codes (entire code embedded in dictionary keys) within the failed period to check (up to section 99)
            specific_to_check[course_code][fail] = [sec for sec in range(section, 100)]
            # [f'{course_code}.{sec:02d}.{fail}' for sec in range(section, 100)]

    return specific_to_check


def solve_simple_failures(cache: CourseCache=None) -> CourseCache:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    })
    driver = webdriver.Chrome(options=chrome_options)

    if cache is None:
        cache = CourseCache()

    d = _find_courses_to_check_from_failed(cache)

    for course_code, periods in d.items():
        for period, sections in periods.items():
            all_succeeded = True
            for sec in sections:
                s = SpecificClassScraper(course_code, period[:2], period[2:], str(sec), cache, True)
                result = s.scrape_pdf(driver)
                if result is None:
                    break
                elif result is False:
                    all_succeeded = False
                    cache.mark_failed(s.specific_class_code)
                    break
                
                cache = s.parse_pdf()
            
            if all_succeeded:
                cache.data[course_code]['metadata']['failed_periods'].remove(period)
                cache.save()

    return cache  # unecessary output because I think it updates in place but why not

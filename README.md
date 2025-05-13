# Previous Goal of this Repository:

1. Web scrape to download pdfs for a given class in a given semester
    - DONE!
2. Parse PDFs to get all relevant data
    - DONE!
3. Data analysis
    - Letting ChatGPT do it manually for now until I do something more robust
        - Note from the future: this was all I personally needed. Use of the data from here on out will be catered toward user.

# Future considerations:

1. Consider doing some sort of general data analysis once all relevant data for it is downloaded
2. Consider downloading summer/interesession in bulk using a different method to shorten times from ~30 minutes to ~1 minute per course
3. Build cissna.github.io into an interface where students enter a course code to get comprehensive data and also input what analysis they want done.
#3 is most important!


# Description of the Codebase, as of 5/13/25:
- cache.json
    - Data I've collected thus far. This is as much a place to store data as it is a tool to help me safetly collect more in the future.
        - That is, I have a lot of unnecessary things that are useful to me——metadata telling me whether a download has failed, empty data dictionaries telling me that, even though I tried, there was nothing to be downloaded for a given course code, and |SU or |IN appended to cache entries corresponding to summer or interesession codes (which could and should (later) be combined with the fall/spring entries for the same code).
        - See page_parse.py for more info on what/how data is downloaded.
    - Metadata:
        - failed_periods — internal for keeping track
        - first_period_gathered, last_period_gathered — self explanatory, can be used for looping and to verify that all periods attempted were downloaded.
        - relevant_periods — list of periods with data between the above.
        - intersession/summer — course code if there is a (respectively, summer or intersession) course associated with the same course code that downloaded without the interesession/summer expectation. otherwise true if it *is* summer/interesession data (should also be in the course code), else null.
- page_parse.py
    - Bulk of all code, probably too bulky actually.
    - Contains SpecificClassScraper and GeneralClassScraper
        - SpecificClassScraper is actually very robust, all it does it takes in a code to search, a period, a year, and a section and it can download the corresponding PDF (or return None if n/a) with scrape_pdf(). Then, it can parse the text with parse_pdf(), which will also ensure the course is in the cache, and add it to the appropriate location in the cache. Returns False (not None) if there is an error, and prints an error message.
        - GeneralClassScraper is quite messy, but basically the main goal is to input a course code and create an entire cache entry that logs the last (default=5) years, and return the relevant cache entry for the user. It will also return the cache entry if it's already stored, and if it's already stored but out of date, it will update the cache and return the new entry. There is also functionality to deal with intersession or summer courses, which are not downloaded for a course code by defailt (only fall/spring), although in it's current state it's unusubly slow, due to the fact that I download courses by section but, whereas spring/fall courses have consecutive sections starting at 1, intersession/summer have unpredictable section numbers. This could be circumvented by downloading by only searching the department number (XX.### out of XX.###.###.##.IN/SU##). 
            - Confusing note—if no data is downloaded, GeneralClassScraper leaves an empty entry, however SpecificClassScraper does not if the section it searches for fails, it only saves to the cache after successes.
- CourseCache.py
    - Very nice class (thanks ChatGPT) that manages the course cache, by default "cache.json"
        - mark_failed is the only actual complicated functionality, not really just a wrapper.
        - Ensure course makes it easy to be defaultdict-like
- manage_failed_downloads.p
    - Using the failed metadata in CourseCache, it does solve_simple_failures() to just rerun the download starting from the place it failed onwards. Ostensibly, it could fail in other ways, but since solve_simple_failures() hasn't *not* fixed something yet, I'm not doing anything more complicated.
        - However, the file exists so if anything does come up, I can
            - The reason I thought it would is after seeing that some COVID neuro labs had multiple evals for one section, which I thought broke the code. However, it did not, so I'm fine with just downloading the first one and ignoring the second.
- main.py and unimportant_files/
    - Simple data analysis and actual instantiation of GeneralClassScraper() so data can be downloaded.
    - In the future, the main functionality will be through a website.
# Previous Goal of this repo:

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


# Actual Description of the codebase in its current form:
- cache.json
- CourseCache.py
- manage_failed_downloads.p
- main.py and unimportant_files/
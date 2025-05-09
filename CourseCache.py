import json
import os
from datetime import datetime

class CourseCache:
    def __init__(self, path="cache.json", years=5):
        self.path = path
        self.periods = self._generate_periods(years)
        self.data = self._load()

    def _generate_periods(self, years):
        now = datetime.now()

        # Determine final period
        last_year = now.year - 1
        last_period = "FA"
        if now.month > 5:  # After May, consider SP of this year to be included
            last_year += 1
            last_period = "SP"

        # Build list of all periods going backward
        seasons = ["SP", "FA"]
        all_periods = []
        total_periods = 2 * years
        while len(all_periods) < total_periods:
            for season in reversed(seasons):  # FA, then SP (so newer first)
                if len(all_periods) < total_periods:
                    all_periods.insert(0, f"{season}{str(last_year)[2:]}")
            last_year -= 1

        return all_periods

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get_course(self, course_code):
        return self.data.get(course_code, None)

    def ensure_course(self, course_code, period=None):
        if course_code not in self.data:
            self.data[course_code] = {
                "metadata": {
                    "failed_periods": [],
                    "first_period_gathered": self.periods[0],
                    "last_period_gathered": self.periods[-1],
                    "relevant_periods": [],
                    "intersession": None,
                    "summer": None
                },
                "data": {p: {} for p in self.periods if p == period}  # let the period be generated as you go
            }
        elif period is not None and period not in self.data[course_code]['data']:
            self.data[course_code]['data'][period] = {}

    def mark_failed(self, full_code, intersession=False, summer=False):
        assert(not (intersession and summer))
        period = full_code.split(".")[4]
        general = ".".join(full_code.split(".")[:3]) + ("|IN" if intersession else ("|SU" if summer else ""))
        self.ensure_course(general)
        self.data[general]["data"].setdefault(period, {})
        self.data[general]["data"][period][full_code] = None

        md = self.data[general]["metadata"]
        if period not in md["failed_periods"]:
            md["failed_periods"].append(period)
        if period not in md["relevant_periods"]:
            md["relevant_periods"].append(period)


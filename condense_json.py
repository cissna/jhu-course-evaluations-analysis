import os
import json
from collections import defaultdict

input_dir = "data"
output_file = "cache.json"

# Define all academic periods between SP20 and FA24
seasons = ["SP", "FA"]
years = list(range(2020, 2025))
all_periods = [f"{season}{str(year)[-2:]}" for year in years for season in seasons]

cache = {}

for i, filename in enumerate(os.listdir(input_dir)):
    filepath = os.path.join(input_dir, filename)
    if not os.path.isfile(filepath):
        continue

    parts = filename.split(".")
    if len(parts) < 4:
        print(f"Skipping malformed filename: {filename}")
        continue

    general_course = ".".join(parts[:3])  # e.g. EN.601.490
    period = parts[-1]                   # e.g. FA21

    if period not in all_periods:
        print(f"Skipping unknown period in filename: {filename}")
        continue

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {filename}: {e}")
        continue

    # Initialize structure if new course
    if general_course not in cache:
        cache[general_course] = {
            "metadata": {
                "failed_periods": [],
                "first_period_gathered": "SP20",
                "last_period_gathered": "FA24",
                "relevant_periods": []
            },
            "data": {p: {} for p in all_periods}
        }

    # Add data under correct period + full section filename
    cache[general_course]["data"][period][filename] = data
    cache[general_course]["metadata"]["relevant_periods"].append(period)

# Save to cache.json
with open(output_file, "w") as f:
    json.dump(cache, f, indent=2)

print(f"✅ Generated {output_file} with {len(cache)} courses.")

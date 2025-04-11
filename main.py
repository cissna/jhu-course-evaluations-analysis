import json
import os
from page_parse import GeneralClassScraper

code = """
AS.150.499
""".strip()

# Define the mappings from rating labels to numeric scores.
quality_mapping = {
    "Poor": 1,
    "Weak": 2,
    "Satisfactory": 3,
    "Good": 4,
    "Excellent": 5
}
workload_mapping = {
    "Much lighter": 1,
    "Somewhat lighter": 2,
    "Typical": 3,
    "Somewhat heavier": 4,
    "Much heavier": 5
}

# Function to parse a term string into a comparable tuple.
def parse_term(term_str):
    # We assume the term string is of the form XXYY
    # where "XX" is the term code (e.g. SP, FA, etc.)
    # and "YY" are the last two digits of the year.
    season_priority = {"SP": 1, "SU": 2, "FA": 3, "WI": 4}  # adjust if needed
    season = term_str[:2]
    year = int(term_str[2:])
    return (year, season_priority.get(season, 0))

# Function to compute the weighted sum and count from a frequency dict.
def aggregate_frequency(freq, mapping):
    total_count = sum(freq.values())
    weighted_sum = sum(mapping.get(resp, 0) * count for resp, count in freq.items())
    return weighted_sum, total_count

# This helper will compute an average from (weighted_sum, count) if count > 0.
def compute_avg(sum_count_pair):
    s, count = sum_count_pair
    return s / count if count else None

# Define cutoff for recent evaluations: files with term >= Spring 2023 (i.e., term code "SP23" or later)
cutoff_term = (23, 1)  # (year, season_order), where Spring is given priority 1

# Assume that you have a scraper instance 'g' that returns a list of file names.
# For example: "data/EN.553.420.04.FA24"
g = GeneralClassScraper(code)
file_list = g.scrape_all_pdfs()  # returns list of file paths like "data/EN.553.420.04.FA24"

# Create aggregation dictionaries.
# Each instructor will have two sets of aggregates ("all" and "recent") for both quality and workload.
instructor_data = {}
# Also aggregate for the overall course (i.e. combining all files)
overall_data_all   = {"quality": [0, 0], "workload": [0, 0]}   # [weighted_sum, total_count]
overall_data_recent = {"quality": [0, 0], "workload": [0, 0]}

for file in file_list:
    # The file name is expected to have the format:
    # data/[class code].[section].[date]
    # Example: "data/EN.553.420.04.FA24"
    # Strip the "data/" prefix and split based on '.'.
    fname = file.replace("data/", "")
    parts = fname.split(".")
    # The date is the last part (e.g. "FA24")
    date_code = parts[-1]
    file_term = parse_term(date_code)
    is_recent = (file_term >= cutoff_term)
    
    # Load the JSON data from the file.
    with open(file, 'r') as f:
        data = json.load(f)
    
    # Get the instructor name (if missing or empty, use "Unknown").
    instructor = data.get("instructor_name", "").strip() or "Unknown"
    
    # Get the frequency distributions.
    quality_freq = data.get("overall_quality_frequency", {})
    workload_freq = data.get("workload_frequency", {})
    
    # Compute the weighted sums and response counts.
    quality_sum, quality_count = aggregate_frequency(quality_freq, quality_mapping)
    workload_sum, workload_count = aggregate_frequency(workload_freq, workload_mapping)
    
    # Initialize aggregation for this instructor if not seen yet.
    if instructor not in instructor_data:
        instructor_data[instructor] = {
            "all": {"quality": [0, 0], "workload": [0, 0]},
            "recent": {"quality": [0, 0], "workload": [0, 0]}
        }
    # Update "all time" aggregator for this instructor.
    instructor_data[instructor]["all"]["quality"][0] += quality_sum
    instructor_data[instructor]["all"]["quality"][1] += quality_count
    instructor_data[instructor]["all"]["workload"][0] += workload_sum
    instructor_data[instructor]["all"]["workload"][1] += workload_count

    # Also update overall (class-wide) aggregator for "all" data.
    overall_data_all["quality"][0] += quality_sum
    overall_data_all["quality"][1] += quality_count
    overall_data_all["workload"][0] += workload_sum
    overall_data_all["workload"][1] += workload_count
    
    # If the file qualifies as recent (>= SP23), update the "recent" aggregates.
    if is_recent:
        instructor_data[instructor]["recent"]["quality"][0] += quality_sum
        instructor_data[instructor]["recent"]["quality"][1] += quality_count
        instructor_data[instructor]["recent"]["workload"][0] += workload_sum
        instructor_data[instructor]["recent"]["workload"][1] += workload_count

        overall_data_recent["quality"][0] += quality_sum
        overall_data_recent["quality"][1] += quality_count
        overall_data_recent["workload"][0] += workload_sum
        overall_data_recent["workload"][1] += workload_count
if (not file_list):
    print(f"No files found for {code}")
    exit()

print(f"\n\nClass: {data.get('course_name')}    Code: {code}\n\n")

# Print the aggregated averages.
print("Averages per instructor:")
for instructor, stats in instructor_data.items():
    all_quality_avg = compute_avg(stats["all"]["quality"])
    all_workload_avg = compute_avg(stats["all"]["workload"])
    recent_quality_avg = compute_avg(stats["recent"]["quality"])
    recent_workload_avg = compute_avg(stats["recent"]["workload"])
    
    print(f"\nInstructor: {instructor}")
    print(f"  All Time: Quality Average = {all_quality_avg:.2f}, Workload Average = {all_workload_avg:.2f}")
    if stats["recent"]["quality"][1] > 0:
        print(f"  Recent:   Quality Average = {recent_quality_avg:.2f}, Workload Average = {recent_workload_avg:.2f}")
    else:
        print("  Recent:   No recent evaluation data.")

# Compute and print overall class averages.
overall_all_quality = compute_avg(overall_data_all["quality"])
overall_all_workload = compute_avg(overall_data_all["workload"])
overall_recent_quality = compute_avg(overall_data_recent["quality"])
overall_recent_workload = compute_avg(overall_data_recent["workload"])

print("\nOverall class averages:")
print(f"  All Time: Quality Average = {overall_all_quality:.2f}, Workload Average = {overall_all_workload:.2f}")
if overall_data_recent["quality"][1] > 0:
    print(f"  Recent:   Quality Average = {overall_recent_quality:.2f}, Workload Average = {overall_recent_workload:.2f}")
else:
    print("  Recent:   No recent evaluation data.")

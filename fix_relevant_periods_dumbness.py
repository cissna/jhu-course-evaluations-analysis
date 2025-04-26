import json
import argparse


def add_fields_to_metadata(input_path: str, output_path: str) -> None:
    """
    Load the JSON file, add 'intersession' and 'summer' fields to metadata, then write updated JSON.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for entry in data.values():
        metadata = entry.get('metadata')
        if isinstance(metadata, dict):
            metadata.setdefault('intersession', None)
            metadata.setdefault('summer', None)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def count_entries(input_path: str) -> int:
    """
    Load the JSON file and return the number of top-level entries.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return len(data)


def fix_relevant_periods(input_path: str, output_path: str) -> None:
    """
    Load the JSON file, fix relevant_periods based on non-empty periods in data, and save it.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for course_code, entry in data.items():
        data_periods = entry.get('data', {})
        non_empty_periods = {period for period, value in data_periods.items() if value}

        metadata = entry.get('metadata', {})
        relevant_periods_set = set(metadata.get('relevant_periods', []))

        if non_empty_periods != relevant_periods_set:
            print(f"Mismatch for course {course_code}:")
            print(f"  Expected: {sorted(non_empty_periods)}")
            print(f"  Found: {sorted(relevant_periods_set)}\n")
            metadata['relevant_periods'] = sorted(non_empty_periods)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Tool for updating metadata, counting entries, or fixing relevant periods in cache.json'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_update = subparsers.add_parser('update', help='Add intersession and summer fields')
    parser_update.add_argument('input', help='Path to input cache.json')
    parser_update.add_argument('output', help='Path to output updated JSON')

    parser_count = subparsers.add_parser('count', help='Count top-level entries in cache.json')
    parser_count.add_argument('input', help='Path to input cache.json')

    parser_fix = subparsers.add_parser('fix_relevant', help='Fix relevant_periods in cache.json')
    parser_fix.add_argument('input', help='Path to input cache.json')
    parser_fix.add_argument('output', help='Path to output updated JSON')

    args = parser.parse_args()

    if args.command == 'update':
        add_fields_to_metadata(args.input, args.output)
    elif args.command == 'count':
        total = count_entries(args.input)
        print(f'The file {args.input} contains {total} entries.')
    elif args.command == 'fix_relevant':
        fix_relevant_periods(args.input, args.output)


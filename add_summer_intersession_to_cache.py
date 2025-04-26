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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Tool for updating metadata or counting entries in cache.json'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_update = subparsers.add_parser('update', help='Add intersession and summer fields')
    parser_update.add_argument('input', help='Path to input cache.json')
    parser_update.add_argument('output', help='Path to output updated JSON')

    parser_count = subparsers.add_parser('count', help='Count top-level entries in cache.json')
    parser_count.add_argument('input', help='Path to input cache.json')

    args = parser.parse_args()

    if args.command == 'update':
        add_fields_to_metadata(args.input, args.output)
    elif args.command == 'count':
        total = count_entries(args.input)
        print(f'The file {args.input} contains {total} entries.')


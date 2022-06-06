import argparse
import csv
import logging


MAPPING_CSV = 'mapping.csv'
LOGGER = logging.getLogger()


mapping = {}
with open('mapping.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        mapping[row['id']] = row

parser = argparse.ArgumentParser()
parser.add_argument('selected_csv')
args = parser.parse_args()

with open(args.selected_csv) as f:
    reader = csv.DictReader(f)
    for row in reader:
        _id = row['id']
        if _id not in mapping:
            LOGGER.warning(f'{_id} not in mapping')
            continue

        attendee = mapping[_id]
        print(f'{attendee["real_name"]} <{attendee["real_email"]}>')

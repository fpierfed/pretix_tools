import csv
import logging
import os
import re
from dotenv import load_dotenv
import faker
import pycountry
import requests
try:
    import requests_cache
except ImportError:
    pass
else:
    requests_cache.install_cache('cache')


load_dotenv()
LOGGER = logging.getLogger()


PRETIX_TOKEN = os.getenv('PRETIX_TOKEN')
EXCLUDE_ITEM_RE = {
    r'Childcare.*',
    r'Test.*',
    r'Remote.*',
    r'Livestream.*'
}


def _fetch(url, params, page=1):
    params.update({'page': page})
    r = requests.get(
        url,
        headers={'Authorization': f'Token {PRETIX_TOKEN}'},
        params=params
    )
    assert r.status_code == 200
    return r.json()


def fetch_orders(page=1):
    LOGGER.info(f'Fetching order page {page}')
    return _fetch(
        'https://pretix.eu/api/v1/organizers/europython/events/2022/orders/',
        params={'status':  'p'},
        page=page
    )


def fetch_items(page=1):
    LOGGER.info(f'Fetching item page {page}')
    return _fetch(
        'https://pretix.eu/api/v1/organizers/europython/events/2022/items/',
        params={},
        page=page
    )


def fetch_all(fetcher):
    pageno = 0
    has_more = True
    while has_more:
        pageno += 1
        data = fetcher(page=pageno)
        for result in data['results']:
            yield result
        has_more = data['next'] is not None


exclude_item_ids = set()

for item in fetch_all(fetch_items):
    _id = item['id']
    if any(re.match(p, item['name']['en']) for p in EXCLUDE_ITEM_RE):
        exclude_item_ids.add(_id)


ids = set()
attendees = []
faker = faker.Faker()

for order in fetch_all(fetch_orders):
    invoice_country_code = order['invoice_address']['country']
    invoice_country = pycountry.countries.get(
        alpha_2=invoice_country_code
    ).name
    invoice_city = order['invoice_address']['city']

    for position in order['positions']:
        _id = position['pseudonymization_id']
        assert _id is not None
        assert _id not in ids

        item_id = position['item']
        if item_id in exclude_item_ids:
            continue

        attendees.append(
            {
                'name': faker.unique.name(),
                'email': faker.unique.company_email(),
                'real_name': position['attendee_name'],
                'real_email': position['attendee_email'],
                'city': invoice_city,
                'country': invoice_country,
                'country_code': invoice_country_code,
                'id': _id,
            }
        )
        ids.add(_id)

anon_keys = ['name', 'email', 'city', 'country', 'country_code', 'id']
mapping_keys = ['id', 'name', 'email', 'real_name', 'real_email']

with open('anonymised.csv', 'w') as f, open('mapping.csv', 'w') as m:
    anon_writer = csv.DictWriter(f, anon_keys)
    mapping_writer = csv.DictWriter(m, mapping_keys)
    anon_writer.writeheader()
    mapping_writer.writeheader()

    for attendee in attendees:
        anon_writer.writerow({k: attendee[k] for k in anon_keys})
        mapping_writer.writerow({k: attendee[k] for k in mapping_keys})

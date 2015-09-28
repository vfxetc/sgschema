
import argparse
import urlparse
import os

import shotgun_api3

import sgschema


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name')
parser.add_argument('base_url')
parser.add_argument('script_name')
parser.add_argument('api_key')
args = parser.parse_args()


shotgun = shotgun_api3.Shotgun(args.base_url, args.script_name, args.api_key)
schema = sgschema.Schema()
schema.read(shotgun)


if not args.name:
    parsed = urlparse.urlparse(args.base_url)
    args.name = parsed.netloc.split('.')[0]

here = os.path.dirname(__file__)

schema.dump(os.path.join(here, args.name + '.raw.json'), raw=True)
schema.dump(os.path.join(here, args.name + '.json'))

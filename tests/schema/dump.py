
import argparse
import urlparse
import os

import shotgun_api3

import sgschema


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name')
parser.add_argument('-r', '--registry-name')
parser.add_argument('base_url', nargs='?')
parser.add_argument('script_name', nargs='?')
parser.add_argument('api_key', nargs='?')
args = parser.parse_args()


if args.registry_name or not (args.base_url or args.script_name or args.api_key):
    import shotgun_api3_registry
    shotgun = shotgun_api3_registry.connect(args.registry_name)
else:
    shotgun = shotgun_api3.Shotgun(args.base_url, args.script_name, args.api_key)

schema = sgschema.Schema()
schema.read(shotgun)


if not args.name:
    parsed = urlparse.urlparse(shotgun.base_url)
    args.name = parsed.netloc.split('.')[0]

here = os.path.dirname(__file__)

schema._dump_raw(os.path.join(here, args.name + '.'))
schema.dump(os.path.join(here, args.name + '.json'))

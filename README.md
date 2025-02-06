# bunny-gen



Create a .secrets/auth.ini

you'll need to put 4 details


zone_api_key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx

storage_endpoint=https://storage.bunnycdn.com/monitoring/

storage_api_key=xxxxxxxx-xxxx-xxxx-xxxxxxxxxxxxx-xxxx-xxxx

pull_zone_id=NNNNNN

# Example usage

./config_zone.py --help
usage: config_zone.py [-h] [--action [{config,create,get-zone-config,get-storage-config}]] [--domain-name [DOMAIN_NAME]] [--zone-id [ZONE_ID]] [--zone-name [ZONE_NAME]]

optional arguments:
  -h, --help            show this help message and exit
  --action [{config,create,get-zone-config,get-storage-config}]
  --domain-name [DOMAIN_NAME]
  --zone-id [ZONE_ID]
  --zone-name [ZONE_NAME]

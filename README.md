# bunny-gen



Create a .secrets/auth.ini

you'll need to put 4 details

```ini
[BUNNYCDN]
zone_api_key=xxxx
storage_endpoint=https://storage.bunnycdn.com/monitoring/
storage_api_key=xxx
pull_zone_id=123456
```

# Example usage

```bash
./config_zone.py --help
usage: config_zone.py [-h] [--action [{config,create,get-zone-config,get-storage-config}]] [--domain-name [DOMAIN_NAME]] [--zone-id [ZONE_ID]] [--zone-name [ZONE_NAME]]

optional arguments:
  -h, --help            show this help message and exit
  --action [{config,create,get-zone-config,get-storage-config}]
  --domain-name [DOMAIN_NAME]
  --zone-id [ZONE_ID]
  --zone-name [ZONE_NAME]
```

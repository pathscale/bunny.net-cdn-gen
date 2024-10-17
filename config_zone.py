#!/usr/bin/env python3

import requests
import json
from configparser import ConfigParser
from unittest.mock import Mock
import logging

API_URL = 'https://bunnycdn.com/api/'

class BunnyClient(object):
    def __init__(self):
        auth_config = ConfigParser()
        auth_config.read('.secrets/auth.ini')
        self.credentials = dict(auth_config['BUNNYCDN'])
        self.API_URL = 'https://bunnycdn.com/api/'
        self.STORAGE_URL = ' https://storage.bunnycdn.com/'

        self.name_pz_mapping = dict()
        self.get_pullzone_config()
        self.get_storage_zone_config()

    def get_storage_name(self, domain, suffix: int = 1):
        storage_name = domain.replace('.', '--')
        if suffix > 1:
            storage_name += '-%s' % suffix
        if len(storage_name) > 20:
            cut = 19 - len(str(suffix))
            storage_name = domain.replace('.', '--')[:cut] + '-%s' % suffix
        if storage_name in list(self.name_pz_mapping):
            suffix += 1
            return self.get_storage_name(domain, suffix)
        else:
            return storage_name

    def default_request(self, req_type, route, data: dict = None, **kwargs) -> requests.Response:
        kwargs['url'] = self.API_URL + route
        if 'headers' in kwargs.keys():
            kwargs['headers'].update({"AccessKey": self.credentials.get('zone_api_key')})
        else:
            kwargs['headers'] = {"AccessKey": self.credentials.get('zone_api_key')}
        if data:
            kwargs['data'] = json.dumps(data)
        if req_type == 'get':
            return (requests.get(**kwargs))
        elif req_type == 'post':
            kwargs['headers'].update({'Content-Type': 'application/json'})
            return (requests.post(**kwargs))
        elif req_type == 'put':
            return (requests.put(**kwargs))
        elif req_type == 'delete':
            return (requests.delete(**kwargs))
        else:
            r = Mock(requests.Response)
            r.status_code = 404
            return (r)

    def storage_request(self, req_type, zone_name, route, data = None, file = None, **kwargs) -> requests.Response:
        kwargs['url'] = self.STORAGE_URL + f'{zone_name}/' + route
        zone_key = [d.get('Password') for d in self.storage_zone_config if d.get('Name') == zone_name]
        if zone_key:
            zone_key = zone_key[0]
        else:
            raise Exception('Storage zone not found.')
        if 'headers' in kwargs.keys():
            kwargs['headers'].update({"AccessKey": zone_key})
        else:
            kwargs['headers'] = {"AccessKey": zone_key}
        if data:
            kwargs['data'] = json.dumps(data) if type(data) == dict else data
        elif file:
            kwargs['data'] = open(file, 'rb').read()
        if req_type == 'get':
            return (requests.get(**kwargs))
        elif req_type == 'post':
            kwargs['headers'].update({'Content-Type': 'application/json'})
            return (requests.post(**kwargs))
        elif req_type == 'put':
            return (requests.put(**kwargs))
        elif req_type == 'delete':
            return (requests.delete(**kwargs))
        else:
            r = Mock(requests.Response)
            r.status_code = 404
            return (r)

    def get_pullzone_config(self):
        resp = self.default_request('get', 'pullzone')
        self.pull_zone_config = json.loads(resp.content.decode())
        self.name_pz_mapping = dict([(d.get('Name'), d.get('Id')) for d in self.pull_zone_config])
        self.rules = dict(
            [(config.get('Id'), [rule.get('Guid') for rule in config.get('EdgeRules')]) for config in
             self.pull_zone_config])

    def get_storage_zone_config(self):
        resp = self.default_request('get', 'storagezone')
        self.storage_zone_config = json.loads(resp.content.decode())

    def clean_rules(self, pull_zone_id):
        if len(self.rules.get(pull_zone_id)) > 0:
            for rule in self.rules.get(pull_zone_id):
                self.default_request('delete', f'pullzone/{pull_zone_id}/edgerules/{rule}')

    def create_storage(self, domain_name):
        zone_name = self.get_storage_name(domain_name)
        if zone_name not in [d.get('Name') for d in self.storage_zone_config]:
            post_data = {"Name": zone_name}
            resp = self.default_request('post', 'storagezone', post_data)
            if resp.status_code not in [200, 201]:
                print(f"Error occured at creating storage zone for {domain_name}: {resp.content.decode()}")
            else:
                print('Created storage zone %s' % zone_name)
                self.get_storage_zone_config()

    def create_zone(self):
        raise NotImplementedError

    def upload_file(self, zone_name, path, content=None, file=None):
        if content and path:
            return self.storage_request('put', zone_name, path, data=content)
        elif file and path:
            return self.storage_request('put', zone_name, path, file=content)

    def download_file(self, zone_name, path):
        return self.storage_request('get', zone_name, path)

    def list_files(self, zone_name, path=''):
        flist = []
        resp = self.storage_request('get', zone_name, path)
        for obj in resp.json():
            path = obj.get('Path') + obj.get('ObjectName')
            if obj['IsDirectory']:
                flist = self.list_files(zone_name, obj.get('ObjectName'))
            else:
                flist.append(path)
        return flist



    def config_zone(self, domain_name, zone_name=None, pull_zone_id=None):
        if not zone_name:
            zone_name = domain_name.replace('.', '--')
        if not pull_zone_id:
            pull_zone_id = self.name_pz_mapping.get(zone_name)
        if not pull_zone_id:
            return ()
        self.clean_rules(pull_zone_id)
        edge_rules = json.loads(open('edge_rules.json.template').read().format(domain=domain_name, zone_name=zone_name))
        hostnames = json.loads((open('hostnames.json.template').read().format(domain=domain_name, zone_name=zone_name)))
        zone_config = json.loads(open('zone_config.json.template').read())

        resp = self.default_request('post', f'pullzone/{pull_zone_id}', data=zone_config)
        if resp.status_code not in [200, 201, 204]:
            print(
                f'Could not configure pullzone for domain {domain_name}, error {resp.status_code}: {resp.content.decode()}')
            return ()

        for hostname in hostnames:
            req_data = {
                "PullZoneId": pull_zone_id,
                "Hostname": hostname,
            }
            resp = self.default_request('post', 'pullzone/addHostname', data=req_data)
            if resp.status_code not in [200, 201]:
                err = json.loads(resp.content.decode())
                if not err.get('ErrorKey') == "pullzone.hostname_already_registered":
                    print(f'Could not create hostname {hostname}, error {resp.status_code}: {resp.content.decode()}')
                    return ()
                else:
                    print(f"Hostname {hostname} already exists.")
            else:
                print(f'{hostname} created.')
            req_data.update({"ForceSSL": True})
            resp = self.default_request('post', 'pullzone/setForceSSL', data=req_data)
            if resp.status_code not in [200, 201]:
                print(f'Could set SSL for {hostname}, error {resp.status_code}: {resp.content.decode()}')
                # return ()
            else:
                print(f'{hostname} SSL specs updated.')

        for rule in edge_rules:
            resp = self.default_request('post', f'pullzone/{pull_zone_id}/edgerules/addOrUpdate', data=rule)
            if resp.status_code not in [200, 201]:
                print(f'Could not create rule, error {resp.status_code}: {resp.content.decode()}')
                return ()
            else:
                print('Rule created.')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--action', action="store", dest="action", nargs='?', const=1,
                        choices=['config', 'create', 'get-zone-config', 'get-storage-config'])
    parser.add_argument('--domain-name', action="store", dest="domain_name", nargs='?', const=1, default=None)
    parser.add_argument('--zone-id', action="store", dest="zone_id", nargs='?', const=1, type=int, default=None)
    parser.add_argument('--zone-name', action="store", dest="zone_name", nargs='?', const=1, default=None)
    args = parser.parse_args()
    cli = BunnyClient()
    if args.domain_name:
        if args.action == 'create':
            cli.create_storage(args.domain_name)
        elif args.action == 'config':
            cli.config_zone(args.domain_name, args.zone_name, args.zone_id)
        elif args.action == 'get-storage-config':
            zone_name = args.zone_name if args.zone_name else args.domain_name.replace('.', '--')
            match = [d for d in cli.storage_zone_config if d.get('Name') == zone_name]
            if match:
                print(json.dumps(match[0], indent=2))
            else:
                print('Not found.')
        elif args.action == 'get-zone-config':
            zone_name = args.zone_name if args.zone_name else args.domain_name.replace('.', '--')
            match = [d for d in cli.pull_zone_config if d.get('Name') == zone_name]
            if match:
                print(json.dumps(match[0], indent=2))
            else:
                print('Not found.')

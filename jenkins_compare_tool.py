#!/usr/bin/env python

import argparse
from pathlib import Path, PurePath

from jenkinsapi.jenkins import Jenkins
import yaml


current_dir = Path(__file__).parent.absolute()
home_dir = Path.home()
print(home_dir)

CREDENTIALS_FILE = '.jenkins_compare_tool'
CREDENTIALS_PATH = [str(PurePath(current_dir, CREDENTIALS_FILE)),
                    str(PurePath(home_dir, CREDENTIALS_FILE))]

parser = argparse.ArgumentParser(description='Compare yolo run to a benchmark yolo run.')
parser.add_argument('--nightly', dest='nightly', help='Nightly run.')
parser.add_argument('--feature', dest='feature', help='Feature run.')
parser.add_argument('--jenkins-host', dest='jenkins_host', help='jenkins url')
parser.add_argument('--jenkins-username', dest='jenkins_username', help='jenkins url')
parser.add_argument('--jenkins-api-token', dest='jenkins_api_token', help='jenkins url')

args = parser.parse_args()

class Credentials:
    def __init__(self, host=None, username=None, token=None):
        self.host = host
        self.user = username
        self.token = token
creds = Credentials(args.jenkins_host, args.jenkins_username, args.jenkins_api_token)

def load_missing_credentials_from_file(creds):
    """Update any missing credentials using any found in config file"""
    data = None
    for path in CREDENTIALS_PATH:
        try:
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                break
        except Exception:
            pass

    keys = data.keys()
    if 'jenkins_host' in keys and creds.host is None:
        creds.host = data['jenkins_host']
    if 'username' in keys and creds.user is None:
        creds.user = data['username']
    if 'password' in keys and creds.token is None:
        creds.token = data['password']

    if not creds.host:
        raise Exception('Jenkins url required')
    if not creds.user:
        raise Exception('Jenkins username required')
    if not creds.token:
        raise Exception('Jenkins password required')

def get_server_instance(creds):
    server = Jenkins(creds.host, username=creds.user, password=creds.token)
    return server

if __name__ == "__main__":
    print(f'{args.nightly} {args.feature}')

    load_missing_credentials_from_file(creds)
    server = get_server_instance(creds)
    print(server.version)

    

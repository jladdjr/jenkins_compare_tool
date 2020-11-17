#!/usr/bin/env python

import argparse
from pathlib import Path, PurePath

from jenkinsapi.jenkins import Jenkins
from junitparser import JUnitXml, Failure, Skipped, Error
import yaml


#current_dir = Path(__file__).parent.absolute()
current_dir = Path()
home_dir = Path.home()
print(home_dir)

CREDENTIALS_FILE = '.jenkins_compare_tool'
CREDENTIALS_PATH = [str(PurePath(current_dir, CREDENTIALS_FILE)),
                    str(PurePath(home_dir, CREDENTIALS_FILE))]

DEFAULT_JOB_NAME = 'Test_Tower_Yolo_Express'

parser = argparse.ArgumentParser(description='Compare yolo run to a benchmark yolo run.')
parser.add_argument('--nightly', dest='nightly', help='Nightly run.')
parser.add_argument('--feature', dest='feature', help='Feature run.')
parser.add_argument('--jenkins-host', dest='jenkins_host', help='jenkins url')
parser.add_argument('--jenkins-username', dest='jenkins_username', help='jenkins url')
parser.add_argument('--jenkins-api-token', dest='jenkins_api_token', help='jenkins url')
parser.add_argument('--nightly-test-job', dest='nightly_test_job', help='Name of jenkins job used for nightly tests.')
parser.add_argument('--feature-test-job', dest='feature_test_job', help='Name of jenkins job used for feature test.')

args = parser.parse_args()

class Credentials:
    def __init__(self, host=None, username=None, token=None):
        self.host = host
        self.user = username
        self.token = token

creds = Credentials(args.jenkins_host, args.jenkins_username, args.jenkins_api_token)

class Config:
    def __init__(self, nightly_test_job=None, feature_test_job=None):
        self.nightly_test_job = nightly_test_job
        self.feature_test_job = feature_test_job

config = Config(args.nightly_test_job, args.feature_test_job)

def load_missing_options_from_file(creds, config):
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

    if 'nightly_test_job' in keys and config.nightly_test_job is None:
        config.nightly_test_job = data['nightly_test_job']
    if 'feature_test_job' in keys and config.feature_test_job is None:
        config.feature_test_job = data['feature_test_job']

    if not config.nightly_test_job:
        raise Exception('Nightly Test Job name required')
    if not config.feature_test_job:
        raise Exception('Featuer Test Job name required')

def get_server_instance(creds):
    server = Jenkins(creds.host, username=creds.user, password=creds.token)
    return server

def get_test_results(server, job_name, build_number):
    # get artifact
    job = server.get_job(job_name)
    build = job.get_build(build_number)
    artifact_dict = build.get_artifact_dict()
    test_results = artifact_dict['artifacts/results.xml']
    test_results_file = test_results.save('/tmp/test_results.xml')

    # parse xml junit results
    xml = JUnitXml.fromfile(test_results_file)
    for suite in xml:
        print(suite)
        for case in suite:
            if case.result:
                if isinstance(case.result, Failure):
                    print(case.name)
                    #print('  failure ', case.result.message)

if __name__ == "__main__":
    print(f'{args.nightly} {args.feature}')

    load_missing_options_from_file(creds, config)
    server = get_server_instance(creds)
    get_test_results(server, config.nightly_test_job, 18204)

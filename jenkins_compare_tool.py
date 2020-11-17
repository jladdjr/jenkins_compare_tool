#!/usr/bin/env python

import argparse
import logging
import os
from pathlib import Path, PurePath
import sys

from jenkinsapi.jenkins import Jenkins
from junitparser import JUnitXml, Failure, Skipped, Error
import yaml

current_dir = Path()  # current dir
home_dir = Path.home()

CREDENTIALS_FILE = '.jenkins_compare_tool'
CREDENTIALS_PATH = [str(PurePath(current_dir, CREDENTIALS_FILE)),
                    str(PurePath(home_dir, CREDENTIALS_FILE))]

TMP_RESULTS_FILE = '/tmp/test_results.xml'

parser = argparse.ArgumentParser(description='Compare yolo run to a benchmark yolo run.')
parser.add_argument('--nightly', dest='nightly', type=int, required=True, help='Nightly run.')
parser.add_argument('--feature', dest='feature', type=int, required=True, help='Feature run.')
parser.add_argument('--jenkins-host', dest='jenkins_host', help='jenkins url')
parser.add_argument('--jenkins-username', dest='jenkins_username', help='jenkins url')
parser.add_argument('--jenkins-api-token', dest='jenkins_api_token', help='jenkins url')
parser.add_argument('--nightly-test-job', dest='nightly_test_job', default='Install and Integration', help='Name of jenkins job used for nightly tests.')
parser.add_argument('--feature-test-job', dest='feature_test_job', default='Test_Tower_Yolo_Express', help='Name of jenkins job used for feature test.')
parser.add_argument('--verbose', '-v', action='count')

args = parser.parse_args()
import pdb
pdb.set_trace()

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

if args.verbose:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.INFO)

class Credentials:
    def __init__(self, host=None, username=None, token=None):
        self.host = host
        self.user = username
        self.token = token

creds = Credentials(args.jenkins_host, args.jenkins_username, args.jenkins_api_token)

class Config:
    def __init__(self, nightly_test_job=None, feature_test_job=None,
            nightly_build=None, feature_build=None):
        self.nightly_test_job = nightly_test_job
        self.feature_test_job = feature_test_job
        self.nightly_build = nightly_build
        self.feature_build = feature_build

config = Config(args.nightly_test_job, args.feature_test_job,
                args.nightly, args.feature)

def load_missing_options_from_file(creds, config):
    """Update any missing credentials using any found in config file"""
    logger.debug(f'loading credentials')
    data = None
    for path in CREDENTIALS_PATH:
        try:
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                logger.debug(f'found credentials in {path}')
                break
        except Exception:
            pass

    keys = data.keys()
    if 'jenkins_host' in keys and creds.host is None:
        creds.host = data['jenkins_host']
        logger.debug(f'jenkins_host: {creds.host}')
    if 'username' in keys and creds.user is None:
        creds.user = data['username']
        logger.debug(f'username: {creds.user}')
    if 'password' in keys and creds.token is None:
        creds.token = data['password']
        logger.debug(f'password: <omitted>')

    if not creds.host:
        raise Exception('Jenkins url required')
    if not creds.user:
        raise Exception('Jenkins username required')
    if not creds.token:
        raise Exception('Jenkins password required')

    config.nightly_test_job = data['nightly_test_job']
    logger.debug(f'nightly_test_job: {config.nightly_test_job}')
    config.feature_test_job = data['feature_test_job']
    logger.debug(f'feature_test_job: {config.feature_test_job}')

    if not config.nightly_test_job:
        raise Exception('Nightly Test Job name required')
    if not config.feature_test_job:
        raise Exception('Featuer Test Job name required')

def get_server_instance(creds):
    logger.debug(f'connecting to {creds.host}')
    server = Jenkins(creds.host, username=creds.user, password=creds.token)
    return server

def get_test_results(server, job_name, build_number):
    logger.debug(f'getting build results for {job_name}, build: {build_number}')
    # get artifact
    job = server.get_job(job_name)
    build = job.get_build(build_number)
    artifact_dict = build.get_artifact_dict()
    test_results = artifact_dict['artifacts/results.xml']
    try:
        os.remove(TMP_RESULTS_FILE)
    except FileNotFoundError:
        pass
    test_results_file = test_results.save(TMP_RESULTS_FILE)

    # parse xml junit results
    xml = JUnitXml.fromfile(test_results_file)
    failures = []
    for suite in xml:
        for case in suite:
            if case.result:
                if isinstance(case.result, Failure):
                    #print(case.name)
                    #print('  failure ', case.result.message)
                    failures.append(case.name)
    return failures

def filter_out_existing_failures(old_failures, new_failures):
    removed_failures = []
    for failure in old_failures:
        try:
            new_failures.remove(failure)
            removed_failures.append(failure)
        except ValueError:
            pass
    return removed_failures

if __name__ == "__main__":
    load_missing_options_from_file(creds, config)
    server = get_server_instance(creds)
    old_failures = get_test_results(server, config.nightly_test_job, config.nightly_build)
    new_failures = get_test_results(server, config.feature_test_job, config.feature_build)


    logger.debug('Nightly failed tests:')
    for failure in old_failures:
        logger.debug(failure)
    logger.debug('Feature failed tests:')
    for failure in old_failures:
        logger.debug(failure)

    removed_failures = filter_out_existing_failures(old_failures, new_failures)
    logger.debug('Existing failed tests found:')
    for failure in removed_failures:
        logger.debug(failure)

    print('Remaining failed tests:')
    for failure in new_failures:
        print(failure)

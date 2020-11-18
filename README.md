# jenkins_compare_tool

## Requirements

`pip install -U -r requirements.txt`

## Sample Usage

```
jenkins_compare_tool.py --nightly 100 --feature 101

Filtering results for:
http://jenkins/job/My_Integration_Test/101/
My test run description
2020-11-11

With respect to:
http://jenkins/job/My_Integration_Test/100/
2020-11-10

Filtered failures (2):
  test_foo
  test_bar

Remaining failures (1):
  test_baz
```

## Configuration

In the local directory or your home directory, create `.jenkins_compare_tool`:

```
---
jenkins_host: http://jenkins-host
username: joe_user@email.com
token: <jenkins api token>

nightly_test_job: My_Nightly_Integration_Test
feature_test_job: My_Integration_Test
```

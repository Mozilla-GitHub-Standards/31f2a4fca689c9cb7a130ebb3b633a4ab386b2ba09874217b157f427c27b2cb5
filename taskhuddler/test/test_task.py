"""Test Task class."""

import os
import json
import pytest
import datetime

import dateutil.parser
from unittest.mock import patch

from taskhuddler.task import Task, TaskStatus, TaskDefinition
import taskcluster


def mocked_status(dummy, task_id):
    return get_dummy_task_status('completed.json')


def mocked_definition(dummy, task_id):
    return get_dummy_task_definition('completed.json')


def get_dummy_task_json(filename):
    with open(os.path.join(os.path.dirname(__file__), 'data', filename)) as f:
        return json.loads(f.read()).get('tasks')[0]


def get_dummy_task_status(filename):
    full = get_dummy_task_json(filename)
    return full.get('status')


def get_dummy_task_definition(filename):
    full = get_dummy_task_json(filename)
    return full.get('task')


def test_task_taskid():
    task = Task(json=get_dummy_task_json('completed.json'))
    assert task.taskid == "A-8AqzvvRsqH9b0VHBXYjA"


@pytest.mark.parametrize('filename,state', (
    ['completed.json', True],
    ['unscheduled.json', False],
    ['failed.json', False]
))
def test_task_completed_bool(filename, state):
    task = Task(json=get_dummy_task_json(filename))
    assert task.completed is state


@pytest.mark.parametrize('filename,expected', (
    ['completed.json', 'completed'],
    ['unscheduled.json', 'unscheduled'],
    ['failed.json', 'failed']
))
def test_task_state_completed(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.state == expected


@pytest.mark.parametrize('filename,expected', (
    ['completed.json', dateutil.parser.parse('2017-10-26T01:03:58.641Z')],
    ['unscheduled.json', None],
    ['missing.json', dateutil.parser.parse('2017-10-26T01:09:00.750Z')]
))
def test_task_scheduled(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.scheduled == expected


@pytest.mark.parametrize('filename,expected', (
    ['completed.json', dateutil.parser.parse('2017-10-26T01:03:59.291Z')],
    ['unscheduled.json', None],
    ['missing.json', None]
))
def test_task_started(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.started == expected


@pytest.mark.parametrize('filename,expected', (
    ['completed.json', dateutil.parser.parse('2017-10-26T01:18:11.852Z')],
    ['unscheduled.json', None],
    ['missing.json', None]
))
def test_task_resolved(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.resolved == expected


@pytest.mark.parametrize('filename, expected', (
    ['completed.json',  [datetime.timedelta(seconds=852, microseconds=561000)]],
    ['failed.json', [datetime.timedelta(seconds=526, microseconds=231000)]],
    ['unscheduled.json', []],
))
def test_run_durations(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.run_durations() == expected


@pytest.mark.parametrize('filename, expected', (
    ['completed.json', 'test'],
    ['failed.json', 'nightly-l10n'],
))
def test_task_kind(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.kind == expected


@pytest.mark.parametrize('filename, expected', (
    ['completed.json', False],
    ['failed.json', True],
))
def test_task_has_failures(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.has_failures == expected


@pytest.mark.parametrize('filename, expected', (
    ['completed.json', 'test-windows10-64-nightly/opt-web-platform-tests-e10s-3'],
    ['failed.json', 'nightly-l10n-linux-nightly-2/opt'],
))
def test_task_names(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.label == expected
    assert task.name == expected


@pytest.mark.parametrize('filename, expected', (
    ['completed.json',  []],
    ['continuation1.json', [
        "project:releng:signing:cert:nightly-signing",
        "project:releng:signing:format:mar_sha384",
        "project:releng:signing:format:sha2signcode",
        "project:releng:signing:format:sha2signcodestub"
    ]],
))
def test_scopes(filename, expected):
    task = Task(json=get_dummy_task_json(filename))
    assert task.scopes == expected


def test_task_query_by_task_id():
    task_id = 'A-8AqzvvRsqH9b0VHBXYjA'

    with patch.object(taskcluster.Queue, 'task', new=mocked_definition) as mocked_method, patch.object(taskcluster.Queue, 'status', new=mocked_status) as mocked_method2:
        task = Task(task_id=task_id)
        assert task.kind == 'test'
        assert task.state == 'completed'


@pytest.mark.parametrize('filename,started,is_completed,state', (
    ['completed.json', dateutil.parser.parse('2017-10-26T01:03:59.291Z'), True, 'completed'],
    ['unscheduled.json', None, False, 'unscheduled'],
    ['missing.json', None, False, 'failed']
))
def test_task_status_by_json(filename, started, is_completed, state):
    task = TaskStatus(json=get_dummy_task_json(filename))
    assert task.started == started
    assert task.completed is is_completed
    assert task.state == state


def test_task_status_by_task_id():
    task_id = 'A-8AqzvvRsqH9b0VHBXYjA'
    with patch.object(taskcluster.Queue, 'status', new=mocked_status) as mm:
        task = TaskStatus(task_id=task_id)
        assert task.state == 'completed'


def test_task_status_no_input():
    with pytest.raises(ValueError):
        TaskStatus()


def test_task_definition_no_input():
    with pytest.raises(ValueError):
        TaskDefinition()


def test_task_no_input():
    with pytest.raises(ValueError):
        Task()


def test_run_durations():
    task = Task(json=get_dummy_task_json('completed.json'))
    assert task.run_durations() == [datetime.timedelta(seconds=852, microseconds=561000)]

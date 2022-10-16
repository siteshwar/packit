# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from pathlib import Path, PosixPath
from typing import Optional

import pytest
from flexmock import flexmock
from marshmallow import ValidationError

from ogr.abstract import GitProject, GitService
from packit.actions import ActionName
from packit.config import (
    CommonPackageConfig,
    JobType,
    JobConfigTriggerType,
    JobConfig,
    get_package_config_from_repo,
)
from packit.config.package_config import (
    get_specfile_path_from_repo,
    PackageConfig,
    get_local_specfile_path,
    get_local_package_config,
)
import packit.config.package_config
from packit.config.sources import SourcesItem
from packit.constants import CONFIG_FILE_NAMES
from packit.schema import PackageConfigSchema
from packit.sync import SyncFilesItem
from tests.spellbook import UP_OSBUILD, SYNC_FILES
from tests.unit.test_config import (
    get_job_config_dict_full,
    get_job_config_dict_simple,
    get_job_config_simple,
    get_job_config_full,
    get_default_job_config,
    get_job_config_dict_build_for_branch,
    get_job_config_build_for_branch,
)


@pytest.fixture()
def job_config_simple():
    return get_job_config_simple()


@pytest.mark.parametrize(
    "files,expected",
    [(["foo.spec"], "foo.spec"), ([], None)],
)
def test_get_specfile_path_from_repo(files, expected):
    gp = flexmock(GitProject)
    gp.should_receive("full_repo_name").and_return("a/b")
    gp.should_receive("get_files").and_return(files)
    git_project = GitProject(repo="", service=GitService(), namespace="")
    assert get_specfile_path_from_repo(project=git_project) == expected


@pytest.mark.parametrize(
    "package_config, project",
    [
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="xxx",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                            )
                        },
                    )
                ],
            ),
            None,
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="xxx",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                                project="example",
                            )
                        },
                    )
                ],
            ),
            "example",
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="xxx",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.release,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                                project="example1",
                            )
                        },
                    ),
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                                project="example2",
                            )
                        },
                    ),
                ],
            ),
            "example1",
        ),
    ],
)
def test_project_from_copr_build_job(package_config, project):
    config_project_value = package_config.get_copr_build_project_value()
    assert config_project_value == project


@pytest.mark.parametrize(
    "package_config, expected",
    [
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="xxx",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.propose_downstream,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                                dist_git_branches=[
                                    "example",
                                ],
                            )
                        },
                    )
                ],
            ),
            {
                "example",
            },
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="xxx",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.propose_downstream,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                                dist_git_branches=[
                                    "example1",
                                    "example2",
                                ],
                            )
                        },
                    ),
                ],
            ),
            {"example1", "example2"},
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="xxx",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.propose_downstream,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                specfile_path="xxx",
                            )
                        },
                    )
                ],
            ),
            set(),
        ),
    ],
)
def test_dg_branches_from_propose_downstream_job(package_config, expected):
    branches = package_config.get_propose_downstream_dg_branches_value()
    assert branches == expected


def test_package_config_equal(job_config_simple):
    assert PackageConfig(
        packages={
            "package": CommonPackageConfig(
                specfile_path="fedora/package.spec",
                synced_files=[SyncFilesItem(src=["packit.yaml"], dest="packit.yaml")],
                downstream_package_name="package",
                create_pr=True,
            )
        },
        jobs=[job_config_simple],
    ) == PackageConfig(
        packages={
            "package": CommonPackageConfig(
                specfile_path="fedora/package.spec",
                synced_files=[SyncFilesItem(src=["packit.yaml"], dest="packit.yaml")],
                downstream_package_name="package",
                create_pr=True,
            )
        },
        jobs=[job_config_simple],
    )


@pytest.mark.parametrize(
    "not_equal_package_config",
    [
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/other-package.spec",
                    synced_files=[
                        SyncFilesItem(src=["a"], dest="a"),
                        SyncFilesItem(src=["b"], dest="b"),
                    ],
                )
            },
            jobs=[get_job_config_simple()],
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    synced_files=[SyncFilesItem(src=["c"], dest="c")],
                )
            },
            jobs=[get_job_config_simple()],
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    synced_files=[
                        SyncFilesItem(src=["a"], dest="a"),
                        SyncFilesItem(src=["b"], dest="b"),
                    ],
                )
            },
            jobs=[get_job_config_full()],
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    synced_files=[
                        SyncFilesItem(src=["c"], dest="c"),
                        SyncFilesItem(src=["d"], dest="d"),
                    ],
                    create_pr=False,
                )
            },
            jobs=[get_job_config_full()],
        ),
    ],
)
def test_package_config_not_equal(not_equal_package_config):
    config = PackageConfig(
        packages={
            "package": CommonPackageConfig(
                specfile_path="fedora/package.spec",
                synced_files=[
                    SyncFilesItem(src=["c"], dest="c"),
                    SyncFilesItem(src=["d"], dest="d"),
                ],
                create_pr=True,
            )
        },
        jobs=[get_job_config_full()],
    )
    assert config != not_equal_package_config


@pytest.mark.parametrize(
    "raw,is_valid",
    [
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "synced_files": "fedora/foobar.spec",
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/foobar.spec"],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/foobar.spec", "somefile", "somedirectory"],
                "jobs": [],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "propose_downstream",
                        "trigger": "release",
                        "dist_git_branches": [
                            "fedora-all",
                        ],
                    }
                ],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "propose_downstream",
                        "trigger": "release",
                        "dist_git_branches": ["fedora-all", "epel-8"],
                    }
                ],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "copr_build",
                        "trigger": "release",
                        "targets": [
                            "fedora-stable",
                        ],
                    }
                ],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "copr_build",
                        "trigger": "release",
                        "targets": ["fedora-stable", "fedora-development"],
                    }
                ],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "propose_downstream",
                        "trigger": "release",
                        "targets": ["f31", "f32"],
                        "timeout": 123,
                        "owner": "santa",
                        "project": "gifts",
                    }
                ],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "tests",
                        "trigger": "pull_request",
                        "targets": [
                            "fedora-all",
                        ],
                        "env": {
                            "MYVAR1": 5,
                            "MYVAR2": "foo",
                        },
                    }
                ],
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/foobar.spec"],
                "actions": {
                    "pre-sync": "some/pre-sync/command --option",
                    "get-current-version": "get-me-version",
                },
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/foobar.spec"],
                "actions": {
                    "pre-sync": "some/pre-sync/command --option",
                    "unknown-action": "nothing",
                },
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "actions": ["actions" "has", "to", "be", "key", "value"],
                "jobs": [{"job": "asd", "trigger": "qwe"}],
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "notifications": {"pull_request": {"successful_build": False}},
            },
            True,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "notifications": {"pull_request": {"successful_build": "nie"}},
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "notifications": {"pull_request": False},
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "sources": [{"path": "example_path"}],
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "sources": [{"url": "example_url"}],
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "sources": {"path": "example_path", "url": "example_url"},
            },
            False,
        ),
    ],
)
def test_package_config_validate(raw, is_valid):
    if not is_valid:
        with pytest.raises((ValidationError, ValueError)):
            PackageConfig.get_from_dict(raw)
    else:
        PackageConfig.get_from_dict(raw)


@pytest.mark.parametrize(
    "raw,is_valid",
    [
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "propose_downstream",
                        "trigger": "release",
                        "unknown": "key",
                    }
                ],
            },
            False,
        ),
        (
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "propose_downstream",
                        "trigger": "release",
                        "unknown": "key",
                    }
                ],
            },
            False,
        ),
    ],
)
def test_package_config_validate_unknown_key(raw, is_valid):
    if not is_valid:
        with pytest.raises((ValidationError, ValueError)):
            PackageConfig.get_from_dict(raw)
    else:
        PackageConfig.get_from_dict(raw)


@pytest.mark.parametrize(
    "raw",
    [
        # {"specfile_path": "test/spec/file/path", "something": "different"},
        {
            "specfile_path": "test/spec/file/path",
            "jobs": [{"trigger": "release", "release_to": ["f28"]}],
        }
    ],
)
def test_package_config_parse_error(raw):
    with pytest.raises(Exception):
        PackageConfig.get_from_dict(raw_dict=raw)


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/package.spec"],
                "jobs": [get_job_config_dict_full()],
                "downstream_package_name": "package",
                "create_pr": False,
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="fedora/package.spec",
                        downstream_package_name="package",
                        create_pr=False,
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            )
                        ],
                    )
                },
                jobs=[
                    get_job_config_full(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        create_pr=False,
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"],
                                dest="fedora/package.spec",
                            )
                        ],
                    )
                ],
            ),
            id="specfile_path+synced_files+job_config_full+downstream_package_name+create_pr",
        ),
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": [
                    "fedora/package.spec",
                    "somefile",
                    "other",
                    "directory/files",
                ],
                "jobs": [get_job_config_dict_simple()],
                "downstream_package_name": "package",
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            ),
                            SyncFilesItem(src=["somefile"], dest="somefile"),
                            SyncFilesItem(src=["other"], dest="other"),
                            SyncFilesItem(
                                src=["directory/files"], dest="directory/files"
                            ),
                        ],
                    )
                },
                jobs=[
                    get_job_config_simple(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"],
                                dest="fedora/package.spec",
                            ),
                            SyncFilesItem(src=["somefile"], dest="somefile"),
                            SyncFilesItem(src=["other"], dest="other"),
                            SyncFilesItem(
                                src=["directory/files"], dest="directory/files"
                            ),
                        ],
                    )
                ],
            ),
            id="specfile_path+synced_files+job_config_dict_simple+downstream_package_name",
        ),
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/package.spec"],
                "jobs": [get_job_config_dict_full()],
                "downstream_package_name": "package",
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            )
                        ],
                    )
                },
                jobs=[
                    get_job_config_full(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"],
                                dest="fedora/package.spec",
                            )
                        ],
                    )
                ],
            ),
            id="specfile_path+synced_files(spec_only)+job_config_full+downstream_package_name",
        ),
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/package.spec", "somefile"],
                "jobs": [get_job_config_dict_full()],
                "downstream_package_name": "package",
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            ),
                            SyncFilesItem(src=["somefile"], dest="somefile"),
                        ],
                    )
                },
                jobs=[
                    get_job_config_full(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"],
                                dest="fedora/package.spec",
                            ),
                            SyncFilesItem(src=["somefile"], dest="somefile"),
                        ],
                    )
                ],
            ),
            id="specfile_path+synced_files+job_config_full+downstream_package_name",
        ),
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/package.spec"],
                "jobs": [get_job_config_dict_full()],
                "upstream_project_url": "https://github.com/asd/qwe",
                "upstream_package_name": "qwe",
                "dist_git_base_url": "https://something.wicked",
                "downstream_package_name": "package",
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        upstream_project_url="https://github.com/asd/qwe",
                        upstream_package_name="qwe",
                        dist_git_base_url="https://something.wicked",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            )
                        ],
                    )
                },
                jobs=[
                    get_job_config_full(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        upstream_project_url="https://github.com/asd/qwe",
                        upstream_package_name="qwe",
                        dist_git_base_url="https://something.wicked",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"],
                                dest="fedora/package.spec",
                            )
                        ],
                    )
                ],
            ),
            id="specfile_path+synced_files+job_config_dict_full+upstream_project_url"
            "+upstream_package_name+dist_git_base_url+downstream_package_name",
        ),
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "actions": {
                    "pre-sync": "some/pre-sync/command --option",
                    "get-current-version": "get-me-version",
                },
                "jobs": [],
                "upstream_project_url": "https://github.com/asd/qwe",
                "upstream_package_name": "qwe",
                "dist_git_base_url": "https://something.wicked",
                "downstream_package_name": "package",
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="fedora/package.spec",
                        actions={
                            ActionName.pre_sync: "some/pre-sync/command --option",
                            ActionName.get_current_version: "get-me-version",
                        },
                        upstream_project_url="https://github.com/asd/qwe",
                        upstream_package_name="qwe",
                        dist_git_base_url="https://something.wicked",
                        downstream_package_name="package",
                    )
                },
                jobs=[],
            ),
            id="specfile_path+actions+empty_jobs+upstream_project_url"
            "+upstream_package_name+dist_git_base_url+downstream_package_name",
        ),
        pytest.param(
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/package.spec"],
                "downstream_package_name": "package",
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            )
                        ],
                    )
                },
                jobs=get_default_job_config(
                    downstream_package_name="package",
                    specfile_path="fedora/package.spec",
                    synced_files=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                ),
            ),
            id="specfile_path+synced_files+downstream_package_name",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "spec_source_id": 3,
                "jobs": [get_job_config_dict_build_for_branch()],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        spec_source_id="Source3",
                    )
                },
                jobs=[
                    get_job_config_build_for_branch(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        spec_source_id="Source3",
                    )
                ],
            ),
            id="specfile_path+get_job_config_dict_build_for_branch",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "sync_changelog": True,
                "jobs": [get_job_config_dict_simple()],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sync_changelog=True,
                    )
                },
                jobs=[
                    get_job_config_simple(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sync_changelog=True,
                    )
                ],
            ),
            id="sync_changelog_true",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [get_job_config_dict_simple()],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sync_changelog=False,
                    )
                },
                jobs=[
                    get_job_config_simple(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sync_changelog=False,
                    )
                ],
            ),
            id="sync_changelog_false_by_default",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "create_sync_note": False,
                "jobs": [get_job_config_dict_simple()],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        create_sync_note=False,
                    )
                },
                jobs=[
                    get_job_config_simple(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        create_sync_note=False,
                    )
                ],
            ),
            id="create_sync_note_false",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [get_job_config_dict_simple()],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        create_sync_note=True,
                    )
                },
                jobs=[
                    get_job_config_simple(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        create_sync_note=True,
                    )
                ],
            ),
            id="create_sync_note_true_by_default",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "sources": [
                    {
                        "path": "rsync-3.1.3.tar.gz",
                        "url": "https://git.centos.org/sources/rsync/c8s/82e7829",
                    }
                ],
                "jobs": [],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sources=[
                            SourcesItem(
                                path="rsync-3.1.3.tar.gz",
                                url="https://git.centos.org/sources/rsync/c8s/82e7829",
                            ),
                        ],
                    )
                },
                jobs=[],
            ),
            id="sources",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "copr_build",
                        "trigger": "release",
                        "fmf_url": "https://example.com",
                        "fmf_ref": "test_ref",
                    },
                ],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sync_changelog=False,
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.release,
                        packages={
                            "package": CommonPackageConfig(
                                downstream_package_name="package",
                                specfile_path="fedora/package.spec",
                                sync_changelog=False,
                                fmf_url="https://example.com",
                                fmf_ref="test_ref",
                            )
                        },
                    ),
                ],
            ),
            id="sync_changelog_false_by_default",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "copr_build",
                        "trigger": "release",
                        "tmt_plan": "^packit!",
                        "tf_post_install_script": "echo 'hi packit!'",
                    },
                ],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        sync_changelog=False,
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.release,
                        packages={
                            "package": CommonPackageConfig(
                                downstream_package_name="package",
                                specfile_path="fedora/package.spec",
                                sync_changelog=False,
                                tmt_plan="^packit!",
                                tf_post_install_script="echo 'hi packit!'",
                            )
                        },
                    ),
                ],
            ),
            id="extra_tf_api_parameters",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "vm_image_build",
                        "trigger": "pull_request",
                        "image_distribution": "rhel-90",
                        "image_request": {
                            "architecture": "x86_64",
                            "image_type": "aws",
                            "upload_request": {
                                "options": {"share_with_accounts": ["123456789012"]},
                                "type": "aws",
                            },
                        },
                        "image_customizations": {
                            "packages": ["peddle", "board"],
                        },
                    }
                ],
            },
            PackageConfig(
                # parsing makes it inherit: in here we need to be explicit
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.vm_image_build,
                        trigger=JobConfigTriggerType.pull_request,
                        packages={
                            "package": CommonPackageConfig(
                                downstream_package_name="package",
                                specfile_path="fedora/package.spec",
                                image_distribution="rhel-90",
                                image_request={
                                    "architecture": "x86_64",
                                    "image_type": "aws",
                                    "upload_request": {
                                        "options": {
                                            "share_with_accounts": ["123456789012"]
                                        },
                                        "type": "aws",
                                    },
                                },
                                image_customizations={
                                    "packages": ["peddle", "board"],
                                },
                            )
                        },
                    ),
                ],
            ),
            id="vm-image-build",
        ),
    ],
)
def test_package_config_parse(raw, expected):
    package_config = PackageConfig.get_from_dict(raw_dict=raw)
    assert package_config
    # tests for https://github.com/packit/packit-service/pull/342
    if expected.jobs:
        for j in package_config.jobs:
            assert j.type
    assert package_config == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [
                    {
                        "job": "copr_build",
                        "trigger": "release",
                        "specfile_path": "somewhere/package.spec",
                    }
                ],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.release,
                        packages={
                            "package": CommonPackageConfig(
                                downstream_package_name="package",
                                specfile_path="somewhere/package.spec",
                            )
                        },
                    )
                ],
            ),
            id="override-specfile_path",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "files_to_sync": ["x", "y"],
                "actions": {"post-upstream-clone": "ls"},
                "spec_source_id": "Source0",
                "targets": ["fedora-36"],
                "jobs": [
                    {
                        "job": "copr_build",
                        "trigger": "release",
                        "specfile_path": "somewhere/package.spec",
                        "files_to_sync": ["a", "b", "c"],
                        "actions": {"create-archive": "ls"},
                        "spec_source_id": "Source1",
                    }
                ],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        downstream_package_name="package",
                        specfile_path="fedora/package.spec",
                        files_to_sync=[SyncFilesItem([x], x) for x in ("x", "y")],
                        actions={ActionName.post_upstream_clone: "ls"},
                        _targets=["fedora-36"],
                    )
                },
                jobs=[
                    JobConfig(
                        type=JobType.copr_build,
                        trigger=JobConfigTriggerType.release,
                        packages={
                            "package": CommonPackageConfig(
                                downstream_package_name="package",
                                specfile_path="somewhere/package.spec",
                                files_to_sync=[
                                    SyncFilesItem([x], x) for x in ("a", "b", "c")
                                ],
                                actions={ActionName.create_archive: "ls"},
                                _targets=["fedora-36"],
                                spec_source_id="Source1",
                            )
                        },
                    ),
                ],
            ),
            id="override-alot",
        ),
    ],
)
def test_package_config_overrides(raw, expected):
    package_config = PackageConfig.get_from_dict(raw_dict=raw)
    assert package_config == expected


@pytest.mark.parametrize(
    "raw,err_message",
    [
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [{"job": "build", "trigger": "release", "actions": ["a"]}],
            },
            "'dict' required, got <class 'list'>.",
            id="bad_actions",
        ),
        pytest.param(
            {
                "downstream_package_name": "package",
                "specfile_path": "fedora/package.spec",
                "jobs": [{"job": "build", "trigger": "release", "synced_files": "a"}],
            },
            "ValidationError",
            id="bad_synced_files",
        ),
    ],
)
def test_package_config_overrides_bad(raw, err_message):
    with pytest.raises(ValidationError) as ex:
        PackageConfig.get_from_dict(raw_dict=raw)
    assert err_message in str(ex)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            {
                "specfile_path": "fedora/package.spec",
                "synced_files": ["fedora/package.spec"],
                "jobs": [],
            },
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        specfile_path="fedora/package.spec",
                        synced_files=[
                            SyncFilesItem(
                                src=["fedora/package.spec"], dest="fedora/package.spec"
                            )
                        ],
                        downstream_package_name="package",
                        upstream_package_name="package",
                    )
                },
            ),
        )
    ],
)
def test_package_config_upstream_and_downstream_package_names(raw, expected):
    package_config = PackageConfig.get_from_dict(raw_dict=raw, repo_name="package")
    assert package_config
    assert package_config == expected


def test_dist_git_package_url():
    di = {
        "dist_git_base_url": "https://packit.dev/",
        "downstream_package_name": "packit",
        "dist_git_namespace": "awesome",
        "synced_files": ["fedora/foobar.spec"],
        "specfile_path": "fedora/package.spec",
        "create_pr": False,
    }
    new_pc = PackageConfig.get_from_dict(di)
    pc = PackageConfig(
        packages={
            "packit": CommonPackageConfig(
                dist_git_base_url="https://packit.dev/",
                downstream_package_name="packit",
                dist_git_namespace="awesome",
                synced_files=[
                    SyncFilesItem(src=["fedora/foobar.spec"], dest="fedora/foobar.spec")
                ],
                specfile_path="fedora/package.spec",
                create_pr=False,
            )
        },
        jobs=get_default_job_config(
            dist_git_base_url="https://packit.dev/",
            downstream_package_name="packit",
            dist_git_namespace="awesome",
            synced_files=[
                SyncFilesItem(src=["fedora/foobar.spec"], dest="fedora/foobar.spec")
            ],
            specfile_path="fedora/package.spec",
            create_pr=False,
        ),
    )
    assert new_pc.specfile_path.endswith("fedora/package.spec")
    assert pc.specfile_path.endswith("fedora/package.spec")
    assert pc == new_pc
    assert pc.dist_git_package_url == "https://packit.dev/awesome/packit.git"
    assert new_pc.dist_git_package_url == "https://packit.dev/awesome/packit.git"
    assert not pc.create_pr


@pytest.mark.parametrize(
    "content,project,spec_path",
    [
        (
            "synced_files:\n"
            "  - packit.spec\n"
            "  - src: .packit.yaml\n"
            "    dest: .packit2.yaml",
            GitProject(repo="packit", service=GitService(), namespace=""),
            "packit.spec",
        ),
        (
            "synced_files:\n"
            "  - packit.spec\n"
            "  - src: .packit.yaml\n"
            "    dest: .packit2.yaml",
            GitProject(repo="packit", service=GitService(), namespace=""),
            "packit.spec",
        ),
    ],
)
def test_get_package_config_from_repo(
    content,
    project: GitProject,
    spec_path: Optional[str],
):
    gp = flexmock(GitProject)
    gp.should_receive("full_repo_name").and_return("a/b")
    gp.should_receive("get_file_content").and_return(content)
    # TODO(csomh): add this back, once we search for the specfile when
    # downstream_package_name was not provided by the _user_.
    # gp.should_receive("get_files").and_return(["packit.spec"]).once()
    config = get_package_config_from_repo(project=project)
    assert isinstance(config, PackageConfig)
    assert config.specfile_path == spec_path
    assert config.files_to_sync == [
        SyncFilesItem(src=["packit.spec"], dest="packit.spec"),
        SyncFilesItem(src=[".packit.yaml"], dest=".packit2.yaml"),
    ]
    assert config.create_pr


@pytest.mark.parametrize(
    "content, specfile_path",
    [
        ("{}", "packit.spec"),
        ("{jobs: [{job: build, trigger: commit}]}", "packit.spec"),
        (
            "{downstream_package_name: horkyze, jobs: [{job: build, trigger: commit}]}",
            "horkyze.spec",
        ),
        (
            "{upstream_package_name: slize, jobs: [{job: build, trigger: commit}]}",
            "packit.spec",
        ),
    ],
)
def test_get_package_config_from_repo_spec_file_not_defined(content, specfile_path):
    gp = flexmock(GitProject)
    gp.should_receive("full_repo_name").and_return("a/b")
    gp.should_receive("get_file_content").and_return(content)
    gp.should_receive("get_files").and_return([specfile_path])
    git_project = GitProject(repo="packit", service=GitService(), namespace="")
    config = get_package_config_from_repo(project=git_project)
    assert isinstance(config, PackageConfig)
    assert config.specfile_path == specfile_path
    assert config.create_pr
    for j in config.jobs:
        assert j.specfile_path == specfile_path
        assert j.downstream_package_name == config.downstream_package_name
        assert j.upstream_package_name == config.upstream_package_name


@pytest.mark.parametrize(
    "package_config, all_synced_files",
    [
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        config_file_path="packit.yaml",
                        specfile_path="file.spec",
                        synced_files=[
                            SyncFilesItem(src=["file.spec"], dest="file.spec")
                        ],
                    )
                },
            ),
            [
                SyncFilesItem(src=["file.spec"], dest="file.spec"),
                SyncFilesItem(src=["packit.yaml"], dest="packit.yaml"),
            ],
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        config_file_path="packit.yaml",
                        specfile_path="file.spec",
                        downstream_package_name="package",
                        synced_files=[
                            SyncFilesItem(src=["file.spec"], dest="package.spec")
                        ],
                    )
                },
            ),
            [
                SyncFilesItem(src=["file.spec"], dest="package.spec"),
                SyncFilesItem(src=["packit.yaml"], dest="packit.yaml"),
            ],
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        config_file_path="packit.yaml",
                        specfile_path="file.spec",
                        downstream_package_name="package",
                        synced_files=[SyncFilesItem(src=["file.txt"], dest="file.txt")],
                    )
                },
            ),
            [
                SyncFilesItem(src=["file.txt"], dest="file.txt"),
                SyncFilesItem(src=["file.spec"], dest="package.spec"),
                SyncFilesItem(src=["packit.yaml"], dest="packit.yaml"),
            ],
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        config_file_path="packit.yaml",
                        specfile_path="file.spec",
                        synced_files=[],
                        downstream_package_name="package",
                    )
                },
            ),
            [
                SyncFilesItem(src=["file.spec"], dest="package.spec"),
                SyncFilesItem(src=["packit.yaml"], dest="packit.yaml"),
            ],
        ),
        (
            PackageConfig(
                packages={
                    "package": CommonPackageConfig(
                        config_file_path="packit.yaml",
                        specfile_path="file.spec",
                        synced_files=[SyncFilesItem(src=["file.txt"], dest="file.txt")],
                        files_to_sync=[
                            SyncFilesItem(src=["file.spec"], dest="file.spec")
                        ],
                    )
                },
            ),
            [
                SyncFilesItem(src=["file.spec"], dest="file.spec"),
            ],
        ),
    ],
)
def test_get_all_files_to_sync(package_config, all_synced_files):
    assert package_config.get_all_files_to_sync() == all_synced_files


def test_notifications_section():
    pc = PackageConfig.get_from_dict(
        {"specfile_path": "package.spec"}, repo_name="package"
    )
    assert not pc.notifications.pull_request.successful_build


def test_get_local_specfile_path():
    assert str(get_local_specfile_path(UP_OSBUILD)) == "osbuild.spec"
    assert not get_local_specfile_path(SYNC_FILES)


@pytest.mark.parametrize(
    "directory, local_first,local_last,config_file_name,res_pc_path",
    [
        ([], False, True, None, Path.cwd() / CONFIG_FILE_NAMES[0]),
        ([], False, False, "different_conf.yaml", "different_conf.yaml"),
    ],
)
def test_get_local_package_config_path(
    directory, local_first, local_last, config_file_name, res_pc_path
):

    flexmock(PosixPath).should_receive("is_file").and_return(True)

    (
        flexmock(packit.config.package_config)
        .should_receive("load_packit_yaml")
        .with_args(Path(res_pc_path))
        .and_return(None)
    )

    (
        flexmock(packit.config.package_config)
        .should_receive("parse_loaded_config")
        .and_return(None)
    )

    get_local_package_config(
        try_local_dir_last=local_last, package_config_path=config_file_name
    )


def test_get_local_package_config_no_spec():
    """make sure specfile_path gets the proper default when not set"""
    flexmock(PosixPath).should_receive("is_file").and_return(True)

    (
        flexmock(packit.config.package_config)
        .should_receive("load_packit_yaml")
        .and_return({})
    )
    (
        flexmock(packit.config.package_config)
        .should_receive("get_local_specfile_path")
        .and_return(None)
    )

    assert (
        get_local_package_config(
            package_config_path=".packit.yaml", repo_name="cockpit"
        ).specfile_path
        == PackageConfig(
            packages={"cockpit": CommonPackageConfig(specfile_path="cockpit.spec")}
        ).specfile_path
    )


@pytest.mark.parametrize(
    "package_config",
    [
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    downstream_package_name="package",
                    upstream_package_name="package",
                    synced_files=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                )
            },
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    downstream_package_name="package",
                    upstream_package_name="package",
                    synced_files=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                    files_to_sync=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                )
            },
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    downstream_package_name="package",
                    upstream_package_name="package",
                    synced_files=[
                        SyncFilesItem(src=["fedora/p.spec"], dest="fedora/p.spec")
                    ],
                    files_to_sync=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                )
            },
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    downstream_package_name="package",
                    upstream_package_name="package",
                    files_to_sync=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                )
            },
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    downstream_package_name="package",
                    synced_files=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                )
            },
            jobs=[
                get_job_config_full(
                    specfile_path="fedora/package.spec",
                    downstream_package_name="package",
                    synced_files=[
                        SyncFilesItem(
                            src=["fedora/package.spec"], dest="fedora/package.spec"
                        )
                    ],
                )
            ],
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    actions={
                        ActionName.pre_sync: "some/pre-sync/command --option",
                        ActionName.get_current_version: "get-me-version",
                    },
                    upstream_project_url="https://github.com/asd/qwe",
                    upstream_package_name="qwe",
                    dist_git_base_url="https://something.wicked",
                    downstream_package_name="package",
                    spec_source_id="Source1",
                )
            },
            jobs=[],
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    actions={
                        ActionName.pre_sync: "some/pre-sync/command --option",
                        ActionName.get_current_version: "get-me-version",
                    },
                    upstream_project_url="https://github.com/asd/qwe",
                    upstream_package_name="qwe",
                    dist_git_base_url="https://something.wicked",
                    downstream_package_name="package",
                    spec_source_id="Source1",
                    sources=[
                        SourcesItem(
                            path="rsync-3.1.3.tar.gz",
                            url="https://git.centos.org/sources/rsync/c8s/82e7829",
                        ),
                    ],
                )
            },
            jobs=[],
        ),
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    actions={
                        ActionName.pre_sync: "some/pre-sync/command --option",
                        ActionName.get_current_version: "get-me-version",
                    },
                    upstream_project_url="https://github.com/asd/qwe",
                    upstream_package_name="qwe",
                    srpm_build_deps=["make", "tar", "findutils"],
                )
            },
            jobs=[],
        ),
    ],
)
def test_serialize_and_deserialize(package_config):
    schema = PackageConfigSchema()
    serialized = schema.dump(package_config)
    new_package_config = schema.load(serialized)
    assert package_config == new_package_config


@pytest.mark.parametrize(
    "package_config",
    [
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    specfile_path="fedora/package.spec",
                    config_file_path=".packit.yaml",
                    downstream_package_name="package",
                    upstream_package_name="package",
                )
            },
        ),
    ],
)
def test_files_to_sync_after_dump(package_config):
    schema = PackageConfigSchema()
    assert len(package_config.get_all_files_to_sync()) == 2
    serialized = schema.dump(package_config)
    new_package_config = schema.load(serialized)
    assert len(new_package_config.get_all_files_to_sync()) == 2


def test_get_specfile_sync_files_item():
    pc = PackageConfig(
        packages={
            "ogr": CommonPackageConfig(
                specfile_path="fedora/python-ogr.spec",
                downstream_package_name="python-ogr",
            )
        },
    )
    upstream_specfile_path = "fedora/python-ogr.spec"
    downstream_specfile_path = "python-ogr.spec"

    assert pc.get_specfile_sync_files_item() == SyncFilesItem(
        src=[upstream_specfile_path], dest=downstream_specfile_path
    )
    assert pc.get_specfile_sync_files_item(from_downstream=True) == SyncFilesItem(
        src=[downstream_specfile_path], dest=upstream_specfile_path
    )


def test_get_specfile_sync_files_nodownstreamname_item():
    pc = PackageConfig(
        packages={
            "package": CommonPackageConfig(specfile_path="fedora/python-ogr.spec")
        }
    )
    upstream_specfile_path = "fedora/python-ogr.spec"
    downstream_specfile_path = "python-ogr.spec"

    assert pc.get_specfile_sync_files_item() == SyncFilesItem(
        src=[upstream_specfile_path], dest=downstream_specfile_path
    )
    assert pc.get_specfile_sync_files_item(from_downstream=True) == SyncFilesItem(
        src=[downstream_specfile_path], dest=upstream_specfile_path
    )


@pytest.mark.parametrize(
    "raw",
    [
        {
            "packages": {"package": {}},
            "jobs": [
                {
                    "job": "copr_build",
                    "trigger": "release",
                    "targets": ["fedora-stable", "fedora-development"],
                }
            ],
        },
        {
            "packages": {"package": {}},
            "jobs": [
                {
                    "job": "tests",
                    "trigger": "release",
                    "targets": ["fedora-stable", "fedora-development"],
                }
            ],
        },
    ],
)
def test_package_config_specfile_not_present_raise(raw):
    with pytest.raises(ValidationError, match="'specfile_path' is not specified"):
        PackageConfig.get_from_dict(raw_dict=raw)


@pytest.mark.parametrize(
    "raw",
    [
        {
            "downstream_package_name": "package",
            "jobs": [
                {
                    "job": "tests",
                    "trigger": "commit",
                    "targets": ["fedora-stable", "fedora-development"],
                    "skip_build": True,
                }
            ],
        },
        {
            "downstream_package_name": "package",
            "jobs": [
                {
                    "job": "tests",
                    "trigger": "commit",
                    "targets": ["fedora-stable", "fedora-development"],
                    "skip_build": True,
                },
                {
                    "job": "tests",
                    "trigger": "pull_request",
                    "targets": ["fedora-stable", "fedora-development"],
                    "skip_build": True,
                },
            ],
        },
    ],
)
def test_package_config_specilfe_not_present_not_raise(raw):
    assert PackageConfig.get_from_dict(raw_dict=raw)


@pytest.mark.parametrize(
    "package_name,result", ((None, None), ("baz", "http://foo/bar/baz.git"))
)
def test_pc_dist_git_package_url_has_no_None(package_name, result):
    assert (
        PackageConfig(
            packages={
                "package": CommonPackageConfig(
                    downstream_package_name=package_name,
                    dist_git_base_url="http://foo/",
                    dist_git_namespace="bar",
                )
            },
        ).dist_git_package_url
        == result
    )

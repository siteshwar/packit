# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import logging
import os
from typing import Optional

import click

from packit.cli.types import LocalProjectParameter
from packit.cli.utils import cover_packit_exception, get_packit_api, iterate_packages
from packit.config import (
    PackageConfig,
    get_context_settings,
    pass_config,
)
from packit.config.aliases import DEPRECATED_TARGET_MAP
from packit.constants import (
    PACKAGE_LONG_OPTION,
    PACKAGE_OPTION_HELP,
    PACKAGE_SHORT_OPTION,
)
from packit.utils import sanitize_branch_name
from packit.utils.changelog_helper import ChangelogHelper

logger = logging.getLogger(__name__)


@click.command("scan-in-osh", context_settings=get_context_settings())
@pass_config
@cover_packit_exception
@iterate_packages
@click.option(
    PACKAGE_SHORT_OPTION,
    PACKAGE_LONG_OPTION,
    multiple=True,
    help=PACKAGE_OPTION_HELP.format(action="build"),
)
@click.option(
    "--target",
    help="Chroot to build in. (defaults to 'fedora-rawhide-x86_64')",
    default="fedora-rawhide-x86_64",
)
@click.option(
    "--base-srpm",
    help="Base SRPM to perform a differential build",
    default=None
)
@click.option(
    "--comment",
    help="Comment for the build",
    default="Submitted through PackIt.",
)
@click.argument("path_or_url", type=LocalProjectParameter(), default=os.path.curdir)
def scan_in_osh(
    config,
    path_or_url,
    package_config,
    target,
    base_srpm,
    comment,
):
    """
    """
    api = get_packit_api(
        config=config,
        package_config=package_config,
        local_project=path_or_url,
    )

    logger.debug(f"Base SRPM: {base_srpm}")

    build_url = api.run_osh_build(
        chroot=target,
        base_srpm=base_srpm,
        comment=comment,
    )

    logger.info(f"Scan URL: {build_url}")

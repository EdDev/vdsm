#
# Copyright 2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

from __future__ import absolute_import

import os
import platform

from .config import config


X86_64 = 'x86_64'
PPC64 = 'ppc64'
PPC64LE = 'ppc64le'
AARCH64 = 'aarch64'

SUPPORTED_ARCHITECTURES = (X86_64, PPC64, PPC64LE, AARCH64)

PAGE_SIZE_BYTES = os.sysconf('SC_PAGESIZE')


class UnsupportedArchitecture(Exception):
    def __init__(self, target_arch):
        self._target_arch = target_arch

    def __str__(self):
        return '{} is not supported architecture.'.format(self._target_arch)


def real():
    '''
    Get the system (host) CPU architecture.

    Returns:

    One of the Architecture attributes indicating the architecture that the
    system is using
    or
    raises UnsupportedArchitecture exception.

    Examples:

    current() ~> X86_64
    '''
    return _supported(platform.machine())


def effective():
    '''
    Get the target VM runtime architecture. This function exists to modify the
    architecture reported in vds capabilities and VMs. It is required because
    some functions require to know the real architecture, while the others are
    fine with fake one.

    Returns:

    The runtime architecture of VDSM
    or
    raises UnsupportedArchitecture exception.
    '''
    if config.getboolean('vars', 'fake_kvm_support'):
        return _supported(
            config.get('vars', 'fake_kvm_architecture'))
    else:
        return real()


def is_ppc(arch):
    return arch == PPC64 or arch == PPC64LE


def is_x86(arch):
    return arch == X86_64


def is_arm(arch):
    return arch == AARCH64


def _supported(target_arch):
    if target_arch not in SUPPORTED_ARCHITECTURES:
        raise UnsupportedArchitecture(target_arch)

    return target_arch

#
# Copyright 2016-2017 Red Hat, Inc.
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

from collections import defaultdict, namedtuple
import xml.etree.cElementTree as ET

from vdsm import cmdutils
from vdsm import commands
from vdsm import libvirtconnection
from vdsm.common import cache
from vdsm.common.cmdutils import CommandPath


NumaTopology = namedtuple('NumaTopology', 'topology, distances, cpu_topology')
CpuTopology = namedtuple('CpuTopology', 'sockets, cores, threads, online_cpus')


_SYSCTL = CommandPath("sysctl", "/sbin/sysctl", "/usr/sbin/sysctl")


AUTONUMA_STATUS_DISABLE = 0
AUTONUMA_STATUS_ENABLE = 1
AUTONUMA_STATUS_UNKNOWN = 2


def topology(capabilities=None):
    '''
    Get what we call 'numa topology' of the host from libvirt. This topology
    contains mapping numa cell -> (cpu ids, total memory).

    Example:
        {'0': {'cpus': [0, 1, 2, 3, 4, 10, 11, 12, 13, 14],
               'totalMemory': '32657'},
         '1': {'cpus': [5, 6, 7, 8, 9, 15, 16, 17, 18, 19],
               'totalMemory': '32768'}}
    '''
    return _numa(capabilities).topology


def distances():
    '''
    Get distances between numa nodes. The information is a mapping
    numa cell -> [distance], where distances are sorted relatively to cell id
    in ascending order.

    Example:
        {'0': [10, 21],
         '1': [21, 10]}
    '''
    return _numa().distances


def cpu_topology(capabilities=None):
    '''
    Get 'cpu topology' of the host from libvirt. This topology tries to
    summarize the cpu attributes over all numa cells. It is not reliable and
    should be reworked in future.

    Example:
        (sockets, cores, threads, online_cpus)
        (1, 10, 20, [0, 1, 2, 3, 4, 10, 11, 12, 13,
                     14, 5, 6, 7, 8, 9, 15, 16, 17, 18, 19])
    '''
    return _numa(capabilities).cpu_topology


@cache.memoized
def autonuma_status():
    '''
    Query system for autonuma status. Returns one of following:

        AUTONUMA_STATUS_DISABLE = 0
        AUTONUMA_STATUS_ENABLE = 1
        AUTONUMA_STATUS_UNKNOWN = 2
    '''
    out = _run_command(['-n', '-e', 'kernel.numa_balancing'])

    if not out:
        return AUTONUMA_STATUS_UNKNOWN
    elif out[0] == '0':
        return AUTONUMA_STATUS_DISABLE
    elif out[0] == '1':
        return AUTONUMA_STATUS_ENABLE
    else:
        return AUTONUMA_STATUS_UNKNOWN


def memory_by_cell(index):
    '''
    Get the memory stats of a specified numa node, the unit is MiB.

    :param cell: the index of numa node
    :type cell: int
    :return: dict like {'total': '49141', 'free': '46783'}
    '''
    conn = libvirtconnection.get()
    meminfo = conn.getMemoryStats(index, 0)
    meminfo['total'] = str(meminfo['total'] / 1024)
    meminfo['free'] = str(meminfo['free'] / 1024)
    return meminfo


@cache.memoized
def _numa(capabilities=None):
    if capabilities is None:
        capabilities = _get_libvirt_caps()

    topology = defaultdict(dict)
    distances = defaultdict(dict)
    sockets = set()
    siblings = set()
    online_cpus = []

    caps = ET.fromstring(capabilities)
    cells = caps.findall('.host//cells/cell')

    for cell in cells:
        cell_id = cell.get('id')
        meminfo = memory_by_cell(int(cell_id))
        topology[cell_id]['totalMemory'] = meminfo['total']
        topology[cell_id]['cpus'] = []
        distances[cell_id] = []

        for cpu in cell.findall('cpus/cpu'):
            topology[cell_id]['cpus'].append(int(cpu.get('id')))
            if cpu.get('siblings') and cpu.get('socket_id'):
                online_cpus.append(cpu.get('id'))
                sockets.add(cpu.get('socket_id'))
                siblings.add(cpu.get('siblings'))

        if cell.find('distances') is not None:
            for sibling in cell.find('distances').findall('sibling'):
                distances[cell_id].append(int(sibling.get('value')))

    cpu_topology = CpuTopology(len(sockets), len(siblings),
                               len(online_cpus), online_cpus)

    return NumaTopology(topology, distances, cpu_topology)


def _get_libvirt_caps():
    conn = libvirtconnection.get()
    return conn.getCapabilities()


def _run_command(args):
    cmd = [_SYSCTL.cmd]
    cmd.extend(args)
    rc, out, err = commands.execCmd(cmd, raw=True)
    if rc != 0:
        raise cmdutils.Error(cmd, rc, out, err)

    return out

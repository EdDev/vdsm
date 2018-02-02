# Copyright 2018 Red Hat, Inc.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA
#
# Refer to the README and COPYING files for full details of the license
#
from __future__ import absolute_import
from __future__ import division

import errno
import os
import signal

import pytest

from vdsm.common.cmdutils import exec_cmd


class TestPyWatch(object):

    def test_short_success(self):
        rc, _, _ = exec_cmd(['./py-watch', '0.2', 'true'])
        assert rc == 0

    def test_short_failure(self):
        rc, _, _ = exec_cmd(['./py-watch', '0.2', 'false'])
        assert rc == 1

    def test_timeout(self):
        rc, out, err = exec_cmd(['./py-watch', '0.1', 'sleep', '10'])
        assert b'Watched process timed out' in out
        assert rc == 128 + signal.SIGTERM

    def test_kill_grandkids(self):
        # watch a bash process that starts a grandchild bash process.
        # The grandkid bash echoes its pid and sleeps a lot.
        # on timeout, py-watch should kill the process session spawned by it.
        rc, out, err = exec_cmd([
            './py-watch', '0.2', 'bash',
            '-c', 'bash -c "readlink /proc/self; sleep 10"'])

        # assert that the internal bash no longer exist
        grandkid_pid = int(out.splitlines()[0])
        with pytest.raises(OSError) as excinfo:
            assert os.kill(grandkid_pid, 0)
        assert excinfo.value.errno == errno.ESRCH
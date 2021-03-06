# Back In Time
# Copyright (C) 2016 Taylor Raack, Germar Reitze
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
# You should have received a copy of the GNU General Public Licensealong
# with this program; if not, write to the Free Software Foundation,Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import sys
import tempfile
import unittest
from test import generic
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import config
import logger
import mount
import tools

HAS_BINDFS = tools.check_command('bindfs')

class TestLocal(generic.TestCase):

    def setUp(self):
        super(TestLocal, self).setUp()
        logger.DEBUG = '-v' in sys.argv
        self.config = config.Config()
        self.config.set_snapshots_mode('local')
        self.mount_kwargs = {}

    @unittest.skipIf(not HAS_BINDFS, 'Skip as this test requires bindfs to be installed')
    def test_can_mount_local_rw(self):
        self.internal_test(read_only = False, implicit_read_only = False)

    @unittest.skipIf(not HAS_BINDFS, 'Skip as this test requires bindfs to be installed')
    def test_can_mount_local_ro_implicitly(self):
        self.internal_test(read_only = True, implicit_read_only = True)

    @unittest.skipIf(not HAS_BINDFS, 'Skip as this test requires bindfs to be installed')
    def test_can_mount_local_ro_explicitly(self):
        self.internal_test(read_only = True, implicit_read_only = False)
 
    def internal_test(self, read_only, implicit_read_only):
        with tempfile.TemporaryDirectory() as dirpath:
            self.config.set_local_path(dirpath)

            if implicit_read_only:
                mnt = mount.Mount(cfg = self.config, tmp_mount = True)
            else:
                mnt = mount.Mount(cfg = self.config, tmp_mount = True, read_only = read_only)
            mnt.pre_mount_check(mode = 'local', first_run = True, **self.mount_kwargs)

            hash_id = ''
            try:
                hash_id = mnt.mount(mode = 'local', check = False, **self.mount_kwargs)
                full_path = os.path.expanduser(os.path.join("~",".local","share","backintime","mnt",hash_id,"mountpoint","testfile"))

                # warning - don't use os.access for checking writability
                # https://github.com/bit-team/backintime/issues/490#issuecomment-156265196
                if read_only:
                    with self.assertRaisesRegex(OSError, "Read-only file system"):
                        with open(full_path, 'wt') as f:
                            f.write('foo')
                else:
                    with open(full_path, 'wt') as f:
                        f.write('foo')
            finally:
                if hash_id != '':
                    mnt.umount(hash_id = hash_id)

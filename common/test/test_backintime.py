# Back In Time
# Copyright (C) 2016 Taylor Raack
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
import re
import subprocess
import sys
import unittest
from test import generic
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestBackInTime(generic.TestCase):

# main tests for backintime

    def setUp(self):
        super(TestBackInTime, self).setUp()

    def test_quiet_mode(self):
        self.assertEquals("", subprocess.getoutput("python3 backintime.py --quiet"))
    
    # end to end test - from BIT initialization all the way through successful snapshot on a local mount
    # test one of the highest level interfaces a user could work with - the command line
    # ensures that argument parsing, functionality, and output all work as expected
    # is NOT intended to replace individual method tests, which are incredibly useful as well
    def test_local_snapshot_is_successful(self):
        # ensure that we see full diffs of assert output if there are any
        self.maxDiff = None

        # create pristine source directory with single file
        subprocess.getoutput("chmod -R a+rwx /tmp/test && rm -rf /tmp/test")
        os.mkdir('/tmp/test')
        with open('/tmp/test/testfile', 'w') as f:
            f.write('some data')

        # create pristine snapshot directory
        subprocess.getoutput("chmod -R a+rwx /tmp/snapshots && rm -rf /tmp/snapshots")
        os.mkdir('/tmp/snapshots')

        # remove restored directory
        subprocess.getoutput("rm -rf /tmp/restored")
        
        # install proper destination filesystem structure and verify output
        output = subprocess.check_output(["./backintime","--config","test/config","check-config"])

        self.assertRegex(output.decode(), re.compile('''
Back In Time
Version: \d+.\d+.\d+ .*

Back In Time comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; type `backintime --license' for details.


 ┌────────────────────────────────┐
 │        Run mount tests         │
 └────────────────────────────────┘
Run mount tests: done

 ┌────────────────────────────────┐
 │             Mount              │
 └────────────────────────────────┘
INFO: mount local: /tmp/snapshots on .*
Mount: done

 ┌────────────────────────────────┐
 │  Check/prepair snapshot path   │
 └────────────────────────────────┘
Check/prepair snapshot path: done

 ┌────────────────────────────────┐
 │            Unmount             │
 └────────────────────────────────┘
INFO: unmount local: /tmp/snapshots from .*
Unmount: done

 ┌────────────────────────────────┐
 │          Check config          │
 └────────────────────────────────┘
Check config: done

 ┌────────────────────────────────┐
 │        Install crontab         │
 └────────────────────────────────┘
Install crontab: done

Config test/config profile 'Main profile' is fine.''', re.MULTILINE))
        
        # execute backup and verify output
        # TODO - verify exit code is 0. using check_output() hangs, not sure why. tried shell=True which doesn't help
        output = subprocess.getoutput("./backintime --config test/config backup")
        self.assertRegex(output, re.compile('''
Back In Time
Version: \d+.\d+.\d+ .*

Back In Time comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; type `backintime --license' for details.

INFO: Lock(
INFO: Inhibit Suspend started. Reason: take snapshot)?
INFO: mount local: /tmp/snapshots on .*
INFO: Take a new snapshot. Profile: 1 Main profile
INFO: Call rsync to take the snapshot
INFO: Save config file
INFO: Save permissions
INFO: Create info file
INFO: Remove backups older than: .*
INFO: Keep min free disk space: 1024 MiB
INFO: Keep min 2% free inodes
INFO: unmount local: /tmp/snapshots from .*
INFO: Unlock(
INFO: Release inhibit Suspend)?''', re.MULTILINE))

        # get snapshot id
        subprocess.check_output(["./backintime","--config","test/config","snapshots-list"])
        
        # execute restore and verify output
        # TODO - verify exit code is 0. using check_output() hangs, not sure why. tried shell=True which doesn't help
        output = subprocess.getoutput("./backintime --config test/config restore /tmp/test/testfile /tmp/restored 0")
        self.assertRegex(output, re.compile('''
Back In Time
Version: \d+.\d+.\d+ .*

Back In Time comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; type `backintime --license' for details.

INFO: mount local: /tmp/snapshots on .*

INFO: Restore: /tmp/test/testfile to: /tmp/restored.*''', re.MULTILINE))
        
        # verify that files restored are the same as those backed up
        subprocess.check_output(["diff","-r","/tmp/test","/tmp/restored"])

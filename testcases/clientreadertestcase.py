# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: t -*-
# vi: set ft=python sts=4 ts=4 sw=4 noet :

# This file is part of Fail2Ban.
#
# Fail2Ban is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Fail2Ban is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fail2Ban; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Author: Cyril Jaquier
# 
# $Revision$

__author__ = "Cyril Jaquier"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Cyril Jaquier"
__license__ = "GPL"

import os, shutil, tempfile, unittest
from client.configreader import ConfigReader
from client.jailreader import JailReader
from client.jailsreader import JailsReader

class ConfigReaderTest(unittest.TestCase):

	def setUp(self):
		"""Call before every test case."""
		self.d = tempfile.mkdtemp(prefix="f2b-temp")
		self.c = ConfigReader(basedir=self.d)

	def tearDown(self):
		"""Call after every test case."""
		shutil.rmtree(self.d)

	def _write(self, fname, value):
		# verify if we don't need to create .d directory
		if os.path.sep in fname:
			d = os.path.dirname(fname)
			d_ = os.path.join(self.d, d)
			if not os.path.exists(d_):
				os.makedirs(d_)
		open("%s/%s" % (self.d, fname), "w").write("""
[section]
option = %s
""" % value)

	def _remove(self, fname):
		os.unlink("%s/%s" % (self.d, fname))
		self.assertTrue(self.c.read('c'))	# we still should have some


	def _getoption(self, f='c'):
		self.assertTrue(self.c.read(f))	# we got some now
		return self.c.getOptions('section', [("int", 'option')])['option']


	def testInaccessibleFile(self):
		f = os.path.join(self.d, "d.conf")  # inaccessible file
		self._write('d.conf', 0)
		self.assertEqual(self._getoption('d'), 0)
		os.chmod(f, 0)
		self.assertFalse(self.c.read('d'))	# should not be readable BUT present


	def testOptionalDotDDir(self):
		self.assertFalse(self.c.read('c'))	# nothing is there yet
		self._write("c.conf", "1")
		self.assertEqual(self._getoption(), 1)
		self._write("c.conf", "2")		# overwrite
		self.assertEqual(self._getoption(), 2)
		self._write("c.local", "3")		# add override in .local
		self.assertEqual(self._getoption(), 3)
		self._write("c.d/98.conf", "998") # add 1st override in .d/
		self.assertEqual(self._getoption(), 998)
		self._write("c.d/90.conf", "990") # add previously sorted override in .d/
		self.assertEqual(self._getoption(), 998) #  should stay the same
		self._write("c.d/99.conf", "999") # now override in a way without sorting we possibly get a failure
		self.assertEqual(self._getoption(), 999)
		self._remove("c.d/99.conf")
		self.assertEqual(self._getoption(), 998)
		self._remove("c.d/98.conf")
		self.assertEqual(self._getoption(), 990)
		self._remove("c.d/90.conf")
		self.assertEqual(self._getoption(), 3)
		self._remove("c.conf")			#  we allow to stay without .conf
		self.assertEqual(self._getoption(), 3)
		self._write("c.conf", "1")
		self._remove("c.local")
		self.assertEqual(self._getoption(), 1)


class JailReaderTest(unittest.TestCase):

	def testStockSSHJail(self):
		jail = JailReader('ssh-iptables', basedir='config') # we are running tests from root project dir atm
		self.assertTrue(jail.read())
		self.assertTrue(jail.getOptions())
		self.assertFalse(jail.isEnabled())
		self.assertEqual(jail.getName(), 'ssh-iptables')

	def testSplitAction(self):
		action = "mail-whois[name=SSH]"
		expected = ['mail-whois', {'name': 'SSH'}]
		result = JailReader.splitAction(action)
		self.assertEquals(expected, result)

class JailsReaderTest(unittest.TestCase):

	def testProvidingBadBasedir(self):
		if not os.path.exists('/XXX'):
			self.assertRaises(ValueError, JailsReader, basedir='/XXX')

	def testReadStockJailConf(self):
		jails = JailsReader(basedir='config') # we are running tests from root project dir atm
		self.assertTrue(jails.read())		  # opens fine
		self.assertTrue(jails.getOptions())	  # reads fine
		comm_commands = jails.convert()
		# by default None of the jails is enabled and we get no
		# commands to communicate to the server
		self.assertEqual(comm_commands, [])


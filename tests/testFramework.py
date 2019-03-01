# Mostly copy/paste from https://github.com/PyGithub/PyGithub/blob/master/github/tests/Framework.py
# as it uses httplib in a way that breaks VCR.py. If requests were used
# (https://github.com/PyGithub/PyGithub/pull/383) we could drop this...

# ########################## Copyrights and license ############################
#                                                                              #
# Copyright 2012 Vincent Jacques <vincent@vincent-jacques.net>                 #
# Copyright 2012 Zearin <zearin@gonk.net>                                      #
# Copyright 2013 AKFish <akfish@gmail.com>                                     #
# Copyright 2013 Vincent Jacques <vincent@vincent-jacques.net>                 #
#                                                                              #
# This file is part of PyGithub. http://jacquev6.github.com/PyGithub/          #
#                                                                              #
# PyGithub is free software: you can redistribute it and/or modify it under    #
# the terms of the GNU Lesser General Public License as published by the Free  #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# PyGithub is distributed in the hope that it will be useful, but WITHOUT ANY  #
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS    #
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more #
# details.                                                                     #
#                                                                              #
# You should have received a copy of the GNU Lesser General Public License     #
# along with PyGithub. If not, see <http://www.gnu.org/licenses/>.             #
#                                                                              #
# ##############################################################################

import unittest
import github
from github.tests import Framework
import traceback, os, sys

# Uncomment this and set test_org/test_admin_token when making new tests
# Framework.activateRecordMode()

atLeastPython3 = sys.hexversion >= 0x03000000

def readLine(file):
    if atLeastPython3:
        return file.readline().decode("utf-8").strip()
    else:
        return file.readline().strip()

class TestCase(Framework.TestCase):
    test_org = "lshift"
    test_admin_token = "ADMIN_TOKEN"

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.__fileName = ""
        self.__file = None
        if self.recordMode:  # pragma no cover (Branch useful only when recording new tests, not used during automated tests)
            github.Requester.Requester.injectConnectionClasses(
                lambda ignored, *args, **kwds: Framework.RecordingHttpConnection(self.__openFile("wb"), *args, **kwds),
                lambda ignored, *args, **kwds: Framework.RecordingHttpsConnection(self.__openFile("wb"), *args, **kwds)
            )
            self.login = self.test_org
            self.oauth_token = self.test_admin_token
            # @todo Remove client_id and client_secret from ReplayData (as we already remove login, password and oauth_token)
        else:
            github.Requester.Requester.injectConnectionClasses(
                lambda ignored, *args, **kwds: Framework.ReplayingHttpConnection(self, self.__openFile("rb"), *args, **kwds),
                lambda ignored, *args, **kwds: Framework.ReplayingHttpsConnection(self, self.__openFile("rb"), *args, **kwds)
            )
            self.login = "login"
            self.oauth_token = "oauth_token"
            self.client_id = "client_id"
            self.client_secret = "client_secret"

    def __openFile(self, mode):
        for (_, _, functionName, _) in traceback.extract_stack():
            if functionName.startswith("test") or functionName == "setUp" or functionName == "tearDown":
                if functionName != "test":  # because in class Hook(Framework.TestCase), method testTest calls Hook.test
                    fileName = os.path.join(os.path.dirname(__file__), "ReplayData", self.__class__.__name__ + "." + functionName + ".txt")
        if fileName != self.__fileName:
            self.__closeReplayFileIfNeeded()
            self.__fileName = fileName
            self.__file = open(self.__fileName, mode)
        return self.__file

    def __closeReplayFileIfNeeded(self):
        if self.__file is not None:
            if not self.recordMode:  # pragma no branch (Branch useful only when recording new tests, not used during automated tests)
                self.assertEqual(readLine(self.__file), "")
            self.__file.close()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.__closeReplayFileIfNeeded()
        github.Requester.Requester.resetConnectionClasses()

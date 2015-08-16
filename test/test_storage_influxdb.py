# Copyright (c) 2015 Steve Milner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     (1) Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     (2) Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
#     (3)The name of the author may not be used to
#     endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""
Tests influxdb based storage.
"""

HAS_INFLUXDB = False
RUNNING_INFLUXDB = False

import datetime
import unittest

ENVIRON_BASE = {'REMOTE_ADDR': '127.0.0.1'}

try:
    import influxdb
    HAS_INFLUXDB = True
    DB = 'flask_track_usage'
except ImportError:
    HAS_INFLUXDB = False

try:
    influxdb.InfluxDBClient().create_database('flask_track_usage')

    RUNNING_INFLUXDB = True
except Exception, ex:
    RUNNING_INFLUXDB = False


from flask_track_usage import TrackUsage
from flask_track_usage.storage.influx import InfluxDBStorage

from . import FlaskTrackUsageTestCase


@unittest.skipUnless(HAS_INFLUXDB, "Requires influxdb")
@unittest.skipUnless(RUNNING_INFLUXDB, "Requires a running influxd instance")
class TestInfluxDBStorage(FlaskTrackUsageTestCase):
    """
    Tests InfluxDB storage while using it's own connection.
    """

    def setUp(self):
        """
        Set up an app to test with.
        """
        tmp_client = influxdb.InfluxDBClient()
        FlaskTrackUsageTestCase.setUp(self)
        self.storage = InfluxDBStorage(
            database='flask_track_usage',
        )
        self.track_usage = TrackUsage(self.app, self.storage)

    def test_influxdb_storage_data(self):
        """
        Test that data is stored in InfluxDB and retrieved correctly.
        """
        self.client.get('/', environ_base=ENVIRON_BASE)

    def test_influxdb_storage_get_usage(self):
        """
        Verify we can get usage information in expected ways.
        """
        # Make 3 requests to make sure we have enough records
        self.client.get('/', environ_base=ENVIRON_BASE)
        self.client.get('/', environ_base=ENVIRON_BASE)
        self.client.get('/', environ_base=ENVIRON_BASE)

        # Limit tests
        #assert len(self.storage.get_usage()) == 3
        #assert len(self.storage.get_usage(limit=2)) == 2
        assert len(self.storage.get_usage(limit=1)) == 1
        """
        # Page tests
        assert len(self.storage.get_usage(limit=2, page=1)) == 2
        assert len(self.storage.get_usage(limit=2, page=2)) == 1
        """
        # timing tests
        now = datetime.datetime.utcnow()
        assert len(self.storage.get_usage(start_date=now)) == 0
        assert len(self.storage.get_usage(end_date=now)) == 1
        #assert len(self.storage.get_usage(end_date=now, limit=2)) == 2

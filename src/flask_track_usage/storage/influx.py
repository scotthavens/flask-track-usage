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
Simple influxdb storage.
"""

import json
import datetime

from flask_track_usage.storage import Storage


class InfluxDBStorage(Storage):
    """
    Parent storage class for InfluxDB storage.

    .. versionadded:: 1.0.0
        SQLStorage was added.
    """

    def set_up(
            self, database, host='127.0.0.1',
            port=8086, username=None, password=None):
        """
        Sets the collection.

        :Parameters:
           - `database`: Name of the database to use.
           - `collection`: Name of the collection to use.
           - `host`: Host to conenct to. Default: 127.0.0.1
           - `port`: Port to connect to. Default: 27017
           - `username`: Optional username to authenticate with.
           - `password`: Optional password to authenticate with.
        """
        from influxdb import InfluxDBClient

        self.db = InfluxDBClient(host, port, username, password, database)

    def store(self, data):
        """
        Executed on "function call".

        :Parameters:
           - `data`: Data to store.
        """
        usage = [
            {
                "measurement": "flask_track_usage",
                "tags": {
                    "ua_browser": data['user_agent'].browser or '',
                    "ua_language": data['user_agent'].language or '',
                    "ua_platform": data['user_agent'].platform or '',
                    "ua_version": data['user_agent'].version or '',
                    "path": data["path"] or '',
                    "blueprint": data["blueprint"] or '',
                    "url": data["url"],
                },
                "time": data['date'],
                "fields": {
                    "url": data['url'],
                    "ua_browser": data['user_agent'].browser,
                    "ua_language": data['user_agent'].language,
                    "ua_platform": data['user_agent'].platform,
                    "ua_version": data['user_agent'].version,
                    "blueprint": data["blueprint"],
                    "view_args": json.dumps(
                        data["view_args"], ensure_ascii=False),
                    "status": data["status"],
                    "remote_addr": data["remote_addr"],
                    "authorization": data["authorization"],
                    "ip_info": data["ip_info"],
                    "path": data["path"],
                    "speed": data["speed"],
                    "datetime": data['date'],
                }
            }
        ]
        self.db.write_points(usage)

    def _get_usage(self, start_date=None, end_date=None, limit=500, page=1):
        """
        Implements the simple usage information by criteria in a standard form.

        :Parameters:
           - `start_date`: datetime.datetime representation of starting date
           - `end_date`: datetime.datetime representation of ending date
           - `limit`: The max amount of results to return
           - `page`: Result page number limited by `limit` number in a page
        """
        # TODO: page and limit
        if end_date is None:
            # Note: InfluxDB wants time in %Y-%m-%d %H:%M:%S
            end_date = datetime.datetime.utcnow().strftime(
                '%Y-%m-%d %H:%M:%S')
        if start_date is None:
            start_date = datetime.datetime(1970, 1, 1)
        query = (
            "select * from flask_track_usage where "
            "time > '%s' and time < '%s' limit %d;" % (
                start_date, end_date, limit))
        usage_data = []
        results = self.db.query(query)
        # tags correspond with the InfluxDB tags. Since tags are not
        # part of the fields we collect them here for use in usage_data
        try:
            tags = results.keys()[0][1]
            for r in results['flask_track_usage']:
                usage_data.append({
                    'url': tags['url'],
                    'user_agent': {
                        'browser': tags.get('ua_browser', None) or None,
                        'language': tags.get('ua_language', None) or None,
                        'platform': tags.get('ua_platform', None) or None,
                        'version': tags.get('ua_version', None) or None,
                    },
                    'blueprint': r.get('blueprint', None) or None,
                    'view_args': (
                        r['view_args'] if r['view_args'] != '{}' else None),
                    'status': int(r['status']),
                    'remote_addr': r['remote_addr'],
                    'xforwardedfor': r.get('xforwardedfor', None) or None,
                    'authorization': r['authorization'],
                    'ip_info': r.get('ip_info', None) or None,
                    'path': tags.get('path', None) or None,
                    'speed': r['speed'],
                    'date': r['datetime']
                })
        except IndexError:
            # No results
            pass
        return usage_data

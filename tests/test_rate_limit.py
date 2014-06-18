import os
import unittest
from webtest import TestApp
from nginxtest.server import NginxServer


LIBDIR = os.path.normpath(os.path.join(os.path.dirname(__file__),
                          '..', 'lib'))
LUA_SCRIPT = os.path.join(LIBDIR, 'rate_limit.lua')


_HTTP_OPTIONS = """\
  lua_package_path "%s/?.lua;;";
  lua_shared_dict stats 100k;
"""  % LIBDIR


_SERVER_OPTIONS = """\
  set $max_hits 4;
  set $throttle_time 10;
  access_by_lua_file '%s/rate_limit.lua';
""" % LIBDIR


class TestMyNginx(unittest.TestCase):

    def setUp(self):
        hello = {'path': '/hello', 'definition': 'echo "hello";'}
        world = {'path': '/world', 'definition': 'echo "world";'}

        self.nginx = NginxServer(locations=[hello, world],
                                 http_options=_HTTP_OPTIONS,
                                 server_options=_SERVER_OPTIONS)
        self.nginx.start()
        # see https://github.com/openresty/lua-nginx-module/issues/379
        self.app = TestApp(self.nginx.root_url, lint=False)

    def tearDown(self):
        self.nginx.stop()

    def test_rate(self):
        self.app.get('/hello', status=200)
        self.app.get('/hello', status=200)
        self.app.get('/world', status=429)

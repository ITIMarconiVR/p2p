#!/usr/bin/python3.7
import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/wwwlocal/p2p/wrk/src')
from app import app as application
application.secret_key = 'test'
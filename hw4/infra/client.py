import errno
import logging
import os
import re
import socket
import sys

from utils import CHUNK_SIZE, SOCKET_FILE, KVStoreError

"""
If you want to write your own test cases, you will want to look at the code in
KVStoreClient, and possibly some of the methods of its parent class.

DO NOT CHANGE ANY CODE IN THIS FILE.
"""

class BaseKVStoreClient:
    def __init__(self, log_level=logging.WARNING):
        if not os.path.exists(SOCKET_FILE):
            raise KVStoreError('Server does not seem to be running')
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self._sock.connect(SOCKET_FILE)
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                raise KVStoreError('Server does not seem to be running')
            else:
                raise e
        # TODO: implement reliable recv?
        data = self._sock.recv(CHUNK_SIZE)
        try:
            self._xid = int(data)
        except ValueError:
            self._sock.close()
            raise KVStoreError('Server did not provide valid transaction id: %r' % (data))

        self._logger = logging.getLogger('<%s %s>' % (self.__class__.__name__, self._xid))
        self._logger.setLevel(log_level)

        self._logger.debug('Constructed client')

    def reliable_send(self, msg):
        if msg == '':
            raise ValueError("msg is ''")
        try:
            return self._sock.sendall(msg)
        except socket.error as e:
            if e.errno == errno.EPIPE:
                raise KVStoreError('Connection to server was lost')
            raise e

    def recv(self):
        resp = self._sock.recv(CHUNK_SIZE)
        if resp == '':
            raise KVStoreError('Connection to server was lost')
        return resp

    def request(self, msg):
        self.reliable_send(msg)
        # TODO: implement reliable recv?
        return self.recv()

    def close(self):
        self._sock.close()
        self._logger.debug('Closed client')

class KVStoreClient(BaseKVStoreClient):
    def get(self, key):
        return self.request('GET %s' % (key))

    def put(self, key, value):
        return self.request('PUT %s %s' % (key, value))

    def commit(self):
        return self.request('COMMIT')

    def abort(self):
        return self.request('ABORT')

class KVStoreCommandLineClient(BaseKVStoreClient):
    def run(self):
        while True:
            try:
                msg = sys.stdin.readline()
            except KeyboardInterrupt:
                self.request('ABORT')
                break
            sanitized_msg = re.sub(r'\s+', ' ', msg.strip())
            if sanitized_msg == 'COMMIT':
                print self.request('COMMIT')
                break
            if sanitized_msg == 'ABORT' or sanitized_msg == 'EXIT':
                print self.request('ABORT')
                break
            print self.request(sanitized_msg)
        self.close()

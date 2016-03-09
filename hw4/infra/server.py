import asyncore
import logging
import os
import re
import socket
import time
import traceback

from utils import CHUNK_SIZE, SOCKET_FILE, KVStoreError
from student import DEADLOCK, USER, KVSTORE_CLASS, TransactionCoordinator, TransactionHandler

"""
YOU DO NOT NEED TO LOOK AT ANY CODE IN THIS FILE.
EVEN MORE IMPORTANTLY, DO NOT CHANGE ANY CODE IN THIS FILE.
"""

"""
Constants representing the current state of the handler between calls to
handle_read() and handle_write(). After data is sent in handle_write(), the
handler is WAITING. If handle_write() is still waiting for a lock, the handler
is LOCKING. After data is received in handle_read(), the handler is ABORTING,
COMMITTING, LOCKING, or RESPONDING.
"""
WAITING = 0
ABORTING = 1
COMMITTING = 2
LOCKING = 3
RESPONDING = 4

class KVStoreServerHandler(asyncore.dispatcher):
    """
    Each handler communicates with a single client. If the handler raises an
    exception, during the constructor or from a handle_*() method, then it is
    automatically closed. The handle_*() methods of all handlers (that have not
    yet been closed) are called by the polling loop whenever appropriate.
    """

    def __init__(self, sock, server, store, stats, lock_table, xid, log_level):
        """
        Initializes the handler and adds it to the polling loop. If an
        exception is raised during the constructor, then the handler is closed
        and removed from the polling loop.
        """
        self._logger = logging.getLogger('<%s %s>' % (self.__class__.__name__, xid))
        self._logger.setLevel(log_level)
        self._server = server
        self._store = store
        self._stats = stats
        # Global lock table. Each key maps to a list of four lists.
        # The first list contains txns holding the key's s lock. The second list contains txns holding the key's x lock (list length should be either 0 or 1)
        # The third list contains txns waiting to acquire the s lock. The fourth list contains txns waiting to acquire the x lock
        self._lock_table = lock_table
        self._xid = xid
        # A string storing data passed from handle_read() to handle_write().
        self._data = str(self._xid)
        # One of the state constants listed above
        self._state = RESPONDING
        # self.connected is inherited
        self._txn_handler = TransactionHandler(self._lock_table, self._xid, self._store)

        try:
            asyncore.dispatcher.__init__(self, sock)
        except:
            # Exceptions from constructor are not caught by handle_error(), so
            # we catch them in the constructor itself
            exc = traceback.format_exc()
            self._logger.error('Uncaught exception in __init__, cannot construct server handler\n%s', exc[:-1])
            self.close()
            return

        self._logger.debug('Constructed server handler')

    def reliable_send(self, msg):
        """
        asyncore.dispatcher does not have sendall, so we implement it here.
        We stop trying to send if the handler is ever closed.
        """
        if not self.connected:
            return
        sent = self.send(msg)
        while sent < len(msg) and self.connected:
            sent += self.send(msg[sent:])

    def end_transaction(self):
        """
        Marks the end of a transaction, after a COMMIT or ABORT. Notifies the
        user that the COMMIT or ABORT completed.
        """
        self.close()

    def readable(self):
        """
        handle_read() is called if readable() is True and the select syscall
        says the socket is ready to read.

        We always want to call handle_read() if there is data to be read.
        """
        return True

    def writable(self):
        """
        handle_write() is called if writable() is True and the select syscall
        says the socket is ready to write.

        We avoid calling handle_write() when there is no data to be written.
        """
        return self._state != WAITING

    def handle_read(self):
        """
        Called by the polling loop if readable() is True and the socket is
        ready to read. We read the data by calling recv(). recv() returns '' if
        the connection was closed, so we check for this explicitly. If the
        connection is still open, handle_read() must set self._data to a
        non-None value.
        """
        # TODO: implement reliable recv. Create input buffer, in case the input takes too long to arrive or arrives in multiple chunks, and delimiter to mark end of stream.
        data = self.recv(CHUNK_SIZE)

        if data == '':
            # The connection was closed (and handle_close() was already called)
            return

        if data[0] == ' ':
            self._state, self._data = RESPONDING, 'Command begins with whitespace'
            return
        if re.search(r'[^A-Za-z0-9_ ]', data):
            self._state, self._data = RESPONDING, 'Special characters in message'
            return
        tokens = data.split(' ', 3)
        if tokens[0] == 'GET':
            if len(tokens) == 2:
                key = tokens[1]
                if key == '':
                    self._state, self._data = RESPONDING, 'Bad format for GET'
                else:
                    result = self._txn_handler.perform_get(key)
                    self._stats[0] += 1
                    if result is None:
                        self._state, self._data = LOCKING, None
                    elif isinstance(result, str):
                        self._state, self._data = RESPONDING, result
                    else:
                        raise KVStoreError('T%s.perform_get() returned %r, which is not a string or None' % (self._xid, result))
            else:
                self._state, self._data = RESPONDING, 'Bad format for GET'
        elif tokens[0] == 'PUT':
            if len(tokens) == 3:
                key, value = tokens[1], tokens[2]
                if key == '' or value == '':
                    self._state, self._data = RESPONDING, 'Bad format for PUT'
                else:
                    result = self._txn_handler.perform_put(key, value)
                    self._stats[1] += 1
                    if result is None:
                        self._state, self._data = LOCKING, None
                    elif isinstance(result, str):
                        self._state, self._data = RESPONDING, result
                    else:
                        raise KVStoreError('T%s.perform_put() returned %r, which is not a string or None' % (self._xid, result))
            else:
                self._state, self._data = RESPONDING, 'Bad format for PUT'
        elif tokens[0] == 'COMMIT':
            if len(tokens) == 1:
                result = self._txn_handler.commit()
                if not isinstance(result, str):
                    raise KVStoreError('T%s.commit() returned %r, which is not a string' % (self._xid, result))
                self._state, self._data = COMMITTING, result
            else:
                self._state, self._data = RESPONDING, 'Bad format for COMMIT'
        elif tokens[0] == 'ABORT':
            if len(tokens) == 1:
                result = self._txn_handler.abort(USER)
                if not isinstance(result, str):
                    raise KVStoreError('T%s.abort() returned %r, which is not a string' % (self._xid, result))
                self._state, self._data = ABORTING, result
            else:
                self._state, self._data = RESPONDING, 'Bad format for ABORT'
        else:
            self._state, self._data = RESPONDING, 'Unrecognized command'

        self._logger.debug('Lock table is %r', self._lock_table)

    def handle_write(self):
        """
        Called by the polling loop if writable() is True and the socket is
        ready to write. We write the data by calling send().
        """
        if self._state != LOCKING:
            self.reliable_send(self._data)
            if self._state == ABORTING or self._state == COMMITTING:
                self.end_transaction()
            self._data = None
            self._state = WAITING
        else:
            # Try to acquire the necessary locks
            result = self._txn_handler.check_lock()
            if result is not None:
                if not isinstance(result, str):
                    raise KVStoreError('T%s.check_lock() returned %r, which is not a string or None' % (self._xid, result))
                self._state, self._data = RESPONDING, result

    def deadlock_abort(self):
        result = self._txn_handler.abort(DEADLOCK)
        if not isinstance(result, str):
            raise KVStoreError('T%s.abort() returned %r, which is not a string' % (self._xid, result))
        self._state, self._data = ABORTING, result

    def is_open(self):
        return self.connected

    def close(self):
        asyncore.dispatcher.close(self)
        self._server.remove_transaction(self._xid)
        self._logger.debug('Closed server handler')

    def handle_close(self):
        """
        Closes the handler and removes it from the polling loop.

        Called when the client has closed the connection. Because the polling
        loop uses the select syscall, handle_close() is called immediately
        after the connection is closed.
        """
        self._logger.debug('Client disconnected, closing server handler')
        self.close()

    def handle_error(self):
        """
        Closes the handler and removes it from the polling loop.

        Called when one of the handle_*() methods of the class raises an
        exception. Prints the stack trace and closes the handler.
        """
        exc = traceback.format_exc()
        self._logger.error('Uncaught exception, closing server handler\n%s', exc[:-1])
        self.close()

class KVStoreServer(asyncore.dispatcher):
    """
    The server listens for incoming connections from clients and spawns a
    handler to communicate with each client. The run() method of the server
    starts the polling loop.
    """

    @classmethod
    def get_poll_timeout(cls, poll_timeout, ttl, elapsed_time):
        if ttl is None:
            return poll_timeout
        else:
            return min(poll_timeout, ttl - elapsed_time)

    def __init__(self, kvstore_class=KVSTORE_CLASS, log_level=logging.WARNING, max_handlers=None):
        """
        Initializes the server. Does not start the polling loop. After the
        constructor returns, there can be no other servers.
        """
        self._logger = logging.getLogger('<%s>' % (self.__class__.__name__))
        self._logger.setLevel(log_level)
        self._remaining_handlers = max_handlers
        self._stats = [0, 0]
        self._lock_table = {}
        self._next_xid = 0
        self._store = kvstore_class()
        self._log_level = log_level
        self._txn_map = {}
        self._coordinator = TransactionCoordinator(self._lock_table)

        # Raise an exception if we can connect to an existing server. If a
        # context switch occurs in the middle of this code segment, or before
        # the socket is bound to the socket file, then this will fail. We
        # assume that the probability that the user constructs two servers in
        # two different processes at the same time is low, and we ignore this
        # edge case. It should not be a problem in any of the test files - most
        # of these only create a single instance of the server class.
        if os.path.exists(SOCKET_FILE):
            test_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                test_sock.connect(SOCKET_FILE)
                raise KVStoreError('Server seems to be running')
            except socket.error as e:
                pass
            finally:
                test_sock.close()
            os.unlink(SOCKET_FILE)

        try:
            asyncore.dispatcher.__init__(self)

            # Create socket, but do not connect to anything yet
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.set_reuse_addr()

            self.bind(SOCKET_FILE)
            self.listen(5)
        except Exception as e:
            exc = traceback.format_exc()
            self._logger.error('Uncaught exception in __init__, closing server\n%s', exc[:-1])
            self.close()
            raise e

        self._logger.debug('Constructed server')

    def remove_transaction(self, xid):
        """
        Server handler calls this when it is closed. No method in the server
        should have to call this directly.
        """
        self._txn_map.pop(xid, None)

    def run(self, check_deadlock_fn=None, poll_timeout=1.0, ttl=None):
        """
        Runs the polling loop. This does not create any separate processes or
        threads, and it only returns after all handlers and the server itself
        have been closed. For debugging purposes, we can also specify a time-
        to-live (ttl), which specifies the number of seconds that the server
        and server handlers are allowed to run before they are forcibly closed.

        This is a monkeypatched version of asyncore.loop(). This was the
        cleanest way to add the deadlock detector and ttl.
        """
        if check_deadlock_fn is None:
            check_deadlock_fn = lambda get_count, put_count: True
        start_time = time.time()
        timed_out = False
        while len(asyncore.socket_map) > 0:
            elapsed_time = time.time() - start_time
            if ttl is not None and elapsed_time > ttl:
                timed_out = True
                break
            new_poll_timeout = self.get_poll_timeout(poll_timeout, ttl, elapsed_time)
            # Run select syscall and readable() and writable() on all handlers,
            # then run handle_read() and handle_write() on appropriate handlers
            asyncore.poll(new_poll_timeout, asyncore.socket_map)
            if check_deadlock_fn(self._stats[0], self._stats[1]):
                abort_id = self._coordinator.detect_deadlocks()
                if abort_id is not None:
                    self._txn_map[abort_id].deadlock_abort()
        for fd, obj in asyncore.socket_map.items():
            if obj != self:
                obj.close()
        self.close()
        self._logger.debug('No more open connections')
        if timed_out:
            raise KVStoreError('Server timed out')

    def readable(self):
        """
        handle_accept() is called if readable() is True and the select syscall
        says the socket is ready to read.

        We always want to call handle_accept() if there is data to be read.
        """
        return True

    def writable(self):
        """
        handle_write() is called if writable() is True and the select syscall
        says the socket is ready to write.

        We never want to call handle_write().
        """
        return False

    def handle_accept(self):
        """
        Accepts a connection from a client, and spawns a new handler to perform
        all future communication with that client. The handler is closed
        immediately if an exception occurs in the constructor, otherwise it
        is added to the polling loop.
        """
        pair = self.accept()
        if pair is not None:
            sock, _ = pair
            self._logger.debug('Accepted connection')
            xid = self._next_xid
            self._next_xid += 1
            # After it is initialized, the handler only interacts with the
            # server through the variables passed (by reference) into the
            # constructor
            server_handler = KVStoreServerHandler(sock, self, self._store, self._stats, self._lock_table, xid, self._log_level)
            if server_handler.is_open():
                # Constructor did not raise an exception
                self._txn_map[xid] = server_handler
        if self._remaining_handlers is not None:
            self._remaining_handlers -= 1
            if self._remaining_handlers == 0:
                self.handle_close()

    def close(self):
        asyncore.dispatcher.close(self)
        self._logger.debug('Closed server')

    def handle_close(self):
        """
        Closes the server and removes it from the polling loop. If handlers
        have not been closed yet, then run() will not return.

        Called when the server has created the maximum number of handlers.
        """
        self._logger.debug('Server is not accepting more connections')
        self.close()

    def handle_error(self):
        """
        Closes the server and removes it from the polling loop. If handlers
        have not been closed yet, then run() will not return.

        Called when one of the handle_*() methods of the class raises an
        exception. Prints the stack trace and closes the server.
        """
        exc = traceback.format_exc()
        self._logger.error('Uncaught exception, closing server\n%s', exc[:-1])
        self.close()

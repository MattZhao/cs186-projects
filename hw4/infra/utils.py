import logging
import os
import stat

# Maximum number of bytes received at one time from socket
CHUNK_SIZE = 1024
SOCKET_FILE = './uds_socket'

class KVStoreError(Exception):
    pass

# We want this to happen only once per process, so we perform it here, rather
# than in the server and client classes (which are constructed multiple times
# in unit tests)
logging.basicConfig(format='%(name)s %(message)s')

# Check that socket is accessible
base_dir, _ = os.path.split(SOCKET_FILE)
if base_dir == '':
    raise KVStoreError("If SOCKET_FILE is in current directory, remember to put './' at the beginning")
if not os.path.isdir(base_dir) or not os.access(base_dir, os.W_OK | os.X_OK):
    raise KVStoreError('Cannot write to %s: %s is not an accessible directory, or is missing write or execute permission' % (SOCKET_FILE, base_dir))
if os.path.exists(SOCKET_FILE):
    mode = os.stat(SOCKET_FILE).st_mode
    if not stat.S_ISSOCK(mode):
        raise KVStoreError('%s exists and is not a socket link' % (SOCKET_FILE))

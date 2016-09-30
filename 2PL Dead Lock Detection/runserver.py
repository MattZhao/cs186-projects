from infra.server import KVStoreServer

"""
You can start the server by simply running this file on the command line.
"""

def main():
    server = KVStoreServer()
    server.run()

if __name__ == '__main__':
    main()

from infra.client import KVStoreCommandLineClient

"""
You can start a client by simply running this file on the command line.
"""

def main():
    client = KVStoreCommandLineClient()
    client.run()

if __name__ == '__main__':
    main()

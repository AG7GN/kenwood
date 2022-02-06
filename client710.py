#!/usr/bin/env python3
import xmlrpc.client
import sys
import signal
from socket import gaierror
from socket import timeout
from common710 import XMLRPC_PORT

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "1.0.1"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"
SERVER_HOST = 'localhost'


def sigint_handler(_, __):
    sys.exit(0)


class TimeoutTransport(xmlrpc.client.SafeTransport):
    def __init__(self, timeout=15, context=None, use_datetime=0):
        xmlrpc.client.Transport.__init__(self, use_datetime)
        self._timeout = timeout
        self.context = context

    def make_connection(self, host):
        conn = xmlrpc.client.Transport.make_connection(self, host)
        conn.timeout = self._timeout
        return conn


if __name__ == "__main__":
    import argparse

    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(prog='client710.py',
                                     description=f"XML-RPC client for 710.py",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {__version__}")
    parser.add_argument("-s", "--server",
                        type=str, default=SERVER_HOST,
                        help="Hostname or IP address of XML-RPC server")
    parser.add_argument("-x", "--xmlport", type=int,
                        choices=range(1024, 65536),
                        metavar="[1024-65535]", default=XMLRPC_PORT,
                        help="TCP port on which XML-RPC server is listening.")
    parser.add_argument('command', metavar='command', type=str,
                        help="CAT command to send to 710.py")

    arg_info = parser.parse_args()

    transport_xml = TimeoutTransport(timeout=10)
    with xmlrpc.client.ServerProxy(f"http://{arg_info.server}:{arg_info.xmlport}/RPC2",
                                   transport=transport_xml) as proxy:
        try:
            print(f"{proxy.rig.command(arg_info.command)}")
        except xmlrpc.client.Fault as error:
            print(f"xmlrpc fault: {error}", file=sys.stderr)
            sys.exit(1)
        except (gaierror, ConnectionRefusedError) as error:
            print(f"Unable to connect to http://{arg_info.server}:{arg_info.xmlport}/RPC2",
                  file=sys.stderr)
            sys.exit(1)
        except timeout as error:
            print(f"Connection timeout to http://{arg_info.server}:{arg_info.xmlport}/RPC2",
                  file=sys.stderr)
            sys.exit(1)
    sys.exit(0)

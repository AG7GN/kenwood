import re
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from common710 import within_frequency_limits
from common710 import MODULATION_DICT
# import psutil
# from os import kill
# from signal import SIGTERM

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2023, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "1.0.8"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"
_STATES = ('CLOSE_WAIT', 'ESTABLISHED')


class SimpleThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    """
    Implements a threaded XMLRPC server so more than one client
    can connect at a time.
    """
    pass
    # ThreadingMixIn.block_on_close = True


class RigXMLRPC(object):
    """
    Implements a simple XMLRPC server that appears to clients as
    Flrig, allowing Fldigi and Hamlib and other apps to control
    Kenwood TM-D710G and TM-V71A radios.
    """
    class RequestHandler(SimpleXMLRPCRequestHandler):
        # Restrict to a particular path.
        rpc_paths = ('/', '/RPC2')
        # Specify HTTP/1.1, so we can use a single HTTP session
        protocol_version = 'HTTP/1.1'

        def decode_request_content(self, data):
            """
            Override the decode_request_content method which allows removal
            of clientid if present in POST from client
            :param data: string to examine
            :return:
            """
            data = SimpleXMLRPCRequestHandler.decode_request_content(self,
                                                                     data)
            data = re.sub(b'<\?clientid=.*\?>', b'', data)
            return data

    def __init__(self, port: int, rig, cmd_queue):
        self.port = port
        self.rig = rig
        self.cmd_queue = cmd_queue
        self.rpc_server = \
            SimpleThreadedXMLRPCServer(('0.0.0.0', self.port),
                                       allow_none=True,
                                       requestHandler=self.RequestHandler,
                                       logRequests=False)
        self.rpc_server.register_introspection_functions()

        # Register a function under a different name
        def get_xcvr():
            return self.rig.info['model']
        self.rpc_server.register_function(get_xcvr, 'rig.get_xcvr')

        def get_modes():
            return list(MODULATION_DICT['map'].values())
        self.rpc_server.register_function(get_modes, 'rig.get_modes')

        def get_bws():
            return "bandwidth", "NONE"
        self.rpc_server.register_function(get_bws, 'rig.get_bws')

        def get_mode():
            rig_d = self.rig.get_dictionary()
            data_side = rig_d['data_side']
            return rig_d[data_side]['modulation']
        self.rpc_server.register_function(get_mode, 'rig.get_mode')
        self.rpc_server.register_function(get_mode, 'rig.get_modeA')

        def set_mode(mode: str):
            rig_d = self.rig.get_dictionary()
            data_side = rig_d['data_side']
            self.cmd_queue.put(['modulation', data_side,
                                MODULATION_DICT['inv'][mode]])
            return rig_d[data_side]['modulation']
        self.rpc_server.register_function(set_mode, 'rig.set_mode')
        self.rpc_server.register_function(get_mode, 'rig.set_modeA')
        self.rpc_server.register_function(get_mode, 'rig.set_modeB')

        def get_ab():
            # Always return "A" side because the notion of A and B
            # on these radios is not compatible one side being
            # designated as the data side.
            return "A"
        self.rpc_server.register_function(get_ab, 'rig.get_AB')

        def get_sideband():
            # There isn't a sideband, so always return U as a placeholder
            return "U"
        self.rpc_server.register_function(get_sideband, 'rig.get_sideband')

        def get_bw():
            return '', ''
        self.rpc_server.register_function(get_bw, 'rig.get_bw')

        def get_bwa():
            return 3000
        self.rpc_server.register_function(get_bwa, 'rig.get_bwA')

        def get_ptt():
            return self.rig.get_ptt()
        self.rpc_server.register_function(get_ptt, 'rig.get_ptt')

        def set_ptt(ptt: int):
            self.rig.set_ptt(ptt)
            return ''
        self.rpc_server.register_function(set_ptt, 'rig.set_ptt')

        def get_frequency():
            rig_d = self.rig.get_dictionary()
            data_side = rig_d['data_side']
            # For some reason, fldigi only works if frequency is returned
            # as a string.
            return str(int(float(rig_d[data_side]['frequency']) * 1000000))
        self.rpc_server.register_function(get_frequency, 'rig.get_vfo')
        self.rpc_server.register_function(get_frequency, 'rig.get_vfoA')
        self.rpc_server.register_function(get_frequency, 'rig.get_vfoB')

        def set_frequency(frequency: int):
            rig_d = self.rig.get_dictionary()
            data_side = rig_d['data_side']
            freq_f = float(frequency / 1000000)
            if within_frequency_limits(data_side, freq_f):
                if rig_d[data_side]['mode'] != 'VFO':
                    self.cmd_queue.put(['mode', data_side, '0'])
                self.cmd_queue.put(['frequency', data_side, freq_f])
            return ''
        self.rpc_server.register_function(set_frequency, 'main.set_frequency')
        self.rpc_server.register_function(set_frequency, 'rig.set_frequency')
        self.rpc_server.register_function(set_frequency, 'rig.set_vfo')
        self.rpc_server.register_function(set_frequency, 'rig.set_vfoA')
        self.rpc_server.register_function(set_frequency, 'rig.set_vfoB')

        def get_smeter():
            return 0
        self.rpc_server.register_function(get_smeter, 'rig.get_smeter')

        def get_pwrmeter():
            return 0
        self.rpc_server.register_function(get_pwrmeter, 'rig.get_pwrmeter')

        def get_pwrmeter_scale():
            return 0
        self.rpc_server.register_function(get_pwrmeter_scale,
                                          'rig.get_pwrmeter_scale')

        def get_notch():
            return 0
        self.rpc_server.register_function(get_notch, 'rig.get_notch')

        def cwio_get_wpm():
            return 20
        self.rpc_server.register_function(cwio_get_wpm, 'rig.cwio_get_wpm')

        def get_info():
            return __version__
        self.rpc_server.register_function(get_info, 'rig.get_info')
        self.rpc_server.register_function(get_info, 'main.get_version')

        def get_power():
            rig_d = self.rig.get_dictionary()
            data_side = rig_d['data_side']
            power = rig_d[data_side]['frequency']
            if power == 'L':
                return 2
            elif power == 'M':
                return 20
            else:
                return 100
        self.rpc_server.register_function(get_power, 'rig.get_power')

        def run_command(cmd: str):
            """
            Handle commands received from clients that send actual
            CAT command strings rather than XML-RPC calls.
            :param cmd: string containing CAT command
            :return:
            """
            self.cmd_queue.put(['command', cmd])
            while self.rig.reply_queue.empty():
                pass
            answer = self.rig.reply_queue.get()
            self.rig.reply_queue.task_done()
            answer_len = len(answer)
            if answer_len == 1:
                return str(answer[0])
            elif answer_len == 2:
                return ' '.join(answer)
            elif answer_len > 2:
                return f"{' '.join(answer[0:2])},{','.join(answer[2:])}"
            else:
                return 'N'
        self.rpc_server.register_function(run_command, 'rig.command')

    def start(self):
        # Run the rpc_server's main loop
        self.rpc_server.serve_forever()

    def stop(self):
        # Don't kill local processes in _EXCLUDED_CLIENTS when the server
        # shuts down.
        # _EXCLUDED_CLIENTS = ('fldigi',)
        self.rpc_server.shutdown()
        # Use psutil.net_connections to extract a list of PIDs for
        # local processes that have ESTABLISHED or CLOSE-WAIT TCP
        # connections left over now that the XML-RPC server has
        # been shut down. From that list, kill those client processes
        # that are not in the _EXCLUDED_CLIENTS list.
        # leftover_pids = [tcp_conn[-1] for tcp_conn in
        #                  (psutil.net_connections(kind='tcp'))
        #                  if not set(_STATES).isdisjoint(tcp_conn)
        #                  and (tcp_conn[-1] is not None)
        #                  and (getattr(tcp_conn[4], 'port') == self.port)]
        # for pid in leftover_pids:
        #     try:
        #         with open(f"/proc/{pid}/comm", 'r') as f:
        #             # Get the name of the client process
        #             client_name = f.read().rstrip()
        #     except IOError as _:
        #         pass
        #     else:
        #         # Don't kill clients listed in _EXCLUDED_CLIENTS
        #         if client_name not in _EXCLUDED_CLIENTS:
        #             try:
        #                 kill(pid, SIGTERM)
        #             except SystemError as _:
        #                 pass

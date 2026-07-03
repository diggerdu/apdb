import socketserver

from .protocol import ProtocolError, dumps_response, error_response, loads_request


class APDBRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline()
        try:
            request = loads_request(line)
        except ProtocolError as exc:
            response = error_response({"id": None}, exc.code, exc.message)
        else:
            response = self.server.session.handle_request(request)
        self.wfile.write(dumps_response(response))


class APDBTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, session):
        self.session = session
        super().__init__(server_address, APDBRequestHandler)

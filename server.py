mport socket
import threading
import signal
import sys


config =  {
            "HOST_NAME" : "0.0.0.0",
            "BIND_PORT" : 12345,
            "MAX_REQUEST_LEN" : 1024,
            "CONNECTION_TIMEOUT" : 5
          }


class Server:

    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown)
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        self.serverSocket.listen(10)    # become a server socket
        self.__clients = {}


    def listenForClient(self):
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxy_thread, args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()
        self.shutdown(0,0)


    def proxy_thread(self, conn, client_addr):

        request = conn.recv(config['MAX_REQUEST_LEN'])
        first_line = request.split('\n')[0]                  
        url = first_line.split(' ')[1]                        

        # find the webserver and port
        http_pos = url.find("://")          # find pos of ://
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):]       

        port_pos = temp.find(":")           

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos):      
            port = 80
            webserver = temp[:webserver_pos]
        else:                                               
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]

        try:
            # create a socket to connect to the web server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(config['CONNECTION_TIMEOUT'])
            s.connect((webserver, port))
            s.sendall(request)                           

            while 1:
                data = s.recv(config['MAX_REQUEST_LEN'])          
                if (len(data) > 0):
                    conn.send(data)                               
                else:
                    break
            s.close()
            conn.close()
        except socket.error as error_msg:
            print 'ERROR: ',client_addr,error_msg
            if s:
                s.close()
            if conn:
                conn.close()


    def _getClientName(self, cli_addr):
        return "Client"


    def shutdown(self, signum, frame):
        self.serverSocket.close()
        sys.exit(0)


if __name__ == "__main__":
    server = Server(config)
    server.listenForClient()

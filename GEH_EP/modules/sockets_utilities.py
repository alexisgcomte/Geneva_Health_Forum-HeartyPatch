import socket
import sys


# def tcp_client_streamlit(host='localhost', port=12800):
# 
#     st_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     st_socket.connect((host, port))
#     
#     sys.stdout.write('Connexion established\n')
#     sys.stdout.flush()
# 
#     data_to_send = b""
# 
#     while True:
#         data_to_send = input("> ")
#         data_to_send = data_to_send.encode()
#         # On envoie le message
#         st_socket.send(data_to_send)
#         #data_received = connexion_avec_serveur.recv(1024)
#         #print(data_received.decode())
# 
#     print("Closing socket")
#     st_socket.close()
# 

class tcp_client_streamlit:

    def __init__(self, host='localhost', port=12800):

        self.st_socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.st_socket_client.connect((host, port))

        sys.stdout.write('Connexion established\n')
        sys.stdout.flush()

    def send_to_st_client(self, data_to_send=''):
        print(data_to_send)
        data_to_send = data_to_send.encode()
        print(data_to_send)
        print(data_to_send)
        self.st_socket_client.send(data_to_send)

    def close(self):
        self.st_socket_client.close()


class tcp_server_streamlit:

    def __init__(self, host='localhost', port=12800):

        self.st_socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.st_socket_server.bind((host, port))
        self.st_socket_server.listen(10)

        self.st_connexion, infos = self.st_socket_server.accept()

        sys.stdout.write('Connexion established\n')
        sys.stdout.flush()

        self.data_received = self.st_connexion.recv(1024)

    def receive_and_process(self):
        while True:
            data_decoded = self.data_received.decode()
            print(data_decoded)
            self.data_received = self.st_connexion.recv(1024)

    def close(self):
        self.st_socket_server.close()


if __name__ == "__main__":

    if sys.argv[1] == '--server':
        tcp_server_st = tcp_server_streamlit()
        tcp_server_st.receive_and_process()
    elif sys.argv[1] == '--client':
        tcp_client_st = tcp_client_streamlit()
        # tcp_client_st.st_socket_client.send(b'test')
    else:
        print("Valid arguments are '--server' and '--client'")
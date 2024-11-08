import socket
import threading
from ClientHandler import ClientHandle


def server_program():
    host = socket.gethostname()
    port = 5000  # Port to bind the server

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(4)
    print("Server is listening on port", port)

    #Input thread for server console, ensures when calling input it does not lock up the main thread
    input_thread = threading.Thread(target=Console)
    input_thread.start()

    #Connect to the RSA Encryption Server
    #encryption_server = threading.Thread(target=ConnectToRSA)
    #encryption_server.start()

    while True:
        # Accept new connection
        conn, address = server_socket.accept()

        # Start a new thread to handle each client
        client_thread = threading.Thread(target=ClientHandle(conn, address).handle_client)
        client_thread.start()

def ConnectToRSA(): #Function for a thread to use
    host = socket.gethostname()
    rsa_server = socket.socket()
    rsa_server.connect((host, 4000))
    ClientHandle.SetRSA(rsa_server)

    while True:
        try:
            rsa_server.recv(1024)
        except:
            print("Connection to RSA Server Terminated")
            rsa_server.close()
            break

#Function for input thread to use
def Console():
    command = ""
    while command.lower().strip() != 'shutdown':
        command = input("server/ ")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    server_program()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

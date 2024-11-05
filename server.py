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

    input_thread = threading.Thread(target=Console)
    input_thread.start()

    while True:
        # Accept new connection
        conn, address = server_socket.accept()

        # Start a new thread to handle each client
        client_thread = threading.Thread(target=ClientHandle(conn, address).handle_client(), args=(conn, address))
        client_thread.start()


def Console():
    command = ""
    while command.lower().strip() != 'shutdown':
        command = input("server/ ")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    server_program()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

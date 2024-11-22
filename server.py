import socket
import threading
from ClientHandler import ClientHandle
import ast




def server_program():
    host = socket.gethostname()
    port = 5000  # Port to bind the server

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(4)
    print("Server is listening on port", port)

    # Input thread for server console, ensures when calling input it does not lock up the main thread
    input_thread = threading.Thread(target=Console)
    input_thread.start()

    try:
        open("Users.txt", 'x')
    except FileExistsError:
        pass

    with open("Users.txt", 'r') as file:
        data = file.read()

        if data.strip():    # If the file is not empty, grab all users from the file
            ClientHandle.SetUserDict(ast.literal_eval(data))

        else:   # If empty, set as an empty dictionary
            ClientHandle.SetUserDict(dict([]))

    ClientHandle.SetRSA((host, 4000))


    while True:
        # Accept new connection
        conn, address = server_socket.accept()

        # Start a new thread to handle each client
        client_thread = threading.Thread(target=ClientHandle(conn, address).handle_client)
        client_thread.start()



# Function for input thread to use
def Console():
    command = ""
    while command.lower().strip() != 'shutdown':
        command = input("server/ ")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    server_program()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

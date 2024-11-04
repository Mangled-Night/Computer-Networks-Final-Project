import socket
import threading

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
        client_thread = threading.Thread(target=handle_client, args=(conn, address))
        client_thread.start()


def handle_client(conn, address):
    print("Connection from: " + str(address))
    while True:
        data = conn.recv(1024).decode()
        if not data:
            # If data is not received, close the connection
            break
        print("from connected user:", data)
        response = ' -> ' + commands(data)
        conn.send(response.encode())  # Send data to the client
    conn.close()

def Console():
    command = input("server/ ")
    while command.lower().strip() != 'shutdown':
        print("-> " + command)
        command = input("server/ ")


def commands(request):
    match request:
        case "Connect":
            return "Initiates connection from client to server with the specified files"

        case "Upload":
            return "Clients can upload files to the server. Server will prompt client if file already exists and requires user input to be overwritten"

        case "Download":
            return "Clients can download files from the server. Server will respond with error message if file does not exist."

        case "Delete":
            return "Clients can delete files from the server. Server will respond with error message if file is currently being processed or does not exist."

        case "Dir":
            return "Clients can view a list of files and subdirectories in the server’s file storage path."

        case "Subfolder":
            return "Clients can create or subfolders in the server’s file storage path"

        case _:
            return "I did not understand that command, please try again"


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    server_program()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

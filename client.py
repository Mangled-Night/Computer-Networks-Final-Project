import socket

def connect_server(host, port):
    print("Establishing a connection to the server...")
    client_socket = socket.socket()
    try:
            client_socket.connect((host, port))
            print(f"Connection established: {host} : {port}")
            return client_socket
    except ConnectionError:
        print("Unable to establish a connection to the server.")
        return None

def receive_response(client_socket):
    # receive response from server
    try:
        data = client_socket.recv(1024).decode()
        return data
    except ConnectionError:
        print("Unable to receive data.")
        return None

def send_message(client_socket, message):
    try:
        client_socket.send(message.encode())
    except ConnectionError:
        print("Unable to send data.")

def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = connect_server(host, port)  # connect to the server
    if not client_socket:
        return #exits if unable to connect

    print("Type 'disconnet' to exit.")
    message = input("Enter Command: ")

    while message.lower().strip() != 'disconnet':
        client_socket.send(message.encode())  # send message

        response = receive_response(client_socket)
        if response:
            print(f"Server response: {response}")
        message = input("Enter Command:")

    # exit
    print("Disconnecting...")
    send_message(client_socket, "Disconnected")
    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()

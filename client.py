import socket


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    states = ['Listening', 'Sending']

    message = "" # take input

    while message.lower().strip() != 'bye':
        try:
            client_socket.send(message.encode())  # send message
        except:
            client_socket.close()
            print("Connection has been terminated")
            return

        data = client_socket.recv(1024).decode()  # receive response

        if(data == ""):
            client_socket.close()
            print("Connection has been terminated")
            return

        clientData, serverState = data.split('~')
        print('Received from server: ' + clientData)  # show in terminal

        if(serverState == states[0]):
            message = input(" -> ")  # again take input


    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()
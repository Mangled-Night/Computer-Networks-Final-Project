import socket
import time


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    states = ['Listening', 'Sending', "ACK"]

    message = "" # take input

    while message.lower().strip() != 'bye':
        try:
            if (message != ""):
                client_socket.send(message.encode()) # send message
            data = client_socket.recv(1024)  # receive response
        except Exception as e:
            print(e)
            client_socket.close()
            print("Connection does not exist")
            return

        if(data == ""):
            client_socket.close()
            print("Connection has been terminated")
            return

        #clientData, serverState = data.split('~')
        print(f'Received from server: {data}')  # show in terminal
        client_socket.send("ACK".encode())


        # if(serverState == states[0]):
        #     message = input(" -> ")  # again take input
        # else:
        #     message = ""

    client_socket.close()  # close the connection




if __name__ == '__main__':
    client_program()
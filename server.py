import socket
import threading

def client_commands(conn, address): # used to connect to a single client
        print("Connection from: ", str(address)) # tells who is connecting (Ip address)
        while True:
            data = conn.recv(1024).decode() # limits amound of data by 1kb
            if not data: # if no data then break
                break
            print("Response from:", str(data))
            data = ' : ' + commands(data)
            conn.send(data.encode()) # send data

        conn.close()
        print("Connection closed")


def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    print(f"Server started on {host}:{port}") # added to let us know the server has started up

    while True:
        conn, address = server_socket.accept()
        # used to create a thread for every new client
        client_thread = threading.Thread(target=client_commands, args=(conn, address))
        client_thread.start()

    #conn, address = server_socket.accept()  # accept new connection
    #print("Connection from: " + str(address))
    #while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        #data = conn.recv(1024).decode()
        #if not data:
            # if data is not received break
            #break
        #print("from connected user: " + str(data))
        #data = ' -> ' + commands(data)
        #conn.send(data.encode())  # send data to the client

    #conn.close()  # close the connection

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

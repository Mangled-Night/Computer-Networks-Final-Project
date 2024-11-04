import socket
import threading
import os



Authentication_Server = {}


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
    if( not Authenticate(conn) ): # Failed Authentication Denies Access To Server Commands
        conn.close()
        return

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
    command = ""
    while command.lower().strip() != 'shutdown':
        command = input("server/ ")

def Authenticate(conn):
    TryCounter = 0
    Greeting = "Welcome to the Computer Networks Server! If you are a new user, press 0. If you already have a username, press 1"
    conn.send(Greeting.encode())

    while True:
        data = conn.recv(1024).decode()
        if(data == '0'):
            NewUserSetup(conn)
            Login = "Please Try to Log in With your New Account. Enter your username"
            conn.send(Login.encode())
        elif(data == '1'):
            Verification = "Please enter your username"
            conn.send(Verification.encode())
        else:
            TryAgain = "Please input either 0 for new user or 1 for current user"
            conn.send(TryAgain.encode())
            continue
        while True:
            data = conn.recv(1024)
            if(FetchUser(data)):
                user = data
                TryCounter = 0
                Verified = "User Found, please enter your password"
                conn.send(Verified.encode())
                data = conn.recv(1024)
                while True:
                    if(FetchPass(user, data)):
                        Verified = "Authentication Complete. Welcome "
                        conn.send(Verified.encode() + user)
                        return True
                    else:
                        Denied = "Incorrect Password. Please Try Again"
                        TryCounter += 1
                        if (TryCounter == 4):
                            Deny = "Failed to Authenticate, Access to Server Rejected. Connection is Closed"
                            conn.send(Deny.encode())
                            return False
                        conn.send(Denied.encode())
            else:
                Denied = "Username Not Found. Please Try Again"
                TryCounter += 1
                if (TryCounter == 4):
                    Deny = "Failed to Authenticate, Access to Server Rejected. Connection is Closed"
                    conn.send(Deny.encode())
                    return False
                conn.send(Denied.encode())


def NewUserSetup(conn):
    while True:
        enter_username = "Please Enter a Username"
        conn.send(enter_username.encode())
        user = conn.recv(1024)
        confirm = "Is this the Username that you want? y? Enter anything for no"
        conn.send(confirm.encode())
        data = conn.recv(1024).decode().lower()

        if(data == 'y'):
            while True:
                enter_password = "Please Enter a Password"
                conn.send(enter_password.encode())
                passcode = conn.recv(1024)
                confirm = "Is this the password that you want? y? Enter anything for no"
                conn.send(confirm.encode())
                data = conn.recv(1024).decode().lower()
                if(data == 'y'):
                    Authentication_Server[user] = passcode
                    return
def FetchUser(username):
    for users in Authentication_Server.keys():
        if(users.decode() == username.decode()):
            return True

    return False

def FetchPass(username, passcode):
    return Authentication_Server[username].decode() == passcode.decode()

def Failed():
   return

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

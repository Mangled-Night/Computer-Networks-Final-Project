import threading
import os
import time

class ClientHandle:
    Server = dict([])
    Lock = threading.Lock()
    states = ['Listening', 'Sending']

    def __init__(self, connection, address):
        self.conn = connection
        self.addr = address
        self.state = 'Listening'
        self.user = ''
        self.TryCounter = 0

    def handle_client(self):
        print("Connection from: " + str(self.addr))
        try:
            if( not self.Authenticate() ): # Failed Authentication Denies Access To Server Commands
                self.conn.close()
                return

            while True:
                data = self.conn.recv(1024).decode()
                if (not data):
                    # If data is not received, close the connection
                    break
                print("from connected user:", data)
                self.SendMessage(' -> ' + self.commands(data))
            self.conn.close()
        except:
            print("Connection Terminated By Host")
            del self

    def commands(self, request):
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
                Directory = ""
                for file in os.listdir():
                    Directory += '\n' + str(file)
                self.SendMessage(Directory, 0)


                return "Clients can view a list of files and subdirectories in the server’s file storage path."

            case "cd":
                return

            case "Subfolder":
                return "Clients can create or subfolders in the server’s file storage path"

            case _:
                return "I did not understand that command, please try again"

    def Authenticate(self):
        self.SendMessage ("Welcome to the Computer Networks Server! If you are a new user, press 0. "
                    "If you already have a username, press 1")

        while True:
            data = self.conn.recv(1024).decode()
            if (data == '0'):
                self.NewUserSetup()
                self.SendMessage("Please Try to Log in With your New Account. Enter your username")

            elif (data == '1'):
                self.SendMessage("Please enter your username")

            else:
                self.SendMessage("Please input either 0 for new user or 1 for current user")
                continue

            while True:
                data = self.conn.recv(1024)
                if (self.FetchUser(data)):
                    self.user = data
                    self.TryCounter = 0
                    self.SendMessage("User Found, please enter your password")
                    data = self.conn.recv(1024)
                    while True:
                        if (self.FetchPass(data)):
                            self.SendMessage("Authentication Complete. Welcome " + self.user.decode())
                            return True
                        else:
                            self.TryCounter += 1
                            if (self.TryCounter == 4):
                                self.SendMessage("Failed to Authenticate, Access to Server Rejected. Connection is Closed", 1)
                                return False
                            self.Failed("Incorrect Password. Please Try Again")

                else:
                    self.Failed("Username Not Found. Please Try Again")

    def NewUserSetup(self):
        while True:
            self.SendMessage("Please Enter a Username", 0)
            user = self.conn.recv(1024)
            self.SendMessage("Is this the Username that you want? y? Enter anything for no", 0)
            data = self.conn.recv(1024).decode().lower()

            if (data == 'y'):
                while True:
                    self.SendMessage("Please Enter a Password", 0)
                    passcode = self.conn.recv(1024)
                    self.SendMessage("Is this the password that you want? y? Enter anything for no", 0)
                    data = self.conn.recv(1024).decode().lower()

                    if (data == 'y'):
                        self.Server[user] = passcode
                        return

    def FetchUser(self, username):
        for users in self.Server.keys():
            if (users.decode() == username.decode()):
                return True

        return False

    def FetchPass(self, passcode):
        return self.Server[self.user].decode() == passcode.decode()

    def Failed(self, message):
        self.TryCounter += 1
        if (self.TryCounter == 4):
            self.SendMessage("Failed to Authenticate, Access to Server Rejected. Connection is Closed", 1)
            return False
        self.SendMessage(message)
    def SendMessage(self, message, state=0):
        self.conn.send(message.encode() + f'~{self.states[state]}'.encode())

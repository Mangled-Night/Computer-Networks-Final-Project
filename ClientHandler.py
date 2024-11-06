import threading
import os


class ClientHandle:
    _Server = dict([])
    _Lock = threading.Lock()
    _states = ['Listening', 'Sending']
    _RSAserver = None

    def __init__(self, connection, address):
        self._conn = connection
        self._addr = address
        self._user = ''
        self._TryCounter = 0

    def handle_client(self):
        print("Connection from: " + str(self._addr))
        try:
            if( not self.__Authenticate() ): # Failed Authentication Denies Access To Server Commands
                self.__Close()
                return

            while True:
                data = self._conn.recv(1024).decode()
                if (not data):
                    # If data is not received, close the connection
                    break
                print("from connected user:", data)
                self.__SendMessage(' -> ' + self.__commands(data))
            self.__Close()
        except:
            print("Connection Terminated By Host")
            self.__Close()

    def __commands(self, request):
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
                self.__SendMessage(Directory, 0)
                return "Clients can view a list of files and subdirectories in the server’s file storage path."

            case "cd":
                return

            case "Subfolder":
                return "Clients can create or subfolders in the server’s file storage path"

            case "RSA":
                self.__ContactRSA()
                return "Hello"

            case _:
                return "I did not understand that command, please try again"

    def __Authenticate(self):
        self.__SendMessage ("Welcome to the Computer Networks Server! If you are a new user, press 0. "
                    "If you already have a username, press 1")

        while True:
            data = self._conn.recv(1024).decode()
            if (data == '0'):
                self.__NewUserSetup()
                self.__SendMessage("Please Try to Log in With your New Account. Enter your username")

            elif (data == '1'):
                self.__SendMessage("Please enter your username")

            else:
                self.__SendMessage("Please input either 0 for new user or 1 for current user")
                continue

            while True:
                data = self._conn.recv(1024)
                if (self.__FetchUser(data)):
                    self._user = data
                    self._TryCounter = 0
                    self.__SendMessage("User Found, please enter your password")
                    data = self._conn.recv(1024)
                    while True:
                        if (self.__FetchPass(data)):
                            self.__SendMessage("Authentication Complete. Welcome " + self._user.decode())
                            return True
                        else:
                            if(self.__Failed("Incorrect Password. Please Try Again")):
                                return False

                else:
                    if(self.__Failed("Username Not Found. Please Try Again")):
                        return False

    def __NewUserSetup(self):
        while True:
            self.__SendMessage("Please Enter a Username", 0)
            user = self._conn.recv(1024)
            self.__SendMessage("Is this the Username that you want? y? Enter anything for no", 0)
            data = self._conn.recv(1024).decode().lower()

            if (data == 'y'):
                while True:
                    self.__SendMessage("Please Enter a Password", 0)
                    passcode = self._conn.recv(1024)
                    self.__SendMessage("Is this the password that you want? y? Enter anything for no", 0)
                    data = self._conn.recv(1024).decode().lower()

                    if (data == 'y'):
                        self._Server[user] = passcode
                        return

    def __FetchUser(self, username):
        for users in self._Server.keys():
            if (users.decode() == username.decode()):
                return True

        return False

    def __FetchPass(self, passcode):
        return self._Server[self._user].decode() == passcode.decode()

    def __Failed(self, message):
        self._TryCounter += 1
        if (self._TryCounter == 4):
            self.__SendMessage("Failed to Authenticate, Access to Server Rejected. Connection is Closed", 1)
            return True
        self.__SendMessage(message)
        return False
    def __SendMessage(self, message, state=0):
        self._conn.send(message.encode() + f'~{self._states[state]}'.encode())

    def __Close(self):
        self._conn.close()
        del self

    def __ContactRSA(self):
        message = "Hello"
        self._RSAserver.send(message.encode())

    @classmethod
    def SetRSA(cls, server):
        if(cls._RSAserver == None):
            cls._RSAserver = server



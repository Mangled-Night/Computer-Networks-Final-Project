import threading
import os
import socket


class ClientHandle:
    # Static Variables for all client threads to use
    _Server = dict([])
    _Lock = threading.Lock()
    _states = ['Listening', 'Sending']
    _RSAServer = None

    # initalize the class and create local variables
    def __init__(self, connection, address):
        self._conn = connection
        self._addr = address
        self._user = ''
        self._TryCounter = 0
        self._dirDepth = 0
        self._dir = ''

    # Main loop to handle client requests
    def handle_client(self):
        print("Connection from: " + str(self._addr))
        try:
            if (not self.__Authenticate()):  # Failed Authentication Denies Access To Server Commands
                self.__Close()
                return

            while True:
                data = self.__ReciveMessage()
                if (not data):
                    # If data is not received, close the connection
                    break
                print("from connected user:", data)
                command, _, request = data.partition(" ")
                print(f'{command} {request}')
                self.__commands(command, request)

            self.__Close()
        except ConnectionResetError or socket.error:  # Runs when client terminates the connection
            print("Connection Terminated By Host")
            self.__Close()
        # except Exception as e:
        #     print(e)
        #     print("Internal Server Error. Closing Connection")
        #     self.__Close()

    def __commands(self, command, data):  # Sends commands to their respective helper function
        match command.lower():
            case "upload":
                # "Clients can upload files to the server. Server will prompt client if file already exists and
                # requires user input to be overwritten"
                self.__Upload(data)

            case "download":
                # "Clients can download files from the server. Server will respond with error message if file does
                # not exist."
                self.__Download(data)

            case "delete":
                return ("Clients can delete files from the server. Server will respond with error message if file is "
                        "currently being processed or does not exist.")

            case "dir":
                # "Clients can view a list of files and subdirectories in the server’s file storage path."
                self.__SendDir()

            case "cd":
                # Changes the current directory
                return

            case "subfolder":
                return "Clients can create or subfolders in the server’s file storage path"

            case "rsa":
                try:
                    self.__ContactRSA()
                except:
                    self.__SendMessage("RSA Server Connection is Terminated")

                return "Hello"

            case _:
                return "I did not understand that command, please try again"

# Authentication Methods
    def __Authenticate(self):  # Client Authentication Preformed Here
        self.__SendMessage("Welcome to the Computer Networks Server! If you are a new user, press 0. "
                           "If you already have a username, press 1")

        while True:
            data = self.__ReciveMessage()
            if (data == '0'):  # This is a new user, set up an account for them
                self.__NewUserSetup()
                self.__SendMessage("Please Try to Log in With your New Account. Enter your username")

            elif (data == '1'):  # This is a current user, go through log in process
                self.__SendMessage("Please enter your username")

            else:  # Handle any mis-inputs
                self.__SendMessage("Please input either 0 for new user or 1 for current user")
                continue

            while True:
                data = self.__ReciveMessage(False)
                if (self.__FetchUser(data)):  # Tries to See if Username is in the dictionary
                    self._user = data
                    self._TryCounter = 0
                    self.__SendMessage("User Found, please enter your password")
                    while True:

                        data = self.__ReciveMessage(False)
                        if (self.__FetchPass(data)):  # Tries to see if password matches the password associated
                            # with that user
                            self.__SendMessage("Authentication Complete. Welcome " + self._user.decode())
                            self._dir = os.path.join(os.getcwd(), self._user.decode())
                            return True

                        else:  # Failed Password Attempt
                            if (self.__Failed("Incorrect Password. Please Try Again")):
                                return False

                else:  # Failed attempt at getting username
                    if (self.__Failed("Username Not Found. Please Try Again")):
                        return False

    def __NewUserSetup(self):  # Set up a user account if client doesn't have one
        while True:
            self.__SendMessage("Please Enter a Username")
            user = self.__ReciveMessage(False)
            self.__SendMessage("Is this the Username that you want? y? Enter anything for no")
            data = self.__ReciveMessage().lower()  # Receives and ensures that this is the username they want

            if (data == 'y'):
                if (self.__FetchUser(user)):  # Checks to see if username has been taken
                    self.__SendMessage("This username is taken", 1)
                    continue

                while True:
                    self.__SendMessage("Please Enter a Password")
                    passcode = self.__ReciveMessage(False)
                    self.__SendMessage("Is this the password that you want? y? Enter anything for no")
                    data = self.__ReciveMessage().lower()  # Receives and ensures that this is the password they want

                    if (data == 'y'):
                        self._Server[user] = passcode  # Adds username and password to dictionary
                        os.mkdir(user.decode())  # Makes a directory for that user within the Server
                        return

    def __FetchUser(self, username):  # Gets a username from the dictionary
        if (self._Server.get(username) != None):  # If get Returns a user, then that username is in the dictionary
            return True
        else:
            return False

    def __FetchPass(self, passcode):  # Gets a password from the dictionary
        return self._Server[self._user].decode() == passcode.decode()  # Sees if the given psassword matches
        # the one in the dictonary

    def __Failed(self, message):  # If an authentication attempt failed
        self._TryCounter += 1
        if (self._TryCounter == 4):  # If too many authentication fails, drop the connection
            self.__SendMessage("Failed to Authenticate, Access to Server Rejected. Connection is Closed", 1)
            return True
        self.__SendMessage(message)
        return False

# General Methods
    def __SendMessage(self, message, state=0):  # Send all messages to the client here
        timeout_counter = 0
        self._conn.settimeout(5)  # After 5 seconds, connection throws a timeout
        while True:
            try:  # Try to send a message to the client and waits for an ack back from the client
                self._conn.send(message.encode() + f'~{self._states[state]}'.encode())
                ack = self._conn.recv(1024).decode()
            except socket.timeout:  # If timeout, increment the counter and resend
                timeout_counter += 1
                if (timeout_counter == 3):  # Timeout 3 times, presume unstable or dropped connection
                    print("Connection with host is unstabled or terminated")
                    self.__Close()
                    break
            else:
                if (ack == "ACK"):  # If no time out, check if we got an ack back. No ack? Resend
                    self._conn.settimeout(None)
                    break

    def __ReciveMessage(self, decode=True):  # Reccive all messages from the client here
        data = self._conn.recv(1024)
        data = data.decode() if decode else data
        return data

    # TODO Implement RSA Encryption
    def __ContactRSA(self):  # Allows the thread to contact the RSA Server
        message = "Hello"
        self._RSAServer.send(message.encode())

# Server-Client Functions
    # TODO Test the Upload Function. Need Client to Have Function
    def __Upload(self, file):  # Client Uploading a File
        # in Theory, recciving the name of the file and not the file path
        file = os.path.join(self._dir, file)
        try:
            with open(file, 'xb') as f:  # Read it in binary mode and attempt to creae a file
                while True:
                    file_data = self._conn.recv(1024).decode()
                    if not file_data:  # Stop if no more data
                        break
                    f.write(file_data)
        except FileExistsError:  # Duplicate Files cannot exist on the server
            self.__SendMessage("Error: This File Already Exists")
            return
        except:  # Error occurred during the transfer, remove the partially uploaded file
            os.remove(file)
            self.__SendMessage("Error: Something Occurred During File Transfer. Stopping the Upload")
            return

    # TODO Test the Download Function. Need Client to Have Function
    def __Download(self, file):  # Client downloading a file from the server
        # Either Receive File Name or Path
        file = os.path.join(self._dir, file)
        try:
            with open(file, 'rb') as f:  # Read the file in binary mode, no need to encode it
                while True:
                    file_data = f.read(1024)
                    self._conn.send(file_data)
                    if not file_data:  # Stop if no more data
                        break

        except FileNotFoundError:  # Could not find the file
            self.__SendMessage("Error: Cannot Find File")
            return

        except:  # Error occurred during the transfer, stop the transfer
            self.__SendMessage("Error: Something Occurred During File Transfer. Stopping the Download")
            return

    def __SendDir(self):
        Directory = ""
        for file in os.listdir(self._dir):
            Directory += '\n' + str(file)
        self.__SendMessage(Directory, 1)
        self.__SendMessage("End of Directory")

# Other Functions
    def __Close(self):  # Connection Was Closed, delete this object
        self._conn.close()
        del self

    @classmethod
    def SetRSA(cls, server):  # Sets up the connection to allow threads to talk to the server, can only be set once
        if (cls._RSAServer == None):
            cls._RSAServer = server

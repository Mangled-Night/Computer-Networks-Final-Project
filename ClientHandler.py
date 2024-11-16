import threading
import os
import socket
import shutil

class ClientHandle:
    # Static Variables for all client threads to use
    _Server = None
    _Lock = threading.Lock()
    _states = ['Listening', 'Sending']
    _RSAServer = None

    # initialize and define local variables and set up secure connection
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
                self.__SendMessage("Enter a command", 0)
                data = self.__ReciveMessage()
                if (not data):
                    # If data is not received, close the connection
                    break
                command, _, request = data.partition(" ")
                self.__commands(command, request)

            self.__Close()
        except ConnectionResetError or socket.error:  # Runs when client terminates the connection
            print("Connection Terminated By Host")
            self.__Close()
        except Exception as e:
            print(e)
            print("Internal Server Error. Closing Connection")
            self.__Close()

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
                # "Clients can delete files from the server. Server will respond with error message if file is "
                #      "currently being processed or does not exist."
                self.__Delete(data)

            case "dir":
                # "Clients can view a list of files and subdirectories in the server’s file storage path."
                self.__SendDir()

            case "cd":
                # Changes the current directory
                self.__ChangeDirectory(data)

            case "subfolder":
                # "Clients can create or folders in the server’s file storage path"
                self.__SubDir(data)
            case _:
                self.__SendMessage("I did not understand that command, please try again")

# Authentication Methods
    def __Authenticate(self):  # Client Authentication Preformed Here
        self.__SendMessage("Welcome to the Computer Networks Server! If you are a new user, press 0. "
                           "If you already have a username, press 1", 0)

        while True:
            data = self.__ReciveMessage()
            if (data == '0'):  # This is a new user, set up an account for them
                self.__NewUserSetup()
                self.__SendMessage("Please Try to Log in With your New Account. Enter your username", 0)

            elif (data == '1'):  # This is a current user, go through log in process
                self.__SendMessage("Please enter your username", 0)

            else:  # Handle any mis-inputs
                self.__SendMessage("Please input either 0 for new user or 1 for current user", 0)
                continue

            while True:
                data = self.__ReciveMessage(False)
                if (self.__FetchUser(data)):  # Tries to See if Username is in the dictionary
                    self._user = data
                    self._TryCounter = 0
                    self.__SendMessage("User Found, please enter your password", 0)
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
            self.__SendMessage("Please Enter a Username", 0)
            user = self.__ReciveMessage(False)
            self.__SendMessage("Is this the Username that you want? y? Enter anything for no", 0)
            data = self.__ReciveMessage().lower()  # Receives and ensures that this is the username they want

            if (data == 'y'):
                if (self.__FetchUser(user)):  # Checks to see if username has been taken
                    self.__SendMessage("This username is taken")
                    continue

                while True:
                    self.__SendMessage("Please Enter a Password", 0)
                    passcode = self.__ReciveMessage(False)
                    self.__SendMessage("Is this the password that you want? y? Enter anything for no", 0)
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
            self.__SendMessage("Failed to Authenticate, Access to Server Rejected. Connection is Closed")
            return True
        self.__SendMessage(message, 0)
        return False

# General Methods
    def __SendMessage(self, message, state=1):  # Send all messages to the client here
        timeout_counter = 0
        noACK = 0
        self._conn.settimeout(5)  # After 5 seconds, connection throws a timeout

        while True:
            try:  # Try to send a message to the client and waits for an ack back from the client
                self._conn.send(ciphertext)
                ack = self._conn.recv(1024)
            except socket.timeout:  # If timeout, increment the counter and resend
                timeout_counter += 1
                if (timeout_counter == 3):  # Timeout 3 times or noACK 5 times, presume unstable or dropped connection
                    print("Connection with host is unstable or terminated")
                    self.__Close()
                    break
            else:
                if (ack == "ACK"):  # If no time out, check if we got an ack back. No ack? Resend
                    self._conn.settimeout(None)
                    break
                noACK += 1  # Increment the number of times we didn't get an ACK
                if(noACK == 5):
                    print("Connection with host is unstable or terminated")
                    self.__Close()
                    break

    def __ReciveMessage(self):  # Reccive all messages from the client here
        data = self._conn.recv(1024)


        return data

    def __CheckInDir(self, target):
        return target in os.listdir(self._dir)

    # TODO Implement RSA Encryption
    def __GetKey(self, type):  # Sends a request for RSA Keys
        Encryption_socket = socket.socket()  # instantiate
        Encryption_socket.connect(self._RSAServer)  # connect to the Encryption server






# Other Functions
    def __Close(self):  # Connection Was Closed, delete this object
        self._conn.close()
        self.WriteUserData()
        del self

    @classmethod
    def SetRSA(cls, server):  # Sets up the connection to allow threads to talk to the server, can only be set once
        if (cls._RSAServer == None):
            cls._RSAServer = server
    @classmethod
    def SetUserDict(cls, dict):     # Sets us the user dictionary, can only be set once
        if(cls._Server == None):
            cls._Server = dict
    @classmethod
    def WriteUserData(cls):     # Writes the current dictionary to the Users File
        with open("Users.txt", 'w') as file:
            file.write(str(cls._Server))

# Server-Client Functions
    # TODO Test the Upload Function. Need Client to Have Function
    def __Upload(self, file):  # Client Uploading a File
        # in Theory, recciving the name of the file and not the file path. Uploads it to current directory
        file = os.path.join(self._dir, file)
        try:
            with open(file, 'xb') as f:  # Read it in binary mode and attempt to create a file
                while True:
                    file_data = self._conn.recv(1024).decode()
                    if not file_data:  # Stop if no more data
                        self.__SendMessage("File Upload Complete!")
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
        # Either Receive File Name or Path. Download from current directory
        file = os.path.join(self._dir, file)
        try:
            with open(file, 'rb') as f:  # Read the file in binary mode, no need to encode it
                while True:
                    file_data = f.read(1024)
                    self._conn.send(file_data)
                    if not file_data:  # Stop if no more data
                        self.__SendMessage("File Download Complete!")
                        break

        except FileNotFoundError:  # Could not find the file
            self.__SendMessage("Error: Cannot Find File")
            return

        except:  # Error occurred during the transfer, stop the transfer
            self.__SendMessage("Error: Something Occurred During File Transfer. Stopping the Download")
            return

    def __SendDir(self):
        Directory = self._dir
        for file in os.listdir(self._dir):
            if(not '.' in file):
                file = '.' + file
            Directory += '\n' + str(file)
        self.__SendMessage(Directory)
        self.__SendMessage("End of Directory")

    def __Delete(self, file):   # Lets the User Delete a File
        # Expects the name of the file, must also be in the current directory
        file_path = os.path.join(self._dir, file)
        if(not self.__CheckInDir(file)):  # Tries to find the file
            self.__SendMessage("Error: File Not Found")

        elif(not os.path.isfile(file_path)):    # Ensures that what was given was a file
            self.__SendMessage("Error: Must Give a File, Not a Directory")
        else:
            self.__SendMessage("Are you sure you want to delete this file? There is no undoing this action."
                               " y? Enter anything for no", 0)
            # Ensures that the user wants to delete this file
            confirmation = self.__ReciveMessage()
            if(confirmation == 'y'):    # Deletes the file
                os.remove(file_path)
                self.__SendMessage(f"{file} Has Been Removed")

    def __SubDir(self, subcommand):     # Creates or deletes a subdirectory
        # Assumes we are given the name
        command, _, target = subcommand.partition(" ")
        file_path = os.path.join(self._dir, target)

        if(os.path.isfile(file_path) or '.' in target):      # Checks if the target is a file
            self.__SendMessage("Error: Give a directory, not a file")
            return

        if(command.lower() == "create"):
            if (not self.__CheckInDir(target)):     # Checks to see if the directory already exists
                try:
                    os.mkdir(file_path)     # Try to make that Directory
                    self.__SendMessage(f"Directory {target} created.")
                except:     # Some OS are case-sensitive and some aren't, so it may or may not throw an error
                    self.__SendMessage(f"Error: Directory {target} already exists.")
            else:
                self.__SendMessage(f"Error: Directory {target} already exists.")

        elif(command.lower() == "delete"):
            if (not self.__CheckInDir(target)):     # Checks to see if the directory exists
                self.__SendMessage("Error: Cannot Find Target Directory")
            else:
                self.__SendMessage("Are you sure you want to delete this directory? "
                                   "There is no undoing this action and all files within will be lost."
                                   " y? Enter anything for no", 0)
                # Ensures that the user wants to delete this directory

                confirmation = self.__ReciveMessage()
                if (confirmation == 'y'):  # Deletes the directory
                    shutil.rmtree(file_path)
                    self.__SendMessage(f"{target} Has Been Removed")

        else:
            self.__SendMessage("Error: I did not understand that command. Either create or delete a subdirectory")

    def __ChangeDirectory(self, target):

        if (target == ".."):    # Cannot travel up if already at root
            if(self._dirDepth == 0):
                self.__SendMessage("Error: Already in Root Directory")
                return

            else:    # Travel up the directory path
                self._dirDepth -= 1
                self._dir, _, _ = self._dir.rpartition("\\")
                self.__SendMessage(f"Currently in {self._dir}")

        elif (not self.__CheckInDir(target)):  # Checks to see if the directory exists
            self.__SendMessage("Error: Cannot Find Target Directory")
            return

        else:   # Travel into a directory
            self._dir = os.path.join(self._dir, target)
            self._dirDepth += 1
            self.__SendMessage(f"Currently in {self._dir}")








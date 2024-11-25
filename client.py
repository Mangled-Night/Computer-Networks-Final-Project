import os
import socket
from fileinput import filename
from os import urandom
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
import base64


def client_program():
    upload = download = connected = False

    host = socket.gethostname()
    print(host)

    command = ''
    while command.lower().strip() != "bye":
        while not connected and command.lower().strip() != "bye":
            command = input("Enter bye to leave or Help for help. Connect: ")

            if(command.lower() == "help"):
                print("Please Enter in this format: [Host/IP] [Port]")
                continue
            elif(command.lower() == "bye"):
                continue
            else:
                host, _, port = command.partition(" ")

            try:
                client_socket = socket.socket()  # instantiate
                client_socket.connect((host, int(port)))
            except ConnectionRefusedError:
                print("The host of the IP/Port is not running/accepting connections")
            except socket.gaierror:
                print("Could not resolve hostname to an IP")
            except socket.timeout:
                print(" Could not Connect to the Server within allocated time")
            except Exception as e:
                print(e)
                print("Please Enter Using the Correct Format. Type Help for help")
            else:
                connected = True



        if (connected):
            key = OnConnect(client_socket)
            message = ''  # take input

            while message.lower().strip() != 'end':
                try:
                    if (message != ""):
                        ciphermessage = Encrypt(message, key)
                        client_socket.send(ciphermessage)  # send message

                    if message.startswith('upload'):
                        upload = True

                    elif message.startswith('download'):
                        download = True

                    data = client_socket.recv(1024)  # receive response
                except Exception as e:
                    print(e)
                    client_socket.close()
                    print("Connection does not exist")
                    break

                if (len(data) <= 16):
                    client_socket.close()
                    print("Connection has been terminated")
                    break

                plaintext = Decrypt(data, key)

                if(upload):
                    upload = False
                    if (plaintext.startswith("Upload")):
                        Upload(client_socket, message, key)
                        message = ""
                        continue

                elif(download):
                    download = False
                    if(plaintext.startswith("Download")):
                        _, buffer_size = plaintext.split('-')
                        buffer_size = int(buffer_size) + 1024
                        Download(client_socket, message, key, buffer_size)
                        message = ""
                        continue


                clientData, serverState = plaintext.split('~')
                print(f'Received from server: {clientData}')  # show in terminal
                client_socket.send(Encrypt("ACK", key))

                if (serverState == "Listening"):
                    message = input(" -> ")  # again take input
                else:
                    message = ""

            try:
                client_socket.send(Encrypt("End", key))
            except:
                pass

            client_socket.close()  # close the connection
            connected = False


def SendKeys(conn, public_key, AES_key):
    encoded_key = base64.b64encode(AES_key)
    encrypted_key = public_key.encrypt(
        encoded_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    conn.send(encrypted_key)
    return public_key


def Encrypt(plaintext, key):  # Double encrypt the message being sent
    iv = urandom(16)
    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    if (isinstance(plaintext, str)):
        # Ensure plaintext is encoded to bytes
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()  # Encrypt in AES

    else:  # plaintext is a bytes object, no need to encode
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()  # Encrypt in AES
    return iv + ciphertext


def Decrypt(ciphertext, key, isString = True):  # Decrypt only using AES
    iv = ciphertext[:16]
    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()

    plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()  # Decrypt using AES

    if(isString):
        return plaintext.decode()

    else:   # In the event, we are expecting file bytes
        return plaintext



def Upload(conn, message, key):
    file_name = message.split(' ', 1)[1]
    try:
        buffer_size = CalculateBuffer(os.path.getsize(file_name))
        conn.send(Encrypt(str(buffer_size), key))
        noACK = 0
        # Reading file and sending data to server
        with open(file_name, "rb") as fi:
            data = fi.read(buffer_size)
            while data:
                conn.send(Encrypt(data, key))
                Ack = Decrypt(conn.recv(1024), key)
                if (Ack == "ACK"):
                    data = fi.read(buffer_size)
                else:
                    noACK += 1
                    if(noACK == 3):
                        print("De-synchronized Connection With Server")
                        return

            # File is closed after data is sent
        conn.send(Encrypt("-", key))


    except FileNotFoundError:
        conn.send(Encrypt("+", key))
        print('You entered an invalid filename!\
        Please enter a valid name')

    except:
        return

def Download(conn, message, key, buffer_size):
    files_name = message.split(' ', 1)[1]
    try:
        # Reading file and sending data to server
        with open(files_name, "xb") as fil:
            conn.send(Encrypt("Download", key))
            print("Starting Download")
            while True:
                file_data = Decrypt(conn.recv(buffer_size), key, False)
                if file_data == b'-':  # Stop if no more data
                    conn.send(Encrypt("ACK", key))
                    return
                elif file_data == b'+':
                    raise EOFError
                fil.write(file_data)
                conn.send(Encrypt("ACK", key))

    except FileExistsError:
        print('This File Already Exists!')
        conn.send(Encrypt('+', key))

    except EOFError:
        os.remove(files_name)
        print("Server Request: Cancelling Download")

    except Exception as e:
        print(e)
        return


def OnConnect(conn):
    try:
        # Key Exchange for Encryption Handshake
        key = urandom(32)
        data = conn.recv(1024)
        public_key = serialization.load_pem_public_key(data)
        SendKeys(conn, public_key, key)

        return key

    except:
        print("An Error Occurred While Setting Up Connection")
        return

def CalculateBuffer(file_size):
    Min = 1024
    Max = 1024 * 63
    if(file_size == 0):
        return 1024
    return max(Min, min(file_size // 10, Max))


if __name__ == '__main__':
    client_program()

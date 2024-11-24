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
    states = ['Listening', 'Sending', "ACK"]
    message = ''  # take input
    upload = download = False

    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    # Key Exchange for Encryption Handshake
    key = urandom(32)
    data = client_socket.recv(1024)
    public_key = serialization.load_pem_public_key(data)
    SendKeys(client_socket, public_key, key)

    while message.lower().strip() != 'bye':
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
            return

        if (len(data) <= 16):
            client_socket.close()
            print("Connection has been terminated")
            return

        plaintext = Decrypt(data, key)

        if(upload):
            upload = False
            if (plaintext == "Upload"):
                Upload(client_socket, message, key)
                message = ""
                continue

        elif(download):
            download = False
            Download(client_socket, message, key)
            message = ""
            continue


        clientData, serverState = plaintext.split('~')
        print(f'Received from server: {clientData}')  # show in terminal
        client_socket.send(Encrypt("ACK", key))

        if (serverState == states[0]):
            message = input(" -> ")  # again take input
        else:
            message = ""

    client_socket.close()  # close the connection


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
    noACK = 0
    try:
        # Reading file and sending data to server
        with open(file_name, "rb") as fi:
            data = fi.read(1024)
            while data:
                conn.send(Encrypt(data, key))
                Ack = Decrypt(conn.recv(1024), key)
                if (Ack == "ACK"):
                    data = fi.read(1024)
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

def Download(conn, message, key):
    files_name = message.split(' ', 1)[1]
    try:
        # Reading file and sending data to server
        with open(files_name, "xb") as fil:
            conn.send(Encrypt("Download", key))
            print("Starting Download")
            while True:
                file_data = Decrypt(conn.recv(2048), key, False)
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

if __name__ == '__main__':
    client_program()
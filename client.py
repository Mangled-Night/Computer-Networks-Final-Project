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
import tkinter as tk
from tkinter import filedialog


files = "C:/Users/grant/PycharmProjects/pythonProject/ComNetProject/Message.txt"
def client_program():
    states = ['Listening', 'Sending', "ACK"]
    message = ""  # take input

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
                ciphermessage = Encrypt(public_key, message, key)
                client_socket.send(ciphermessage)  # send message

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
        clientData, serverState = plaintext.split('~')
        print(f'Received from server: {clientData}')  # show in terminal
        client_socket.send(Encrypt(public_key, "ACK", key))

        if (serverState == states[0]):
            message = input(" -> ")  # again take input
        else:
            message = ""
        if message == 'upload':

            root = tk.Tk()
            button = tk.Button(root, text='Open', command=UploadAction)
            button.pack()

            root.mainloop()
            try:
                # Reading file and sending data to server
                with open(filesname, "r") as file:
                    while chunk := file.read(1024):  # Read in 1KB chunks
                        client_socket.send(Encrypt(public_key, chunk, key))
                    # File is closed after data is sent
                print("File sent successfully.")
            except IOError:
                print('You entered an invalid filename!\
                       Please enter a valid name')


    client_socket.close()  # close the connection


def UploadAction(event=None):
    global filesname
    filesname = filedialog.askopenfilename()
    print('Selected:', filesname)

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

def Encrypt(public_key, plaintext, key):  # Double encrypt the message being sent
    iv = urandom(16)
    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    # Ensure plaintext is encoded to bytes
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()  # Encrypt in AES
    return iv + ciphertext


def Decrypt(ciphertext, key):  # Decrypt only using AES
    iv = ciphertext[:16]
    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()

    plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()  # Decrypt using AES
    return plaintext.decode()  # Convert bytes to string after decryption


if __name__ == '__main__':
    client_program()

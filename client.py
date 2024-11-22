import socket
from os import urandom
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
import base64


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
                ciphermessage = Encrpyt(public_key, message, key)
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
        client_socket.send(Encrpyt(public_key, "ACK", key))

        if (serverState == states[0]):
            message = input(" -> ")  # again take input
        else:
            message = ""

        if message.startswith('upload'):
            file_name = message.split(' ', 1)[1]
            client_socket.send(Encrpyt(f'Upload {file_name}'))
            try:
                # Reading file and sending data to server
                with open(file_name, "rb") as fi:
                    data = fi.read(1024)
                    while data:
                        client_socket.send(data)
                        data = fi.read(1024)
                    # File is closed after data is sent
                final_response = client_socket.recv(1024)
                print(f"Server response: {final_response}")

            except IOError:
                print('You entered an invalid filename!\
                        Please enter a valid name')

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


def Encrpyt(public_key, plaintext, key):  # Double encrypt the message being sent
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

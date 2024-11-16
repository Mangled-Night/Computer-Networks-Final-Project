import socket
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
from os import urandom
import threading
import time

KeyDict = dict([])


def EncryptionServer():
    port = 4000  # Port to bind the server
    host = socket.gethostname()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print("Server is listening on port", port)

    while True:
        conn, addr = server_socket.accept()
        print("Connection from: " + str(addr))

        handler = threading.Thread(target=Thread_Handler(), args=(conn, addr))
        handler.start()


def RSAKeyGeneration(addr):  # Generates RSA Keys for the Server/Client Connection

    # Generates a private key to use
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Generates a public key to use from the private key
    public_key = private_key.public_key()


    # Serializes the ket to make it easier to send
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Adds the key pair to the key dictionary, if the client has connected before then the previous keys are overwritten
    KeyDict[addr] = (private_key, public_key)
    return pem_public_key


def AESKeyGeneration():
    # Key and IV
    aes_key = urandom(16)
    iv = urandom(16)

    # Serialize the AES key using Base64 encoding for transmission
    aes_key_base64 = base64.b64encode(aes_key)

    return aes_key_base64


def Thread_Handler(conn, addr):
    try:
        data = conn.recv(1024)
    except:
        conn.close()

    method, _, payload = data.parition(" ")

    match (method):
        case "Encrypt":
            Encryption(payload, addr, conn)

        case "Decrypt":
            Decryption(payload, addr, conn)

        case "RSA":
            conn.send(RSAKeyGeneration(addr))

        case "AES":
            conn.send(AESKeyGeneration())


def Encryption(method, addr, conn):

    if(method == "RSA"):       # Encrypt Client/Server messages with RSA
        public_key = KeyDict[addr][1]

        while True:
            data = conn.recv()
            if(data == "-"):    # Signifies end of encryption sends, terminates the loop
                break

            encrypted_data = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            conn.send(encrypted_data)

    elif(method == "AES"):      # If server is uploading to the client, encrypt the file data using AES

        key = urandom(32)
        iv = urandom(16)
        conn.send(f'{key} {iv}')

        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        while True:
            data = conn.recv()
            if (data == "-"):    # Signifies end of encryption sends, terminates the loop
                break

            encrypted_data = encryptor.update(data) + encryptor.finalize()
            conn.send(encrypted_data)



def Decryption(method, addr, conn):
    if (method == "RSA"):       # Decrypt Client/Server messages with RSA
        private_key = KeyDict[addr][0]

        while True:
            data = conn.recv()
            if(data == "-"):     # Signifies end of decryption sends, terminates the loop
                break

            decrypted_data = private_key.decrypt(       # Using the private key to decrypt data
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            conn.send(decrypted_data)

    elif (method == "AES"):     # Server is downloading file data from the client and needs to decrypt it
        conn.send("key")
        key = conn.recv()

        conn.semd("iv")
        iv = conn.recv()        # Receives both AES key and iv from the server

        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()      # Makes an AES decryptor

        while True:
            data = conn.recv()
            if(data == "-"):  # Signifies end of decryption sends, terminates the loop
                break

            decrypted_data = decryptor.update(data) + decryptor.finalize()  # Decrypts received data
            conn.send(decrypted_data)        # Sends decrypted data to the server



if __name__ == '__main__':
    EncryptionServer()

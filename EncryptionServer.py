import socket
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import threading
import base64
from os import urandom
import logging
import queue

KeyDict = dict([])
def EncryptionServer():
    port = 4000  # Port to bind the server
    host = socket.gethostname()
    Q = queue.Queue()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    server_socket.setblocking(False)
    print("Server is listening on port", port)

    # Input thread for server console, ensures when calling input it does not lock up the main thread
    input_thread = threading.Thread(target=Console, args=((Q,)))
    input_thread.start()

    while True:

        try:
            conn, address = server_socket.accept()
            conn.setblocking(True)
        except BlockingIOError:
            if (not Q.empty()):
                print("Shutting Down the Server")
                break
        else:
            handler = threading.Thread(target=Thread_Handler, args=(conn,))
            handler.start()

def Console(Q):
    command = ""
    while not command.lower().startswith('shutdown'):
        command = input("server/ ")

    Q.put("StopAllConnections")


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
    KeyDict[addr] = [(private_key, public_key), None]
    return pem_public_key


def Thread_Handler(conn):
    conn.settimeout(5)
    log = logging.getLogger("Encrypt")

    try:
        raw_data = conn.recv(1024).decode()
        addr, request = raw_data.split('-')

    except Exception as e:
        tb = e.__traceback__
        lines = []
        while tb is not None:
            lines.append(tb.tb_lineno)
            tb = tb.tb_next

        log.error(f"Internal Server Error. Closing Connection: {e}: lines: {lines}")
        conn.close()
        return
    else:
        pass

    try:
        match (request):
            case "Encrypt":
                Encryption(addr, conn)

            case "Decrypt":
                Decryption(addr, conn)

            case "RSA":
                conn.send(RSAKeyGeneration(addr))

            case "AES":
                SetAESKey(addr, conn)

            case "Remove":
                RemoveKey(addr)
    except Exception as e:
        tb = e.__traceback__
        lines = []
        while tb is not None:
            lines.append(tb.tb_lineno)
            tb = tb.tb_next

        log.error(f"Internal Server Error. Closing Connection: {e}: lines: {lines}")

    conn.close()


def Encryption(addr, conn):
    key = KeyDict[addr][1]  # Retrieve the key

    conn.send("Hello".encode())
    while True:
        data = conn.recv(1024)
        if(data == b''):  # Signifies end of encryption sends, terminates the loop
            break

        # Generate a fresh IV for each block of data
        iv = urandom(16)

        # Set up the cipher with the key and IV
        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Encrypt the data
        encrypted_data = encryptor.update(data)

        # Send the IV and encrypted data together
        conn.send(iv + encrypted_data)



def Decryption(addr, conn):
    key = KeyDict[addr][1]
    conn.send("Hello".encode())
    while True:
        data = conn.recv(2048)
        if(data == b''):  # Signifies end of decryption sends, terminates the loop
            break

        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(data[:16]),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()  # Makes an AES decryptor

        decrypted_data = decryptor.update(data[16:]) + decryptor.finalize()  # fully decrypts data
        conn.send(decrypted_data)  # Sends decrypted data to the server


def SetAESKey(addr, conn):
    conn.send("Hello".encode())  # Confirmation Message
    encrypted_key = conn.recv(2048)  # Receives the encrypted key
    conn.send("Hello".encode())
    decrypted_key = KeyDict[addr][0][0].decrypt(  # Decrypts the AES Key
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    key = base64.b64decode(decrypted_key)
    KeyDict[addr][1] = key  # Turns it back into its original tuple and saves it

def RemoveKey(addr):
    KeyDict.pop(addr)

if __name__ == '__main__':
    EncryptionServer()
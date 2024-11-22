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

        handler = threading.Thread(target=Thread_Handler, args=(conn,))
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
    KeyDict[addr] = [(private_key, public_key), None]
    return pem_public_key


def Thread_Handler(conn):
    conn.settimeout(5)
    try:
        raw_data = conn.recv(1024).decode()
        addr, request = raw_data.split('-')

    except Exception as e:
        print(e)
        conn.close()
        return
    else:
        conn.settimeout(None)

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

    conn.close()
    #print("Connection has been closed\n")


def Encryption(addr, conn):
    key = KeyDict[addr][1]  # Retrieve the key
    sendIV = False

    conn.send("Hello".encode())
    while True:
        data = conn.recv(1024)
        if(data == b"-" or data == b''):  # Signifies end of encryption sends, terminates the loop
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
        if(not sendIV):
            conn.send(iv + encrypted_data)
            sendIV = True
        else:
            conn.send(encrypted_data)



def Decryption(addr, conn):
    key = KeyDict[addr][1]
    setIV= False
    iv = None

    conn.send("Hello".encode())
    while True:
        data = conn.recv(2048)
        if(data == b"-" or data == b''):  # Signifies end of decryption sends, terminates the loop
            break

        if(not setIV):
            iv = data[:16]
            data = data[16:]
            setIV = True

        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()  # Makes an AES decryptor

        # half_decrypt = KeyDict[addr][0][0].decrypt(  # Decrypts the data using the private key
        #     data,
        #     padding.OAEP(
        #         mgf=padding.MGF1(algorithm=hashes.SHA256()),
        #         algorithm=hashes.SHA256(),
        #         label=None
        #     )
        # )

        decrypted_data = decryptor.update(data) + decryptor.finalize()  # fully decrypts data
        #print(decrypted_data)
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
    #print(KeyDict[addr])

def RemoveKey(addr):
    KeyDict.pop(addr)

if __name__ == '__main__':
    EncryptionServer()
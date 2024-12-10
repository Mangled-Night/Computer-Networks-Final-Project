import os
import socket
from os import urandom
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
import base64
import time


def client_program():
    upload = download = connected = False

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
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1048576)

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
                        buffer_size = int(buffer_size) + 16
                        client_socket.send(b'ACK')
                        Download(client_socket, message, key, buffer_size)
                        message = ""
                        continue

                clientData, serverState = plaintext.split('~')
                print(f'{clientData}')
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
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    try:
        buffer_size = CalculateBuffer(os.path.getsize(file_name))
        conn.send(Encrypt(str(buffer_size), key))
        conn.recv(1024)
        conn.send(Encrypt(str(os.path.getsize(file_name)), key))
        conn.recv(1024)
        noACK = 0
        # Reading file and sending data to server
        with open(file_name, "rb") as fi:
            data = fi.read(buffer_size)
            while data:
                start = time.time()
                conn.sendall(Encrypt(data, key))

                if (len(data) >= buffer_size):
                    Ack = conn.recv(1024)
                    if(len(Ack) > 7):
                        Decrypt(Ack, key)
                    if (Ack.decode().startswith("ACK")):
                        conn.send(b'ACK')
                        data = fi.read(buffer_size)
                    else:
                        noACK += 1
                        if noACK == 3:
                            conn.send(b"+++++")
                            print("De-synchronized Connection With Server")
                            return
                else:
                    data = fi.read(buffer_size)
        # File is closed after data is sent
        conn.send(b"-----")




    except FileNotFoundError:
        conn.send(Encrypt("+", key))
        print('You entered an invalid filename!\
        Please enter a valid name')

    except Exception as e:
        print(e)
        tb = e.__traceback__
        lines = []
        while tb is not None:
            lines.append(tb.tb_lineno)
            tb = tb.tb_next
        print(lines)
        return

def Download(conn, message, key, buffer_size):
    files_name = message.split(' ', 1)[1]
    secondary_buffer = conn.recv(1024)
    secondary_buffer = Decrypt(secondary_buffer, key)
    secondary_buffer_size = CalculateSecondaryBuffer(int(secondary_buffer), buffer_size)
    conn.send(b'ACK')
    try:
        # Reading file and sending data to server
        with open(files_name, "xb") as fil:
            print("Starting Download")
            buffer = b''
            write_buffer = bytearray()

            while True:
                encrypted_bytes = conn.recv(buffer_size)

                if encrypted_bytes[-4:] in [b'----', b'++++', b''] and len(buffer) > 0:  # Stop if no more data
                    if encrypted_bytes[-4:] in [b'++++', b'']:
                        raise EOFError

                    conn.send(Encrypt("ACK", key))
                    buffer += encrypted_bytes[:-4]

                    if(len(buffer)):
                        write_buffer += Decrypt(buffer, key, False)

                    fil.write(write_buffer)
                    return
                else:
                    buffer += encrypted_bytes
                    while len(buffer) >= buffer_size:
                        file_data = buffer[:buffer_size]
                        buffer = buffer[buffer_size:]

                        write_buffer += Decrypt(file_data, key, False)
                        if(len(write_buffer) >= secondary_buffer_size):
                            fil.write(write_buffer)
                            write_buffer.clear()

                        conn.send(Encrypt("ACK", key))

    except FileExistsError:
        print('This File Already Exists!')
        conn.send(Encrypt('+', key))

    except EOFError:
        os.remove(files_name)
        print("Server Request: Cancelling Download")

    except Exception as e:
        print(e)
        os.remove(files_name)
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
    Max = 1024 * 1024
    if(file_size == 0):
        return 1024
    return max(Min, min(file_size // 10, Max))

def CalculateSecondaryBuffer(file_size, main_buffer_size):
    Min = main_buffer_size
    Max = 64 * 1024 * 1024

    if file_size == 0:
        return Min

    # Calculate 1/4 of the file size but make sure it's within the min and max limits
    secondary_buffer_size = file_size // 4
    return max(Min, min(secondary_buffer_size, Max))

if __name__ == '__main__':
    client_program()

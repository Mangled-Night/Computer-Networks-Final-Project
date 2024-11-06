import socket

port = 4000  # Port to bind the server
host = socket.gethostname()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(10)
print("Server is listening on port", port)

conn, addr = server_socket.accept()
print("Connection from: " + str(addr))

while True:
    try:
        data = conn.recv(1024).decode()  # receive response
    except:
        print("Connection Terminated")
        break

    print(f'Reccived Data: {data}')
    #conn.send(data.encode())

conn.close()
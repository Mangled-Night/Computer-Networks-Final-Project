import socket
import tkinter as tk

class GUI:
    def __init__(self):
        self.root = tk.Tk()

        self.root.geometry("500x500")
        self.root.title("CNT_Project")

        self.label = tk.Label(self.root, text="Your mother", font=('Arial', 18))
        self.label.pack(padx = 20, pady=20)

        self.buttonframe = tk.Frame(self.root)
        self.buttonframe.columnconfigure(0, weight=1)
        self.buttonframe.columnconfigure(1, weight=1)
        self.buttonframe.columnconfigure(2, weight=1)

        self.btn1 = tk.Button(self.buttonframe, text="Connect", font=('Arial', 18), command=client_program)
        self.btn1.grid(row=0, column=0, sticky=tk.W+tk.E)

        self.btn2 = tk.Button(self.buttonframe, text="Upload", font=('Arial', 18))
        self.btn2.grid(row=0, column=1, sticky=tk.W+tk.E)

        self.btn3 = tk.Button(self.buttonframe, text="Download", font=('Arial', 18))
        self.btn3.grid(row=0, column=2, sticky=tk.W+tk.E)

        self.btn4 = tk.Button(self.buttonframe, text="Delete", font=('Arial', 18))
        self.btn4.grid(row=1, column=0, sticky=tk.W+tk.E)

        self.btn5 = tk.Button(self.buttonframe, text="Dir", font=('Arial', 18))
        self.btn5.grid(row=1, column=1, sticky=tk.W+tk.E)

        self.btn6 = tk.Button(self.buttonframe, text="Subfolder", font=('Arial', 18))
        self.btn6.grid(row=1, column=2, sticky=tk.W+tk.E)

        self.buttonframe.pack(fill='x')

        self.root.mainloop()

def connect_server(host, port):
    print("Establishing a connection to the server...")
    client_socket = socket.socket()
    try:
        client_socket.connect((host, port))
        print(f"Connection established: {host} : {port}")
        return client_socket
    except ConnectionError:
        print("Unable to establish a connection to the server.")
        return None


def receive_response(client_socket):
    # receive response from server
    try:
        data = client_socket.recv(1024).decode()
        return data
    except ConnectionError:
        print("Unable to receive data.")
        return None

def on_select(event):
    selected_item = combo_box.get()
    label.config(text="Selected Item: " + selected_item)

def send_message(client_socket, message):
    try:
        client_socket.send(message.encode())
    except ConnectionError:
        print("Unable to send data.")

def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = connect_server(host, port)  # connect to the server
    if not client_socket:
        return #exits if unable to connect

    print("Type 'disconnet' to exit.")
    message = input("Enter Command: ")

    while message.lower().strip() != 'disconnet':
        client_socket.send(message.encode())  # send message

        response = receive_response(client_socket)
        if response:
            print(f"Server response: {response}")
        message = input("Enter Command:")

    # exit
    print("Disconnecting...")
    send_message(client_socket, "Disconnected")
    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()

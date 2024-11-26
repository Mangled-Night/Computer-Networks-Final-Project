import select
import socket
import threading
from ClientHandler import ClientHandle
import ast
import queue
import logging
import pandas as pd
from tabulate import tabulate



def server_program():
    host = socket.gethostname()
    port = 5000  # Port to bind the server
    Q = queue.Queue()
    usersQ = queue.Queue()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(4)
    server_socket.setblocking(False)
    print("Server is listening on port", port)

    # Input thread for server console, ensures when calling input it does not lock up the main thread
    input_thread = threading.Thread(target=Console, args=(Q, usersQ,))
    input_thread.start()

    logging.basicConfig(
        filename="my_log_file.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    try:
        open("Users.txt", 'x')
    except FileExistsError:
        pass

    with open("Users.txt", 'r') as file:
        data = file.read()

        if data.strip():    # If the file is not empty, grab all users from the file
            ClientHandle.SetUserDict(ast.literal_eval(data))

        else:   # If empty, set as an empty dictionary
            ClientHandle.SetUserDict(dict([]))

    ClientHandle.SetRSA((host, 4000))


    while True:
        # Accept new connection
        try:
            conn, address = server_socket.accept()
            conn.setblocking(True)
        except BlockingIOError:
            if(not Q.empty()):
                print("Shutting Down the Server")
                ClientHandle.WriteUserData()
                break
        else:
            # Start a new thread to handle each client
            client_thread = threading.Thread(target=ClientHandle(conn, address).handle_client)
            client_thread.start()
            usersQ.put(conn)



# Function for input thread to use
def Console(Q, uQ):
    command = ""
    users = []
    pd.set_option('display.max_rows', None)  # Show all rows
    pd.set_option('display.max_columns', None)  # Show all columns

    while not command.lower().startswith('shutdown'):
        print("\tGetting all users...")

        # Remove all close connections
        users = [u for u in users if u.fileno() != -1]

        if(len(users)):
            rAlive, wAlive, _ = select.select(users, users, [])
            alive = list(set(rAlive + wAlive))
            users = alive

        # Add new users to the users list
        while not uQ.empty(): # Adds all connected users into this list
            users.append(uQ.get())

        print("\tAll users added")
        command = input("server/ ")
        server_command(command, users)

    Shutdown(Q, users, uQ, command)



def server_command(request, users):
    command, _, target = request.partition(" ")
    target = target.strip()

    match command.lower():
        case "users":
            if(not len(users)):
                print("\tNo Connected Users")
                return

            stop = None
            if(target == ""):
                stop = 9999
            else:
                try:
                    stop = int(target)
                    if (stop < 1):
                        print("\tStop parameter must be greater than 1")
                        return

                except ValueError:
                    print("\tStop parameter must be an integer")
                    return

            print(f'\t[ID]- Address: xxx-xxx-xxx-xxx  Port: xxxx')
            i = 0
            for conn in users:
                addr, port = conn.getpeername()
                print(f'\t[{i}]- Address: {addr}  Port: {port}')
                i += 1

                if(i > stop):
                    break

        case "refresh":
            return

        case "kill":
            KillConnection(users, target)

        case "help":
            Help()

        case "stats":
            Stats(target)

        case _:
            print("Enter a server command. Type help for a list of commands")


def KillConnection(users, target):

    if(target == '-a'):
        for conn in users:
            conn.close()

        users.clear()
        print("\tAll User Connections Has Been Terminated")
        return

    try:
        target = int(target)

    except ValueError:
        print("Pass the user-ID")

    if(int(target) > len(users)-1):
        print("\tNo valid target")
        return

    users[target].close()
    users.pop(target)
    print("\tUser Connection Has been Terminated")

def Shutdown(q, u, uQ, command):
    q.put("StopAllConnections")

    # Grabs all users before shutting now
    if (len(u)):
        rAlive, wAlive, _ = select.select(u, u, [])
        alive = list(set(rAlive + wAlive))
        u = alive

        # Add new users to the users list
    while not uQ.empty():  # Adds all connected users into this list
        u.append(uQ.get())

    command, _, flag = command.partition(" ")
    if(flag == "-f"):
        KillConnection(u, '-a')

def Stats(flags):
    s = pd.read_csv('operation_stats.csv')
    grouped_stats = None


    if(s.empty):
        print("\n\tNo statistics have been recorded yet")
        return

    match(flags):
        case "-s":
            grouped_stats = s.groupby("operation_type").agg(
                total_operations=("operation_type", "size"),
                total_MB_transfered=('file_size_MB', "sum"),
                total_time_s=('transfer_time_s', "sum")
            )

        case '-m':
            grouped_stats = s.groupby("operation_type").agg(
                average_size_MB=('file_size_MB', "mean"),
                average_time_s=('transfer_time_s', "mean"),
                average_rate_MBps=('data_rate_MBps', "mean")
            )

        case '-r':
            grouped_stats = s.groupby("operation_type").agg(
                min_MB=("file_size_MB", "min"),
                max_MB=("file_size_MB", "max"),
                min_time_s=('transfer_time_s', "min"),
                max_time_s=('transfer_time_s', "max"),
                min_rate_MBps=("data_rate_MBps", "min"),
                max_rate_MBps=('data_rate_MBps', "max")
            )

        case '':
            grouped_stats1 = s.groupby("operation_type").agg(
                total_operations=("operation_type", "size"),
                total_MB_transfered=('file_size_MB', "sum"),
                total_time_s=('transfer_time_s', "sum")
            )

            grouped_stats2 = s.groupby("operation_type").agg(
                average_size_MB=('file_size_MB', "mean"),
                average_time_s=('transfer_time_s', "mean"),
                average_rate_MBps=('data_rate_MBps', "mean")
            )

            grouped_stats3 = s.groupby("operation_type").agg(
                min_MB=("file_size_MB", "min"),
                max_MB=("file_size_MB", "max"),
                min_time_s=('transfer_time_s', "min"),
                max_time_s=('transfer_time_s', "max"),
                min_rate_MBps=("data_rate_MBps", "min"),
                max_rate_MBps=('data_rate_MBps', "max")
            )
            print(tabulate(grouped_stats1, headers="keys", tablefmt="grid", showindex=True))
            print(tabulate(grouped_stats2, headers="keys", tablefmt="grid", showindex=True))
            print(tabulate(grouped_stats3, headers="keys", tablefmt="grid", showindex=True))
            return


        case _:
            print("\n\tPlease Enter the Correct Flag (s, m, r)")
            return

    print(tabulate(grouped_stats, headers="keys", tablefmt="grid", showindex=True))


def Help():
    print("refresh: Refreshes The List Of Connected Users"
          "\nusers: Display All Connected User's Port and IP"
          "\nkill: [-a | UserID]: Kills a User's Connection"
          "\n\t[-a] All Connected Users Are Terminated"
          "\n\t[UserID] Terminates the Specified User"
          "\nshutdown [-f]: Shuts Down The Server. Waits for all Connected Users To Close Their Connections"
          "\n\t[-f]: Forcefully Shuts Down The Server. All Connected Users Will Be Disconnected"
          "\nstats [-s | -m | -r]: Displays Statistics Collected From The Server"
          "\n\t[-s] Displays The Totals Only"
          "\n\t[-m] Displays The Averages Only"
          "\n\t[-r] Displays the Min/Max Only")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    server_program()


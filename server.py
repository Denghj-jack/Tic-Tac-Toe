import sys
import os
import json
import socket
import selectors
import re
import bcrypt
from game_in import GameIn
import threading

#this function is used to read the config file
def read_config_file(file_path: str):
    expand_path = os.path.expanduser(file_path)
    try:
        with open(expand_path, 'r') as json_file:
            config_info = json.load(json_file)
            return config_info
    except FileNotFoundError:
        print("Error: <server config path> doesn’t exist.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: <server config path> is not in a valid JSON format.")
        sys.exit(1)

#this function is used to analysis the key in the config file
def analysis_key(config_info: dict):
    port = config_info.get("port")
    database_path = config_info.get("userDatabase")
    if port is None and database_path is None:
        print("Error: <server config path> missing key(s): port, userDatabase")
        sys.exit(1)
    elif port is None:
        print("Error: <server config path> missing key(s): port")
        sys.exit(1)
    return port, database_path


#this function is used to read the database file(which is a key inside the config file)
def read_database_file(database_path: str):
    expand_database_path = os.path.expanduser(database_path)
    required_keys = ["username" , "password"]
    try:
        with open(expand_database_path , 'r') as database_file:
            user_database = json.load(database_file)
            if not isinstance(user_database , list):
                print("”Error: <user database path> is not a JSON array.")
                exit(1)
            else:
                for element in user_database:
                    if not all(key in element for key in required_keys):
                        print("Error: <user database path> contains invalid user record formats.")
                        sys.exit(1)
                    else:
                        return user_database
    except FileNotFoundError:
        print("Error: <user database path> doesn’t exist.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: <user database path> is not in a valid JSON format.")
        sys.exit(1)

def login_handle(command_ls , client_socket , user_database , identified_users):
    try:
        username = command_ls[0]
        password = command_ls[1]
        if username not in user_database:
            login_message = "LOGIN:ACKSTATUS:1"
            client_socket.sendall(login_message.encode())
        else:
            encrypted_password = user_database[username]
            if bcrypt.checkpw(password.encode(), encrypted_password):
                identified_users[username] = client_socket
                login_message = "LOGIN:ACKSTATUS:0"
                client_socket.sendall(login_message.encode())
            else:
                login_message = "LOGIN:ACKSTATUS:2"
                client_socket.sendall(login_message.encode())
    except IndexError:
        login_message = "LOGIN:ACKSTATUS:3"
        client_socket.sendall(login_message.encode())


def register_handle(command_ls,client_socket , user_database , user_database_path):
    try:
        username = command_ls[0]
        password = command_ls[1]
        if username in user_database:
            register_message = "REGISTER:ACKSTATUS:1"
            client_socket.sendall(register_message.encode())
        else:
            try:
                with open(user_database_path, 'r') as jsonfile:
                    user_database = json.load(jsonfile)
            except FileNotFoundError:
                user_database = {}
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) #encrypt the password
            hashed_password_str = hashed_password.decode('utf-8')
            user_database.append({
                "username": username,
                "password": hashed_password_str
            })
            #user_database[username] = hashed_password_str
            with open(user_database_path, 'w') as jsonfile:
                json.dump(user_database, jsonfile)
            register_message = "REGISTER:ACKSTATUS:0"
            client_socket.sendall(register_message.encode())
    except IndexError:
        register_message = "REGISTER:ACKSTATUS:2"
        client_socket.sendall(register_message.encode())


def roomlist_handle(command_ls , client_socket , available_rooms):
    try:
        character_option = command_ls[0].upper()
        if character_option != "Player" or character_option != "Viewer":
            roomlist_message= "ROOMLIST:ACKSTATUS:1"
            client_socket.sendall(roomlist_message.encode())
        else:
            roomlist_str = ','.join(available_rooms)
            roomlist_message = f"ROOMLIST:ACKSTATUS:0:{roomlist_str}"
            client_socket.sendall(roomlist_message.encode())
    except IndexError:
        message = "ROOMLIST:ACKSTATUS:1"
        client_socket.sendall(message.encode())


def create_handle(client_socket , command_ls ,server_data):
    pattern = r'^[a-zA-Z0-9\s\-_]{1,20}$'
    try:
        room_name = command_ls[0]
        if not re.match(pattern, room_name):
            message = "CREATE:ACKSTATUS:1"
            client_socket.sendall(message.encode())
        elif room_name in server_data['rooms']:
            message = "CREATE:ACKSTATUS:2"
            client_socket.sendall(message.encode())
        elif len(server_data['rooms']) >= 256:
            message = "CREATE:ACKSTATUS:3"
            client_socket.sendall(message.encode())
        else:
            server_data['rooms'].append(room_name)
            server_data['available_rooms'].append(room_name)
            server_data['room_info'][room_name] = {
                'players': [client_socket],  # use to store player socket
                'player_names': [],
                'viewers': [],
                'current_turn': 0,
                'game_over': False,
                'game_state_string': ""
            }

            message = "CREATE:ACKSTATUS:0"
            client_socket.sendall(message.encode())
    except IndexError:
        message = "CREATE:ACKSTATUS:4"
        client_socket.sendall(message.encode())



def join_handle(command_ls , client_socket , server_data):
    try:
        room_name = command_ls[0]
        character = command_ls[1]
        if character.lower() != "player" or character.lower() != "viewer":
            join_message = "JOIN:ACKSTATUS:3"
            client_socket.sendall(join_message.encode())
        elif room_name not in server_data['rooms']:
            join_message = "JOIN:ACKSTATUS:1"
            client_socket.sendall(join_message.encode())
        elif room_name not in server_data['available_rooms'] and character.lower() == "player":
            join_message = "JOIN:ACKSTATUS:2"
            client_socket.sendall(join_message.encode())
        elif character.lower() == "viewer":
            server_data['room_info'][room_name]['viewers'].append(client_socket)
            join_message = "JOIN:ACKSTATUS:0"
            client_socket.sendall(join_message.encode())
        elif room_name in server_data['available_rooms'] and character.lower() == "player":
            server_data['room_info'][room_name]['players'].append(client_socket)
            server_data['room_info'][room_name]['player_names'].append(server_data['identified_users'][client_socket])
            server_data['available_rooms'].remove(room_name)
            join_message = "JOIN:ACKSTATUS:0"
            client_socket.sendall(join_message.encode())
            if len(server_data['room_info'][room_name]['players']) == 2:
                game_handle(room_name , server_data)
    except IndexError:
        join_message = "JOIN:ACKSTATUS:3"
        client_socket.sendall(join_message.encode())

#this function is used to handle the game session
def game_handle(room_name , server_data):
    room_info = server_data['room_info'][room_name]
    player_sockets = room_info['players']
    viewer_sockets = room_info['viewers']
    identified_users = server_data['identified_users']

    game_instance = GameIn(player_sockets[0], player_sockets[1], viewer_sockets, identified_users, room_info)
    threading.Thread(target=game_instance.running_game).start()
    game_instance.running_game()


# this function is used to distinguish the command
def distinguish_command(command_ls , client_socket , user_database , user_database_path, server_data):
    if command_ls[0] == "LOGIN":
       login_handle(command_ls[1:] , client_socket , user_database , server_data['identified_users'])
    elif command_ls[0] == "REGISTER":
        register_handle(command_ls[1:] ,client_socket , user_database , user_database_path)
    else:
        if client_socket not in server_data['identified_users'].values():
            message = "BADAUTH"
            client_socket.sendall(message.encode())
        elif command_ls[0] == "ROOMLIST":
            roomlist_handle(command_ls[1:], client_socket , server_data['available_rooms'])
        elif command_ls[0] == "CREATE":
            create_handle(client_socket , command_ls[1:], server_data)
        elif command_ls[0] == "JOIN":
            join_handle(command_ls[1:] , client_socket , server_data)


def accept_connection(sock , selector):
    client_socket , address = sock.accept()
    client_socket.setblocking(False)
    selector.register(client_socket , selectors.EVENT_READ , data = client_socket) #problem? data = True or data = address

def read_from_client(selector, client_socket, user_database, user_database_path, roomdata):
    try:
        data = client_socket.recv(8192)
        if data:
            command = data.decode().strip() #consider whether to use strip
            command_ls = command.split(":")
            distinguish_command(command_ls , client_socket , user_database,user_database_path , roomdata)
        else:
            selector.unregister(client_socket)
            client_socket.close()
    except ConnectionResetError:
        selector.unregister(client_socket)
        client_socket.close()


def main(args: list[str]) -> None:
    length_argv = len(args)

    room_data = {
        'rooms': [],  # List of room names
        'available_rooms': [],  # List of available room names
        'identified_users': {},  # Dictionary of identified users( pair: username: socket)
        'room_info': {}  # Dictionary of room information
    }

    if length_argv != 1:
        print("Error: Expecting 1 argument: <server config path>")
        sys.exit(1)
    else:
        file_path = args[0]
        config_info = read_config_file(file_path)
        port , database_path = analysis_key(config_info)
        user_database = read_database_file(database_path)
        selector = selectors.DefaultSelector()  # create a selector object

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_socket.bind(('', port))
        server_socket.listen()
        server_socket.setblocking(False)

        selector.register(server_socket, selectors.EVENT_READ, data = None)
        try:
            while True:
                events = selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        accept_connection(key.fileobj , selector)
                    else:
                        read_from_client(selector , key.fileobj , user_database, database_path, room_data)
        except KeyboardInterrupt:
            print("server is closed")
        finally:
            selector.close()


if __name__ == "__main__":
    main(sys.argv[1:])

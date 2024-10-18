import sys
import socket
import game

MAX_SIZE = 8192

#this function is used to check the character option input
def check_character_option_input(character_option: str):
    if character_option.lower() == "player":
        return "PLAYER"
    elif character_option.lower() == "viewer":
        return "VIEWER"
    else:
        print("Unknown input")


def login(client_socket: socket.socket):
    username = input("Enter username: ")
    password = input("Enter password: ")
    message = f"LOGIN:{username}:{password}"
    client_socket.sendall(message.encode())
    login_response = client_socket.recv(MAX_SIZE).decode()

    if login_response == "LOGIN:ACKSTATUS:0":
        print(f"Welcome {username}")
        return username
    elif login_response == "LOGIN:ACKSTATUS:1":
        print(f" Error: User {username} not found" , file = sys.stderr)
    elif login_response == "LOGIN:ACKSTATUS:2":
        print(f"Error: Wrong password for user {username}", file = sys.stderr)
    elif login_response == "LOGIN:ACKSTATUS:3": #for robustness
        pass



#this function is used to register a new user
def register(client_socket: socket.socket):
    username = input("Enter username: ")
    password = input("Enter password: ")
    message = f"REGISTER:{username}:{password}"
    client_socket.sendall(message.encode())
    register_response = client_socket.recv(MAX_SIZE).decode()

    if register_response == "REGISTER:ACKSTATUS:0":
        print(f"Successfully created user account {username}")
        return username
    elif register_response == "REGISTER:ACKSTATUS:1":
        print(f"Error: User {username} already exists" , file = sys.stderr)
    elif register_response == "REGISTER:ACKSTATUS:2": #for robustness
        pass


#this function is used to create a room
def roomlist(client_socket: socket.socket):
    character_option = input("Do you want to have a room list as player or viewer? (Player/Viewer)") #case-insensitive input
    final_character_option = check_character_option_input(character_option)
    while final_character_option is None:
        character_option = input("Do you want to have a room list as player or viewer? (Player/Viewer)")
        final_character_option = check_character_option_input(character_option)
    message = f"ROOMLIST:{final_character_option}"
    client_socket.sendall(message.encode())
    roomlist_response = client_socket.recv(MAX_SIZE).decode()
    if roomlist_response == "ROOMLIST:ACKSTATUS:1":
        print("Error: Please input a valid mode", file = sys.stderr)
    elif roomlist_response.startswith("ROOMLIST:ACKSTATUS:0"):
        room_to_join_list = roomlist_response.split(":")[3:]
        print(f"Room available to join as {final_character_option}: {room_to_join_list}")
    elif roomlist_response == "BADAUTH":
        badauth_message_output()


#this function is used to create a room
def create(client_socket: socket.socket):
    room_name = input("Enter room name you want to create: ")
    message = f"CREATE:{room_name}"
    client_socket.sendall(message.encode())
    create_response = client_socket.recv(MAX_SIZE).decode()
    if create_response == "CREATE:ACKSTATUS:0":
        print(f"Successfully created room {room_name}")
    elif create_response == "CREATE:ACKSTATUS:1":
        print(f"Error: Room {room_name} is invalid" , file = sys.stderr)
    elif create_response == "CREATE:ACKSTATUS:2":
        print(f"Error: Room {room_name} already exists" , file = sys.stderr)
    elif create_response == "CREATE:ACKSTATUS:3":
        print(f"Error: Server already contains a maximum of 256 rooms" , file = sys.stderr)
    elif create_response == "CREATE:ACKSTATUS:4": #for robustness
        pass
    elif create_response == "BADAUTH":
        badauth_message_output()



#this function is used to join a room
def join(client_socket: socket.socket):
    room_name = input("Enter room name you want to join: ")
    character = input("You wish to join the room as: (Player/Viewer)")
    final_character = check_character_option_input(character)
    while final_character is None:
        character = input("You wish to join the room as: (Player/Viewer)")
        final_character = check_character_option_input(character)
    message = f"JOIN:{room_name}:{final_character}"
    client_socket.sendall(message.encode())
    join_response = client_socket.recv(MAX_SIZE).decode()
    if join_response == "JOIN:ACKSTATUS:0":
        print(f"Successfully joined room {room_name} as a {final_character}")
        return final_character
    elif join_response == "JOIN:ACKSTATUS:1":
        print(f"Error: No room named {room_name}" , file = sys.stderr)
        return None
    elif join_response == "JOIN:ACKSTATUS:2":
        print(f"Error: The room {room_name} already has 2 players" , file = sys.stderr)
        return None
    elif join_response == "JOIN:ACKSTATUS:3":
        pass #for robustness
    elif join_response == "BADAUTH":
        badauth_message_output()


#this function is used to handle wrong format of the message
def badauth_message_output():
    print("Error: You must be logged in to perform this action", file = sys.stderr)


def handle_game_in_message(client_socket: socket.socket , mode: str , user_name: str):
    game_end_flag = False
    board = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
    while True:
        game_in_response = client_socket.recv(MAX_SIZE).decode()
        if game_in_response is None:
            break
        response_lines = game_in_response.strip().split('\n')
        players_list = [] #to store the players'names in the game
        for line in response_lines:
            response_info = line.strip().split(':')
            game_command = response_info[0]
            if game_command == "BEGIN":
                players_list = response_info[1:]
                player_turn = check_player_turn(game_command , players_list)
                print(f"match between {players_list[0]} and {players_list[1]} will commence, it is currently {player_turn}'s turn.")
                if player_turn == user_name:
                    print("It is your turn. Please make a move")
                else:
                    print("It is not your turn. Please wait for the other player to make a move")
            #inform the viewer that the game is in progress,with the current player's turn
            elif game_command == "INPROGRESS":
                players_list = response_info[1:]
                print(f"match between {players_list[0]} and {players_list[1]} is in progress, it is currently {players_list[0]}'s turn.")
            elif game_command == "BOARDSTATUS":
                board_statue_string = response_info[1]
                print(board_statue_string)
                current_player = check_player_turn(board_statue_string, players_list)
                if mode == "PLAYER":
                    if current_player == user_name:
                        print(f"It is {current_player}’s turn")
                        while True:
                            move_input = input("Enter your move as 'x y' coordinates (0-2) or 'FORFEIT' to forfeit: ")
                            if move_input.strip().upper() == "FORFEIT":
                                client_socket.sendall("FORFEIT".encode())
                                game_over = True
                                break #need to modify
                            else:
                                try:
                                    x_str, y_str = move_input.strip().split()
                                    x, y = int(x_str), int(y_str)
                                    if not (0 <= x <= 2 and 0 <= y <= 2):
                                        print("Error: please enter a valid move (0-2).")
                                        continue
                                    index = y * 3 + x
                                    if board[index] != '0':
                                        print("Error: this cell is already occupied.")
                                        continue
                                    else:
                                        client_socket.sendall(f"PLACE:{x}:{y}".encode())
                                        break  # Valid move sent
                                except ValueError:
                                    print("Error: Invalid input. Please enter 'x y' or 'FORFEIT'.")
                                    continue
                    else:
                        #for the player who has just made a move
                        print(f"It is {current_player}’s turn")
                elif mode == "VIEWER":
                    print(f" it is the {current_player}’s turn")
            elif game_command == "GAMEEND":
                game_end_flag = True
                if len(response_info) == 4:
                    winner_username = response_info[3]
                    if response_info[2] == 0:
                        if user_name == winner_username and mode == "PLAYER":
                            print("Congratulations, you won!")
                        elif user_name != winner_username and mode == "PLAYER":
                            print("”Sorry you lost. Good luck next time.")
                        elif mode == "VIEWER":
                            print(f"{winner_username} has won this game")
                    elif response_info[2] == 2:
                        print(f"{winner_username} won due to the opposing player forfeiting")
                elif len(response_info) == 3 and response_info[2] == 1:
                    print("Game ended in a draw")
            elif game_command == "NOROOM":
                print("Error: You are not in a room", file = sys.stderr)
                break







def check_player_turn(board , players_list):
    X_count  = 0
    O_count = 0
    for row in board:
        for element in row:
            if element == 'X':
                X_count += 1
            elif element == 'O':
                O_count += 1
    if X_count >= O_count:
        return players_list[0]
    else:
        return players_list[1]


def main(args: list[str]) -> None:
    if len(args) != 2:
        print("Error: Expecting 2 arguments: <server address> <port>")
        sys.exit(1)
    server_address = args[0]
    port = args[1] #port is a string

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        client_socket.connect((server_address, int(port)))

    except ConnectionRefusedError:
        print("”Error: cannot connect to server at <server address> and <port>.")
        sys.exit(1)
    try:
        user_name = None
        mode = None
        while True:
            try:
                user_command = input("Enter command: ")
                if user_command == "LOGIN":
                    user_name = login(client_socket)
                elif user_command == "REGISTER":
                    user_name = register(client_socket)
                elif user_command == "ROOMLIST":
                    roomlist(client_socket)
                elif user_command == "CREATE":
                    create(client_socket)
                elif user_command == "JOIN":
                    mode = join(client_socket)
                    if mode is not None:
                        handle_game_in_message(client_socket , mode , user_name) #need to modify
                        break
                elif user_command == "QUIT":
                    break
                else:
                    print("Error: Unknown command")
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except ConnectionResetError:
                print("Error: Connection to server lost")
                break
    except KeyboardInterrupt:
        sys.exit(0)



if __name__ == "__main__":
    main(sys.argv[1:])

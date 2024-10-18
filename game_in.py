import selectors
import tictactoe
import socket
import game

MAXIMUM_SIZE = 8192

class GameIn:
    def __init__(self , player1_socket , player2_socket , viewers_sockets , identified_users, room_data):
        self.selector = selectors.DefaultSelector()
        self.player1_socket = player1_socket
        self.player2_socket = player2_socket
        self.identified_users = identified_users #dictionary to store the identified users(socket : username)
        self.viewers_sockets = viewers_sockets #list of sockets of viewers
        self.room_data = room_data #dictionary to store the room data
        self.player_usernames = [
            self.identified_users[self.player1_socket],
            self.identified_users[self.player2_socket]
        ]
        self.player_use_symbols = {self.player_usernames[0] : "X" , self.player_usernames[1] : "O"} #dictionary to store the symbol of each player
        self.players_socket_ls = [player1_socket , player2_socket] #list of sockets of players
        self.current_turn_player = 0 #current turn player
        self.board = game.create_board() #create the board(a 2D list)
        self.game_win_flag = False #flag to check if the game is won
        self.game_draw_flag = False #flag to check if the game is drawn
        self.game_end_flag = False #flag to check if the game is ended
        self.someone_forfeit_flag = False #flag to check if someone forfeited

    def running_game(self):
        self.send_begin_game_message()
        while not self.game_end_flag:
            if not self.handle_player_move(self.players_socket_ls[self.current_turn_player]):
                # Player disconnected or forfeited
                break
            else:
                self.switch_player()
                self.board_status_message()
        self.game_end_message(winner_username=self.player_usernames[1 - self.current_turn_player])#need to modify
        self.room_remove()


    # 0 represents player 1 and 1 represents player 2
    def switch_player(self):
        self.current_turn_player = 1 - self.current_turn_player

    def game_end_message(self , winner_username):
        final_board = self.get_current_board_in_string()
        if self.game_win_flag:
            message = f"GAMEEND:{final_board}:0:{winner_username}"
            self.broadcast_message(message)
        elif self.game_draw_flag:
            message = f"GAMEEND:{final_board}:1"
            self.broadcast_message(message)
        elif self.someone_forfeit_flag:
            message = f"GAMEEND:{final_board}:2:{winner_username}"
            self.broadcast_message(message)


    # a function to handle the player move or forfeit
    def handle_player_move(self, player_socket) -> bool:
        try:
            data = player_socket.recv(MAXIMUM_SIZE).decode().strip()
            if not data:
                # Player disconnected
                self.handle_forfeit(player_socket)
                return False
            if data.startswith("PLACE:"):
                x = int(data.split(":")[1])
                y = int(data.split(":")[2])
                self.handle_place(player_socket, x, y)
                return True
            elif data.startswith("FORFEIT"):
                self.handle_forfeit(player_socket)
                return False
        except ConnectionResetError:
            self.handle_forfeit(player_socket)
            return False


    def handle_place(self, player_socket, x, y):
        symbol = self.player_use_symbols[player_socket]
        self.board[y][x] = symbol


    def handle_forfeit(self, player_socket):
        self.game_end_flag = True
        self.someone_forfeit_flag = True
        #need to modify

    #this function is used to send messages to specific client
    def send_message(self , message , sock):
        sock.sendall(message.encode())

    def send_begin_game_message(self):
        message = f"BEGIN:{self.player_usernames[0]}:{self.player_usernames[1]}"
        self.broadcast_message(message)


    #this function is used to send messages to all the viewers and players
    def broadcast_message(self , message):
        for viewer in self.viewers_sockets:
            self.send_message(message , viewer)
        for player in self.players_socket_ls:
            self.send_message(message , player)

    #this function is used to send the message to the viewers in the room
    #check if It's necessary to send the message to all viewers
    def in_progress_game_message(self):
        message = f"INPROGRESS:{self.player_usernames[self.current_turn_player]}:{self.player_usernames[1 - self.current_turn_player]}"
        for viewer in self.viewers_sockets:
            self.send_message(message , viewer)

    #this function is used to get the current board(2D list)
    def get_current_board(self):
        return self.board

    #this function is used to get the current board in string
    def get_current_board_in_string(self):
        board = self.get_current_board()
        NOUGHT = 'O'
        CROSS = 'X'
        EMPTY = ' '
        board_in_string = ""
        for row in board:
            for element in row:
                if element == EMPTY:
                    board_in_string += "0"
                elif element == NOUGHT:
                    board_in_string += "2"
                elif element == CROSS:
                    board_in_string += "1"
        return board_in_string

    #this function is used to send the board status message
    def board_status_message(self):
        board = self.get_current_board_in_string()
        message = f"BOARDSTATUS:{board}"
        self.broadcast_message(message)

    def room_remove(self):
        room_name = self.room_data['room_name']
        del self.room_data[room_name]
















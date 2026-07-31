Network Tic-Tac-Toe

A command-line multiplayer Tic-Tac-Toe prototype built with Python TCP sockets. The project implements account registration, password hashing, authentication, room creation, player/viewer roles, and a message-based game protocol between a central server and multiple clients.

Project status: educational prototype. Authentication and room-management foundations are present, but the in-room gameplay path contains unfinished logic and known implementation issues. Review the Known issues section before running or extending the project.

Features

TCP client/server architecture

Non-blocking server socket management with selectors

User registration and login

Password hashing with bcrypt

JSON-backed user database

Room creation and room listing

Join as a player or viewer

Two-player board representation

Move, board-status, forfeit, draw, and win message types

Standalone game helper functions for board creation and win checking

Requirements

Python 3.10 or newer

bcrypt

Install the dependency:

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install bcrypt

Configuration

The included server_config.json uses the following structure:

{
  "port": 12345,
  "userDatabase": "user_database.json"
}

Change the port or database path as required.

For a clean local test, replace the contents of user_database.json with:

[]

Do not commit real usernames, passwords, or production credential records.

Running the server

python server.py server_config.json

The server binds to all local interfaces on the configured port.

Running a client

In another terminal:

python client.py 127.0.0.1 12345

Start a second client in another terminal to test two-player room behaviour.

Client commands

At the Enter command: prompt, use:

REGISTER
LOGIN
ROOMLIST
CREATE
JOIN
QUIT

The client asks for any additional information interactively, such as username, password, room name, or whether to join as a player or viewer.

During a game, a player is prompted to enter either:

x y

where each coordinate is between 0 and 2, or:

FORFEIT

Protocol overview

The application uses colon-separated text messages over TCP.

Examples include:

LOGIN:<username>:<password>
REGISTER:<username>:<password>
ROOMLIST:<PLAYER|VIEWER>
CREATE:<room-name>
JOIN:<room-name>:<PLAYER|VIEWER>
PLACE:<x>:<y>
FORFEIT

Server-to-client game messages include:

BEGIN:<player-1>:<player-2>
INPROGRESS:<current-player>:<other-player>
BOARDSTATUS:<encoded-board>
GAMEEND:<encoded-board>:<reason>:<winner>

The encoded board uses:

0 — empty cell

1 — X

2 — O

Repository structure

Tic-Tac-Toe/
├── server.py            # Authentication, rooms, and socket server
├── client.py            # Interactive command-line client
├── game.py              # Board and win/draw helper functions
├── game_in.py           # In-room multiplayer game session
├── tictactoe.py         # Local board/game helper implementation
├── server_config.json   # Port and database configuration
└── user_database.json   # Local JSON user records

Architecture

Server

server.py uses selectors.DefaultSelector to accept and read multiple client connections. It parses commands, authenticates users, updates room state, and starts a GameIn session when a room has two players.

Client

client.py provides a text interface for account, room, and gameplay actions. It converts user input into protocol messages and renders server responses.

Game session

game_in.py stores players, viewers, symbols, board state, turn state, and game-end flags. It broadcasts game events to all sockets associated with the room.

Known issues

The current code should be treated as a work in progress. Important issues include:

player_use_symbols is created with usernames as keys but is later accessed with socket objects.

Board placement does not yet validate occupied cells or coordinate bounds in the session layer.

Win and draw checks are not consistently integrated into the network gameplay loop.

Some client comparisons use integers where protocol values are strings.

Player/viewer input validation contains logic that can reject valid options.

The game-session start path contains duplicated or conflicting execution logic.

TCP messages are assumed to arrive as complete application messages; production code needs framing or buffering.

The flat JSON database is not safe for concurrent production writes.

Connections are unencrypted and there is no rate limiting or account lockout.

Recommended next steps

Fix username/socket mappings in GameIn.

Add message framing, for example newline-delimited JSON.

Validate moves before updating the board.

Call win/draw checks after each accepted move.

Add locks around shared room and user state.

Replace the JSON database with SQLite or PostgreSQL.

Add unit and integration tests for authentication, room state, and full games.

Add structured logging and clean disconnect handling.

Use TLS before exposing the server outside a trusted local network.

Security notice

This project is suitable for local learning and experimentation only. Do not expose it directly to the public internet or reuse the included database for real accounts.

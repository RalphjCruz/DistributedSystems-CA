import socket # To handle network communication
import threading # Used to handle multiple clients concurrently
import json # Import json to work with JSON data

SELLERS_FILE = "sellers.json" # File used to store data

def load_sellers():
    try:
        with open(SELLERS_FILE, "r") as f: # Try to open file in read only mode
            return json.load(f) # Load and return the JSON content from file
    except: # If error
        return {} # Return an empty dictionary

def handle_client(sock):
    try:
        sellers = load_sellers() # Load all the sellers from json file

        if sellers:
            message = "Available Sellers:\n" # Message used to list all sellers
            for sid, info in sellers.items():
                message += f"ID={sid}, Host={info['host']}, Port={info['port']}\n" # Append seller details
        else:
            message = "No sellers available.\n"

        sock.sendall(message.encode()) # Send message to buyers
    finally:
        sock.close() # Close connection to the client

def start_market():
    print("Market running on port 8888") # Print message for feedback
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCp/IP socket
    server.bind(("127.0.0.1", 8888)) # Bind the socket to localhost on port 8888
    server.listen(4) # Listen for incoming connections (up to 4 in the queue)

    while True:
        client_sock, addr = server.accept() # Wait for a client to connect
        print(f"Buyer connected from {addr}")
        threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()

if __name__ == "__main__":
    start_market()

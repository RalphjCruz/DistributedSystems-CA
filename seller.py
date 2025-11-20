import socket # This is used for handling network connections (TCP)
import threading # Used to run multiple threads for concurrency
import time # For time related functions
import json # To read and write to JSON files

class Seller:
    def __init__(self, node_id, host, port, items):
        # Seller class with parameters
        self.node_id = node_id # Seller's unique identifier
        self.host = host # The server will bind to localhost
        self.port = port # This is the port number the server will listen to
        self.items = items # Dictionary containing item names as keys and their stock as values

        self.current_item = None # A flag almost, this is to keep a track of what item is being sold
        self.time_left = 0 # How much time is left for the current session
        self.selling = False # This is a flag to check if an item is being sold

        self.lock = threading.Lock() # This is to manage concurrent access to shared resources aka the items
        self.clients = [] # A list is used to store connected buyers (clients)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Server socket created using IPv4 and TCP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Enable address reuse to prevent errors if the server restarts

        self.sock.bind((self.host, self.port)) # This is used to bind the socket to the given host and port

    # Function used to send message to all connected buyers
    def notify_buyers(self, message):
        tagged = "Notification|" + message # When a 
        failed = [] # This is used to store clients that failed to receive the message

        for client in self.clients: # Loop through all clients
            try:
                client.sendall((tagged + "\n").encode()) # Send the notification to all clients attached to the seller
            except:
                failed.append(client) # If sending the message fails, the client will be appended to 'failed' list

        for i in failed:
            if i in self.clients:
                self.clients.remove(i) # If the message failed to send, remove client 

    # Start the connection between seller server and handle incoming connections.
    def start_selling(self):
        print(f"Seller {self.node_id} Listening on port {self.port}")
        self.sock.listen(4) # This listens for incoming connections (A max of 4)

        # A separate thread is used to handle all the buyers 
        threading.Thread(target=self.accept_buyer, daemon=True).start()

        while True:
            self.sell_item() # While true, refer to sell_item function, but select and sell an item

    # Accept the buyer connection, and assign a new thread for handling
    def accept_buyer(self):
        while True:
            # addr has IP address and port
            client_sock, addr = self.sock.accept() # Accept a new client connection, as the seller. sock.accept() returns 2 values, a new socket object for client, and an address containing the IP address
            print(f"Buyer {self.node_id} Buyer connected: {addr}") # For seller to see, print the address of connected buyer.

            self.clients.append(client_sock) # Add the client socket to list of connected clients

            # Start a new thread to handle the buyer's commands
            # threading.Thread allows handle_buyer to run in parallel to main operations, so the server can still interact with buyer
            # daemon threads are threads that automatically close when main program exits. This lets the server keep running while buyer threads are still working
            threading.Thread(target=self.handle_buyer, args=(client_sock,), daemon=True).start()

    # Allow the seller to select first item and start session.
    def sell_item(self):
        print("\nChoose an item to sell:")
        for i, item in enumerate(self.items.keys(), start=1):
            print(f"{i}. {item} (stock: {self.items[item]})") # List available items and the stock

        # Prompt variable for choice
        choice = None
        names = list(self.items.keys()) # Get the list of item names

        while choice is None:
            try:
                n = int(input("Enter number: ").strip()) # Seller's input
                if 1 <= n <= len(names):
                    choice = names[n - 1] # Set the chosen item
                else:
                    print("Invalid number.")
            except:
                print("Numbers only.")

        # This sets what item is for sale
        self.current_item = choice
        # Set the sale time
        self.time_left = 60
        # Flage to show that the item is in the middle of being sold
        self.selling = True

        # Seller announcement
        print(f"\nCurrently selling: '{self.current_item}' ({self.items[self.current_item]} stock)")
        # Let all buyers know what item is being sold
        self.notify_buyers(f"New item on sale: {self.current_item} Stock={self.items[self.current_item]}")

        # Keep a track of start time of the sale
        start_time = time.time()
        warned_10 = False # Flag for buyers at the 10 second mark
        timer = 60 # Sale duration in seconds

        # Loop while there is time, and there are still more of the item available
        while self.time_left > 0 and self.items[self.current_item] > 0:
            time.sleep(1) # Wait one second
            time_passed = int(time.time() - start_time) # Used to calculate time that has passed
            self.time_left = max(0, timer - time_passed) # Update the remainiing time

            if self.time_left % 5 == 0: 
                print(f"Time left: {self.time_left}s") # For the seller, every 5 seconds the seller is alerted

            if self.time_left == 10 and not warned_10:
                self.notify_buyers("10 seconds left for this item.") # If buyers are not notified yet and there is 10 seconds left, notify all buyers there is 10 seconds left
                warned_10 = True

        # If item is sold out
        if self.items[self.current_item] <= 0:
            print(f"Item sold out.")
        else:
            self.notify_buyers("Sale session ended.")

        print(f"Finished selling '{self.current_item}'.")
        self.selling = False


    def handle_buyer(self, sock):
        # Initiailize buyer_id
        buyer_id = None

        try:
            # Confirmation message for buyer
            sock.sendall(b"Connected|Connected to seller.\n")
            
            while True:
                try:
                    data = sock.recv(1024) # Receive data from buyer, 1024 bytes in size
                except ConnectionResetError:
                    # Client disconnected abruptly
                    break

                if not data:
                    break # Exit if no data is received

                command = data.decode().strip().split() # Decode and split the command into parts

                # Handle the ID command for registering buyer
                if command[0].upper() == "ID":
                    buyer_id = command[1] # Register buyer's ID
                    sock.sendall(b"Reply|Buyer ID registered.\n")
                    continue

                # If command is LIST, list the available items
                if command[0].upper() == "LIST":
                    with self.lock:
                        # Create an empty string to hold the message
                        message = ""

                        # Loop through each item and its stock
                        for item, stock in self.items.items():
                            # Add the item and stock to the message string, formatted as item(stock)
                            message += f"{item}({stock}), "

                        # Remove the last comma and space
                        message = message.rstrip(", ")

                    # Send the message to the buyer
                    sock.sendall(f"Reply|Items: {message}\n".encode())

                # Info about current  item
                elif command[0].upper() == "CURRENT":
                    if not self.selling:
                        sock.sendall(b"Reply|No active sale.\n")
                    else:
                        with self.lock:
                            stock = self.items[self.current_item]
                            sock.sendall(f"Reply|Current: {self.current_item}, stock={stock}, time={self.time_left}s\n".encode())

                # Buy command to allow buyer to purchase an item
                elif command[0].upper() == "BUY":
                    # If the buyer doesnt have a buyer_id 
                    if not buyer_id:
                        sock.sendall(b"Reply|Error: Buyer ID not set.\n")
                        continue
                    
                    # A check to see if the item is being sold currently
                    if not self.selling or self.time_left <= 0:
                        sock.sendall(b"Reply|Sale is over. You cannot buy.\n")
                        continue

                    # Check to see if the command passed is of length less than 2 (provide a number after buy)
                    if len(command) < 2:
                        sock.sendall(b"Reply|Usage: BUY <amount>\n")
                        continue

                    try:
                        # Converts the above number into an integer, an places into quantity
                        quantity = int(command[1])
                    except:
                        sock.sendall(b"Reply|Invalid amount.\n")
                        continue

                    # Lock used to protect the shared item (prevent other threads from accessing)
                    with self.lock:
                        stock = self.items[self.current_item]

                        # If buyer trying to buy more than the available
                        if quantity > stock:
                            sock.sendall(f"Reply|Only {stock} left.\n".encode())
                        else:
                            self.items[self.current_item] -= quantity # Reduce the stock if within amounts
                            new_stock = self.items[self.current_item] # New stock used for display
                            sock.sendall(f"Reply|Purchase OK: bought {quantity}.\n".encode())

                            # Two print messages for seller
                            print(f"Buyer {buyer_id} bought {quantity} of {self.current_item} from Seller {self.node_id}")
                            print(f"Remaining: {new_stock}")

                            # notify_buyers new stock
                            self.notify_buyers(f"Item '{self.current_item}' now has {new_stock} left.")

                            if new_stock <= 0:
                                self.notify_buyers(f"{self.current_item.upper()} has been sold out")

                # Disconnect buyer
                elif command[0].upper() == "QUIT":
                    sock.sendall(b"Reply|You have left.\n")
                    break # Exit loop if buyer quits

                else:
                    sock.sendall(b"Reply|Unknown command.\n")

        except Exception as e:
            print(f"Error handling buyer: {e}") # Just print exceptions

        finally:
            # Clean up and close connection
            try:
                sock.close()
            except:
                pass

            if sock in self.clients:
                self.clients.remove(sock) # Remove disconnected client (their socket) from the list
            print("Buyer disconnected.")

if __name__ == "__main__":
    print("Seller terminal")
    node_id = int(input("Enter Seller ID: ")) # Prompt for seller ID
    host = "127.0.0.1" # localhost
    port = int(input("Enter Port (example: 5000): ")) # Prompt for port

    print("\nEnter starting amount:")
    items = {
        "flower": int(input("Flower stock: ")),
        "sugar": int(input("Sugar stock: ")),
        "potato": int(input("Potato stock: ")),
        "oil": int(input("Oil stock: "))
    }

    # Save seller information to sellers.json
    sellers = {}

    try:
        with open("sellers.json", "r") as f:
            sellers = json.load(f) # Load existing sellers
    except:
        sellers = {} # If no sellers file exists, create an empty dictionary

    sellers[str(node_id)] = {"host": host, "port": port} # Add the new seller to the dictionary

    with open("sellers.json", "w") as f:
        json.dump(sellers, f, indent=4) # Save the seller info into a JSON file

    seller = Seller(node_id, host, port, items) # Create the seller object

    # Start the seller in a new thread
    t = threading.Thread(target=seller.start_selling, daemon=False)
    t.start()

    while True:
        time.sleep(1)

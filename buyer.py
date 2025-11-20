import socket # Socket module for network communication
import json # Used to read and write JSON data
import threading # Used to handle concurrent connections (multithreading)
import time
import random


class BuyerClient:
    def __init__(self):
        # Initialize buyer object
        self.seller_sock = None # This will hold the socket to communicate with seller
        self.last_reply = None  # used to store last reply from seller (from the server)

        # Generate random id
        self.buyer_id = str(random.randint(1000, 9999))

        # Register buyer ID and save to JSON file
        self.register_buyer_id()

    # Register buyer ID and save in file
    def register_buyer_id(self):
        try:
            with open("buyers.json", "r") as f:
                buyers = json.load(f)
        except:
            # If file doesnt exist, initialize empty dicionary
            buyers = {}

        # Save buyer uniquely, their ID as the key
        buyers[self.buyer_id] = {"connected": False}

        # Write updated buyers data back to the buyers.json file
        with open("buyers.json", "w") as f:
            json.dump(buyers, f, indent=4)

        print(f"Your Buyer ID is {self.buyer_id}")

    def join_market(self):
        # Create a new socket to connect to the market server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 8888)) # Connect to the market server, on localhost on port 8888

        print("\nMARKET")
        # Receive and print the welcome message from the market server
        print(sock.recv(4096).decode())

        # Close socket after receiving the message
        sock.close()

    # Function (thread) to listen for live messages from the seller
    def start_listener(self):
        def listen():
            # This loop listens for messages from the seller while connected
            while self.seller_sock:
                try:
                    message = self.seller_sock.recv(4096) # Receive up to 4096 bytes of data from seller

                    if not message: # If no data received, sleep for a short time and continue
                        time.sleep(0.1)
                        continue

                    decoded = message.decode().strip() # Decode message and remove space

                    # this checks if the decoded message is to notify all
                    if decoded.startswith("Notification|"):
                        clean = decoded.replace("Notification|", "") # Remove notification
                        print(f"\n{clean}")
                        print("Menu choice: ", end="", flush=True) # Prompt user input after displaying notif

                    # Checks if message is a reply or connected
                    elif decoded.startswith("Reply|") or decoded.startswith("Connected|"):
                        # Save the reply message after the reply or connected message
                        self.last_reply = decoded.split("|", 1)[1]

                except (ConnectionResetError, OSError):
                    break # Break loop if connection is reset or there is an OS level error
                except:
                    continue

        # Start listener in a new thread so it runs concurrently
        t = threading.Thread(target=listen, daemon=True)
        t.start()

    # Connect buyer to the seller using seller's ID
    def connect_to_seller(self):
        # Prompt the buyer to enter the seller id they want to buy
        seller_id = input("Enter Seller ID: ")

        # Open the sellers.json file and read the list of available sellers
        with open("sellers.json", "r") as f:
            sellers = json.load(f)

        # Check if the entered ID exists in the list
        if seller_id not in sellers:
            print("Invalid seller ID.")
            return

        # Retrieve sellers host and port
        host = sellers[seller_id]["host"]
        port = sellers[seller_id]["port"]

        # Create a new socket to connect to the seller
        self.seller_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the seller by using the retrieved host and port
        self.seller_sock.connect((host, port))

        self.last_reply = None # Reset the last reply variable
        self.start_listener() # Start the listener thread to receive messages

        # Wait for welcome message
        while self.last_reply is None:
            time.sleep(0.05) # This is used to avoid busy-waiting

        # Otherwise, send the buyer id to seller
        self.seller_sock.sendall(f"ID {self.buyer_id}".encode())
        time.sleep(0.1)

        # Mark buyer as connected in buyers.json
        try:
            with open("buyers.json", "r") as f:
                buyers = json.load(f)
            buyers[self.buyer_id]["connected"] = True # Set buyers connected status to True
            with open("buyers.json", "w") as f:
                json.dump(buyers, f, indent=4) # Save the buyers info
        except:
            pass

        print(self.last_reply) # Print the seller's reply to the console
        self.last_reply = None # Reset the last reply for next interaction

    # Request and show the list of available items from the current seller
    def list_items(self):
        # Check first if the buyer is connected to a seller
        if not self.seller_sock:
            print("Connect to a seller first.")
            return

        # Reset the reply variable
        self.last_reply = None
        self.seller_sock.sendall(b"LIST") # Send the list command to the seller to request available items

        while self.last_reply is None:
            time.sleep(0.05)  # Avoid busy waiting

        print(self.last_reply)  # Print the sellers response
        self.last_reply = None  # Reset the last reply for the next interaction

    def buy_item(self):
        # Check first if the buyer is connected to a seller
        if not self.seller_sock:
            print("Connect to a seller first.")
            return

        # Ask seller what is currently selling
        self.last_reply = None
        self.seller_sock.sendall(b"CURRENT") # Send the current command using byte literal, to the seller to get current item details

        while self.last_reply is None:
            time.sleep(0.05)  # Avoid busy waiting

        print(self.last_reply)  # Print the sellers response
        self.last_reply = None  # Reset the last reply for the next interaction

        amount = input("Enter amount: ")

        # Send buy command to the seller
        self.last_reply = None
        self.seller_sock.sendall(f"BUY {amount}".encode())

        while self.last_reply is None:
            time.sleep(0.05)  # Avoid busy waiting

        print(self.last_reply)  # Print the sellers response
        self.last_reply = None  # Reset the last reply for the next interaction

    # Disconnect from the seller
    def leave_seller(self):
        if self.seller_sock:
            self.last_reply = None
            self.seller_sock.sendall(b"QUIT") # Send the quit command to disconnect from seller

            # Wait for seller's reply
            while self.last_reply is None:
                time.sleep(0.05)  # Avoid busy waiting

            print(self.last_reply)  # Print the sellers response
            self.last_reply = None  # Reset the last reply for the next interaction

            self.seller_sock.close() # Close socket to seller
            self.seller_sock = None
            print("Disconnected from seller.")

            # Mark buyer as disconnected in buyers.json
            try:
                with open("buyers.json", "r") as f:
                    buyers = json.load(f)
                buyers[self.buyer_id]["connected"] = False
                with open("buyers.json", "w") as f:
                    json.dump(buyers, f, indent=4) # Save updated buyers data
            except:
                pass

    def menu(self):
        while True:
            print("Buyer Menu")
            print("1. Join/Check Market")
            print("2. Connect to Seller")
            print("3. Leave Seller")
            print("4. List Items")
            print("5. Buy Item")
            print("6. Exit Market")


            choice = input("Menu choice: ")

            if choice == "1":
                self.join_market() # Join market (connect to the market server)
            elif choice == "2":
                self.connect_to_seller() # Connect to a seller
            elif choice == "3":
                self.leave_seller() # Leave the seller, go back to market
            elif choice == "4":
                self.list_items() # List available items from seller
            elif choice == "5":
                self.buy_item() # Buy an item from seller
            elif choice == "6":
                self.leave_seller() # 
                print("You have left the market") # Leave seller and break from program
                break
            else:
                print("Invalid choice.")

# Entry point top run buyer client
if __name__ == "__main__":
    BuyerClient().menu()

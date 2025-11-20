Prerequesites:
1. Ensure you have the latest version of python installed on your system 
(https://www.python.org/)
2. Add python to your system PATH.

Instructions:
Setting the project up:
Download the files buyer.py, market.py, seller.py
Ensure all 3 files are all in the same directory

Step 1: Start market server
Open a new CMD/terminal (I use VS Code)
Navigate to the directory where the files are saved
Run the following command: “python market.py”
The market will listen for incoming buyer connections

Step 2: Start seller server
Open a new CMD/terminal
Navigate to the directory where the files are saved
Run the seller server by executing “python seller.py”
This will start a seller server and wait for a connection from buyers
You can provide item quantities 
You can open multiple seller servers

Step 3: Start buyer server
Open a new CMD/terminal
Navigate to the directory where the files are saved
Run the seller server by executing “python buyer.py”
The buyer will connect to the market server and will get the option to retrieve a list of available sellers in the market (by using sellers.json)

You can do various testing.
There can be multiple seller servers running, and multiple buyers that are connected to one seller.

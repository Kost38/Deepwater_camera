#!/usr/bin/python3

#imports
import socket 
import threading


class ChatServer:
    
    clients_list = []

    last_received_message = ""

    def __init__(self):
        self.server_socket = None
        self.create_listening_server()

    #listen for incoming connection
    def create_listening_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket using TCP port and ipv4
        local_ip =  '127.0.0.1'
        local_port = 10319
        # this will allow you to immediately restart a TCP server
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # this makes the server listen to requests coming from other computers on the network
        self.server_socket.bind((local_ip, local_port))
        print("Listening for incoming messages..")
        self.server_socket.listen(5) #listen for incomming connections / max 5 clients
        self.receive_messages_in_a_new_thread()


    def receive_messages_in_a_new_thread(self):
        while True:
            client = so, (ip, port) = self.server_socket.accept()
            print(so)            
            self.add_to_clients_list(client)
            print('Connected to ', ip, ':', str(port))
            t = threading.Thread(target=self.receive_messages, args=(so,))
            t.start()

    #add a new client 
    def add_to_clients_list(self, client):
        if client not in self.clients_list:
            self.clients_list.append(client)

    #function to receive new msgs
    def receive_messages(self, so):
        #while True:
        incoming_buffer = so.recv(256) #initialize the buffer
        if not incoming_buffer:
            return
            #break
#            self.last_received_message = incoming_buffer.decode('utf-8')
        self.last_received_message = incoming_buffer
        print(self.last_received_message.hex(' '))
        self.broadcast_to_all_clients(so)  # send to all clients
        so.close()


    #broadcast the message to all clients 
    def broadcast_to_all_clients(self, senders_socket):
        senders_socket.send(self.last_received_message)
        for client in self.clients_list:
            socket, (ip, port) = client
            print('client_socket', socket)
            print('ip=',ip, '  port=', port)
            if socket is not senders_socket:
#                socket.sendall(self.last_received_message.encode('utf-8'))
                try:
                    socket.sendall(self.last_received_message)
                except:
                    print("error client")
#                   print(self.clients_list)
                    self.clients_list.remove(client)




if __name__ == "__main__":
    ChatServer()
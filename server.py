import socket
import os
import time
from _thread import *
import threading
import re


class Client:
    def __init__(self):
        self.isConnected = False
        self.ip = ""
        self.conn = ""
        self.name = ""
        

class Manager(Client):
    def __init__(self):
        Client.__init__(self)
        
class Greenhouse(Client):
    def __init__(self):
        Client.__init__(self)
        self.gCode = -1
        self.goal = 52
        self.temperature = 0


manager = Manager()
manager.ip = "192.168.0.21"
manager.name = "manager"

greenhouseIp = ['kkk', 'xxx', 'yyy', 'zzz']                                         # [REPLACE]
greenHouses = []                                                                    #The array of greenhouses, we have 4


HEADER = 64 
port = 8000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
ServerSocket = socket.socket()                                              
host = "192.168.0.21"



def threaded_client(Client,address):                                                # Clientlerden gelen verilerle işlem yapma fonksiyonu 
    global greenHouses
    ilkmesaj = "Hoşgeldiniz "                                                 
    idx = greenhouseIp.index(address[0])                                            # ip adresine göre 
    greenHouses[idx].goal = 51
    greenHouses[idx].isConnected = True
    Client.send(ilkmesaj.encode('utf-8') + greenHouses[idx].name.encode('utf-8'))   # Seraya hoşgeldin mesajı yolla
    while True:                                                                     # sonsuz döngüye gir
        data = Client.recv(1024)                                                    # Clientten veri bekle gelen veriyi dataya eşitle
        if not data:                                                                # Eğer veri gelmemişse
            continue                                                                # while döngüsünün başına ilerle
        else:                                                                       # Eğer veri gelirse
            veri = data.decode(FORMAT);                                            # veriyi okunabilir formata çevir
            print(greenHouses[idx].name + ' Clientinin Sıcaklık Değeri: ' + veri)   # ekrana gelen veriyi yazdır 
            greenHouses[idx].temperature = int(veri)                                #?
    Client.close()                                                                  # Herhangi bir şekilde while döngüsünden çıkarsa client bağlantısını kes


#def input_girisi(Client,address):                                                  # Cliente veri yollama işlemleri fonksiyonu
#    idx = greenhouseIp.index(address[0])                                           # yap ve client_name eşitle
#     while True:                                                                   # sonsuz döngüye gir
#        user = input();                                                            # kullanıcıdan veri yazmasını bekle
#        Client.send(user.encode('utf-8'))                                          # Yazdığı veriyi byte dizisine çevir ve cliente yolla
#        print(greenHouses[idx].name + ' Clientinin sıcaklık değeri değiştirildi.') # Ekrana bilgi yazdır


def handleManager(conn, addr): 
    print(f"\n[NEW CONNECTION] {addr} connected.")
    manager.conn = conn
    #postClients(addr, "[CONNECTED]")
    manager.isConnected = True 
    try:
        while manager.isConnected:                                                   # Connected oldugu surece
            msgLength = conn.recv(HEADER).decode(FORMAT)                             # Oncelikle mesajin uzunlugunu al
            if msgLength:                                                            # Boyle bir header bilgisi geldiyse, mesaj da gelecek demektir
                msgLength = int(msgLength) 
                msg = conn.recv(msgLength).decode(FORMAT)                            # mesaji al
                if msg and msg == DISCONNECT_MESSAGE:                                #mesaji aldiysan ve disconnect mesajiysa...
                    print(f"Message: [{addr}]: {msg}")
                    manager.isConnected = False
                    print(f"\n[MANAGER DISCONNECT] {addr} disconnected.")
                elif msg: 
                    gCode, command = parseManagerCommand(msg)
                    if command !=  'X':
                        postToGreenhouse(gCode, command)
                    else:
                        postToManager(conn, createMessageAbout(gCode))
                    print(f"Message: [{manager.name}][{addr}]: {msg}")
                    #postToManager(conn, "RCVD")
        conn.close()                                                                
    except Exception as e:
        print(e)

def postToManager(conn, msg): 
    message = msg + '\n'
    message = message + ( ' ' * (HEADER - len(message)))
    conn.send(message.encode(FORMAT))

def sendEmptyPackages(conn):
    while (manager.isConnected):
        time.sleep(1)
        try:
            postToManager(conn, "")
        except:
            continue


def parseManagerCommand(command):
    pieces = re.findall(r"\.?([a-zA-z0-9]+)\.?\s?", command)
    command = pieces[0]
    gCode = pieces[1]
    return gCode, command

def createMessageAbout(gCode):
    global greenHouses
    message = ""
    gCode = int(gCode)
    message = message + str(gCode)
    message += "."
    message += str(greenHouses[gCode-1].goal)
    message += "."
    message += str(greenHouses[gCode-1].temperature)
    message += "-"
    return message
    

def postToGreenhouse(gCode, command):
    global greenHouses
    client = greenHouses[gCode-1].conn
    client.send(command.encode(FORMAT)) 
    greenHouses[gCode-1].goal = int(command)
    print(greenHouses[gCode-1].name + ' Clientinin sıcaklık değeri değiştirildi.')



def start():
    global greenHouses
    for i in range (1,5):
        gh = Greenhouse()
        gh.gCode = i
        gh.ip = greenhouseIp[i-1]
        gh.name = "Greenhouse " + str(i)
        greenHouses.append(gh)

    try:
        ServerSocket.bind((host, port))                                         # Verilen host ve porta göre socket haberleşmeyi başlat
    except socket.error as e:                                                   # hata çıktıysa
        print(str(e))                                                           # ekrana hatanın kodunu yazdır

    print('İstemciler bekleniyor...')                                           # ekrana bilgi mesajı yazdır
    ServerSocket.listen(5)                                                      # Socket sunucuya bağlanacak client sayısını belirle

    while True:                                                                 # sonsuz döngüye gir
        Client, address = ServerSocket.accept()                                 # Sunucuyla bağlantı kurulursa clientin bağlantısını ve ip adresini tut
        print(address[0] + ':' + str(address[1]) + ' Clientine bağlanıldı.')    # Ekrana bağlanan clientin ip adresini yansıt
        if address[0]== manager.ip:
            thread = threading.Thread(target = handleManager, args = (Client, address))
            thread2 = threading.Thread(target = sendEmptyPackages, args = (Client,))
            thread.start()
            thread2.start()
        else:    
            start_new_thread(threaded_client, (Client, address,  ))              # threaded_client fonksiyonunu çalıştır (Birden çok kullanıcı için ayrı ayrı başlatılır / Multithreading)
#            start_new_thread(input_girisi, (Client, address,  ))                # input_girisi fonksiyonunu çalıştır (Birden çok kullanıcı için ayrı ayrı başlatılır / Multithreading)
    ServerSocket.close()                                                         # Herhangi bir şekilde while döngüsünden çıkarsa socket haberleşmeyi bitir.


start()







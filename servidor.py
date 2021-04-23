import socket
import hashlib
import threading
import time
import datetime
import os

lock = threading.Lock()


def pedirInput():
    fName = ""
    fileT = ""
    entr = int(input("Ingrese archivo que quiere enviar 1 (100 MB) o 2 (250MB) "))
    if (entr == 1):
        fName = "./files/100MB.txt"
        fileT = ".txt"
    elif (entr == 2):
        fName = "./files/250MB.txt"
        fileT = ".txt"
    entr = int(input("Ingrese el numero de clientes en simultaneo a enviar el archivo "))
    numClientes = entr
    return fName, fileT, numClientes


f_data = pedirInput()
fName = f_data[0]
n_clientes = f_data[2]
fileT = f_data[1]
c_clientes = 0
attend = False

def createLog():
    print("Creando log")

    # Fecha y hora --creacion log
    date = datetime.datetime.now()

    logName = "Logs/Logs-server/" + str(date.timestamp()) + ".txt"
    logFile = open(logName, "a")
    logFile.write("Fecha: " + str(date) + "\n")

    # Nombre del archivo y tamanio
    fileN = fName.split("/")
    fileN = fileN[2]

    logFile.write("Nombre del archivo: " + fileN + "\n")

    fileSize = os.path.getsize(fName)

    logFile.write("Tamanio del archivo: " + str(fileSize) + " bytes\n")
    logFile.write("----------------------------------------\n")

    logFile.close()
    return logName


# Crear el archivo de log
logName = createLog()


def logDataCliente(recepcion, nTime, numPaqEnv, numPaqRecv, hashR, hash):
    with lock:
        paquetesEnv = "Numero de paquetes enviados por el servidor:" + str(numPaqEnv) + "\n"
        paquetesRec = "Numero de paquetes recibidos por el cliente:" + str(numPaqRecv) + "\n"
        tiempoT = "Tiempo: " + str(nTime) + " segundos\n"
        separador = "\n---------------------------------------\n"
        hash = "\nHASH calculado en el servidor: \n" + hash
        logFile = open(logName, "a")
        logFile.write(recepcion + "\n" + paquetesEnv + paquetesRec + tiempoT + hashR + hash + separador)
        logFile.close()


host = ""
BUFFER = 4096

def servidor(port1,dir):
    global c_clientes
    global attend
    port=20001+port1
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Bind to address and ip
    sock.bind((host, port))
    sock.sendto(str(port).encode(),dir)
    print("UDP server up and listening at port ",port)

    while True:
        data = sock.recvfrom(BUFFER)
        msg = data[0]
        dir = data[1]

        print('Server received', msg.decode())

        if (msg.decode() == "READY"):
            c_clientes += 1
            print("Numero Clientes Conectados: ", c_clientes)
            sha1 = hashlib.sha1()
            while True:
                if (c_clientes >= n_clientes or attend):
                    print("Starting to send")
                    break
            attend = True
            i = 0

            sock.sendto(fileT.encode(), dir)

            time.sleep(0.01)

            inicioT = time.time()
            f = open(fName, 'rb')
            while True:
                i += 1
                data = f.read(BUFFER)
                if not data:
                    break
                sha1.update(data)
                sock.sendto(data,dir)
            print("Archivo Enviado")

            # Envio de Hash
            has = str(sha1.hexdigest())
            sock.sendto(("FINM" + has).encode(),dir)
            f.close()


            data = sock.recvfrom(BUFFER)
            # Notificacion de recepcion
            datosCiente = data[0].decode().split("/")
            recepcion = datosCiente[1]
            print(recepcion)

            # Notificacion de tiempo
            finT = float(datosCiente[2])
            totalT = finT - inicioT
            # print("Tiempo total:",totalT, "Segundos")

            # Numero de paquetes recibidos por el cliente
            paqRecv = datosCiente[0]

            hashR = datosCiente[4]
            logDataCliente(recepcion, totalT, i, paqRecv, hashR, has)

            print('Fin envio')
            c_clientes -= 1
            print("Numero Clientes Conectados: ", c_clientes)

            # Notificacion de fin de cliente o no
            terminS = datosCiente[3]
            # print("Mensaje del cliente: ", terminS)

            if (terminS == "TERMINATE"):
                print(terminS)
                sock.close()
                print("Fin Servidor en puerto ",port)
                break



port1=20001

# UDP ------> socket.AF_INET, socket.SOCK_DGRAM
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
sock.bind((host, port1))
i=1
while True:
    data = sock.recvfrom(BUFFER)
    msg = data[0]
    dir = data[1]

    if (msg.decode() == "REQUEST"):
        if(i==26):
            i=1
        t = threading.Thread(target=servidor, args=(i,dir))
        i += 1
        t.start()

    if (msg.decode() == "END"):
        print("FIN CONEXIONES")
        break
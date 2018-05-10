from bluedot.btcomm import BluetoothServer

from PIL import Image
import pyqrcode
from bluedot.btcomm import BluetoothAdapter

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography import exceptions 

import base64
import time
import os
from signal import pause

#def of global constants:
RECEV_IMGS_PATH = 'Recev_Images/'
LOGNAME = 'logfile_' + time.strftime("%d-%m-%y") + '.txt'

CAMERA_SERIAL = ''

first_conn = 0

if os.path.exists('key.code'):
    print('key.code leido de archivo')
else:
    chacha_key = ChaCha20Poly1305.generate_key()
    a = BluetoothAdapter()
    MAC = a.address

    block = chacha_key + MAC.encode() + time.strftime("%H%M%S").encode()

    print('Len of block: ' + repr(len(block)))

    block64 = base64.encodestring(block)
    
    print('Len of block64: ' + repr(len(block64)))

    keypair = pyqrcode.create(block64.decode())

    print('key.code escrito en archivo')
    keycode = open('key.code', 'wb')
    keycode.write(chacha_key) #escribir clave con write
    keycode.close()

    keypair.png('keycode.png', scale=7)

    a.allow_pairing(40)
    first_conn = 1
    

keycode = open('key.code', 'rb')
CHACHAKEY = keycode.read() #Cargar clave con read
print(CHACHAKEY)

image_sbin = ''
image_name = ''

def BLUEcryptosend(plaintext):
    
    aad = bytes(time.strftime("%d%m%y"), 'utf-8')
    chacha = ChaCha20Poly1305(CHACHAKEY)
    nonce = os.urandom(3) + aad + os.urandom(3)
    ct = chacha.encrypt(nonce, plaintext, aad)
    
    ct64 = base64.encodestring(ct + nonce + aad)
    
    s.send(ct64.decode())
    
    print(ct64.decode())
    
    return ct64.decode()

def BLUEdecrypt(ciphertext_base):
    try:
        ciphertext = base64.decodestring(ciphertext_base.encode())
        aad = ciphertext[len(ciphertext)-6:] ##bin
        nonce = ciphertext[len(ciphertext)-18:len(ciphertext)-6] ##bin
        ct = ciphertext[:len(ciphertext)-18] ##bin
        
        try:
            chacha = ChaCha20Poly1305(CHACHAKEY)
            data = chacha.decrypt(nonce, ct, aad)
            print('OK')
        
            return data

        except: ##mejorar Except
            print('ERROR DECRYPTING')
        
            return b'-1'
        
    except: 
        print('ERROR DECRYPTING')
        
        return b'-1'

def save_image(img_data, image_name):
    image = open(RECEV_IMGS_PATH + image_name, 'wb')
    image.write(img_data)
    
    image.close()

def logwrite(text):
    open_mode = ''
    if os.path.exists(LOGNAME):
        open_mode = 'a'
    else:
        open_mode = 'w'
    logfile = open(LOGNAME, open_mode)
    logfile.write('['+ time.strftime("%H:%M:%S") +']'+ text +'\n')
    
    logfile.close()

def data_received(data):
    global image_name
    global first_conn
    
    if(first_conn == 1):
        msg_bin = BLUEdecrypt(data)
        msg = msg_bin.decode()
        
        global HOUR
        
        CAMERA_SERIAL_prov = msg[:20]
        HOUR = msg[20:]
        
        print(CAMERA_SERIAL_prov)
        
        if(HOUR[:2] == time.strftime('%H')) and (int(time.strftime('%M'))- int(HOUR[2:4]) <= 1):
            global CAMERA_SERIAL
            CAMERA_SERIAL = CAMERA_SERIAL_prov
            first_conn = 0
            
    else:
    
        if(len(data) < 1008) and (image_name == ''):
            print(data)

            msg_bin = BLUEdecrypt(data)
            msg = msg_bin.decode()
        
            if(msg == '-1'):
                print('Error en la decodificación')
                BLUEcryptosend(b'NACK') #Do nothing, wait for a new packet.
            elif(msg[0:6]=='0x0011'):
                logwrite('[SYS]: ' + msg.lstrip('0x0011'))
                BLUEcryptosend(b'0x1001ACK')
            elif(msg[0:6]=='0x1100'):
                logwrite('[IMG]: ' + msg.lstrip('0x1100'))
                image_name = msg.lstrip('0x1100')
                BLUEcryptosend(b'0x1001ACK')
            elif(msg[0:6]=='0x1001'):
                if(msg.lstrip('0x1001') == 'ACK'):
                    a=1
                    #ACK recibido del cliente
                elif(msg.lstrip('0x1001') == 'NACK'):
                    #NACK recibido del cliente:
                    ##Reenvío de ACK
                    BLUEcryptosend(b'0x1001ACK')
                    
        else:
            global image_sbin
            image_sbin += data
            if(len(data) < 1008):
                
                print(image_sbin)
                msg_bin = BLUEdecrypt(image_sbin)
                
                try:
                    image_data = base64.decodestring(msg_bin)
                    save_image(image_data, image_name)
                    BLUEcryptosend(b'0x1001ACK')
                    image_sbin = ''
                    image_name = ''
                
                except:
                    image_sbin = ''
                    image_name = ''
                    BLUEcryptosend(b'0x1001NACK')
            
            

s = BluetoothServer(data_received)

if(first_conn == 1):
    time.sleep(60)
    if(first_conn == 1):
        print('Echando de la lista de emparejados')
        if(s.client_connected):
            os.system('./Throw_out.sh "'+s.client_address+'" | bluetoothctl -a')
        os.remove('key.code')
        
    elif(first_conn ==0):
        print('Emparejamiento correcto')

pause()


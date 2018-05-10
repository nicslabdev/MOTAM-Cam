from picamera.array import PiRGBArray
from picamera import PiCamera

from bluedot.btcomm import BluetoothClient, BluetoothAdapter 
import base64

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

import pyzbar.pyzbar as pyzbar

import shutil

import time
import cv2
import os
import numpy as np

from signal import pause

#########################3
doscaras = 0
#################################333

#initilize camera:
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 15
rawCapture = PiRGBArray(camera, size=(640, 480))

#camera warmup-time:
time.sleep(0.1)

#Def const variables:
CONFIDENCE_THRESHOLD = 60
TIME_INTER_NORMAL_FRAME = 9
TIME_INTER_ALERT_FRAME = 3

INITIAL_FOLDER = -2 #Crea una nueva carpeta por cada sujeto en el sistema

ack_recv = 0
nack_send = 0

HOUR = ''
MAC_BL = ''
KEY = b''

SERIAL = 'ABCDEFGHIJ0123456789'

first_conn = 0

try:
    keycode = open('key.code', 'rb')
    KEY = keycode.read(32) #Cargar clave con read
    MAC_BL = keycode.read(17).decode() #CargarMAC
    
    keycode.close()
    
    print('key.code leido de archivo')
    print(KEY)
    print(MAC_BL)
    #modo de inicialización normal

except :
    print('leyendo qr...')
    #lectura de codigo qr
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	
        image = frame.array
 
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
        QRcodes = pyzbar.decode(gray)
	
        if(len(QRcodes) == 1):
            print('Type: ' + QRcodes[0].type)
            print('Data: '+ QRcodes[0].data.decode() + '\n')
            
            
            key = open('key.code', 'wb')
            key.write(base64.decodestring(QRcodes[0].data))
            key.close()
            
            KEY = base64.decodestring(QRcodes[0].data)[:32]
            MAC_BL = base64.decodestring(QRcodes[0].data)[32:49].decode()
            HOUR = base64.decodestring(QRcodes[0].data)[49:].decode()
            
            rawCapture.truncate(0)
            break;
        
        rawCapture.truncate(0)
    
       
    print(KEY)
    print(MAC_BL)
    os.system('./Pairing_process.sh "'+MAC_BL+'" | bluetoothctl -a')
    time.sleep(20)
    first_conn = 1

#paths:
alert_img_path = 'alert-images'
train_img_path = 'training-images'

#Pre-charging xml files:
face_cascade = cv2.CascadeClassifier('/home/pi/opencv-3.3.0/data/lbpcascades/lbpcascade_frontalface.xml')

#---------------------------------------------------
#Def of folder configuration function:
def config_folders():
    dirs = os.listdir()
    if(any(dir == 'training-images' for dir in dirs)):
        shutil.rmtree('training-images')
        os.mkdir('training-images')
    else:
        os.mkdir('training-images')
        
    if(any(dir == 'alert-images' for dir in dirs)):
        shutil.rmtree('alert-images')
        os.mkdir('alert-images')
    else:
        os.kdir('alert-images')
        
#Def of function which finds pasarela's name by her BL_MAC_ADDRESS in pairing files of raspberry:
def mac2NAME(MAC):
    
    a = BluetoothAdapter()
    devices = a.paired_devices
    
    for d in devices:
        if(d[0] == MAC):
            return d[1]
    
    return 'error_mac'
#Def of sending cipher text by Bluetooth Serial Socket:
def BLUEcryptosend(plaintext):
      
    aad = bytes(time.strftime("%d%m%y"), 'utf-8')
    chacha = ChaCha20Poly1305(KEY)
    nonce = os.urandom(3) + aad + os.urandom(3)
    ct = chacha.encrypt(nonce, plaintext, aad)
    
    ct64 = base64.encodestring(ct + nonce + aad)
    
    c.send(ct64.decode())
    
    print(ct64.decode())
    
    time.sleep(2)
    
    global ack_recv
    if(ack_recv == 1):
        ack_recv = 0
        
        global nack_send
        nack_send = 0
        
    return ct64.decode()

def BLUEdecrypt(ciphertext_base):
    try:
        ciphertext = base64.decodestring(ciphertext_base.encode())
        aad = ciphertext[len(ciphertext)-6:] ##bin
        nonce = ciphertext[len(ciphertext)-18:len(ciphertext)-6] ##bin
        ct = ciphertext[:len(ciphertext)-18] ##bin
        
        try:
            chacha = ChaCha20Poly1305(KEY)
            data = chacha.decrypt(nonce, ct, aad)
            print('OK')
        
            return data

        except: ##mejorar Except
            print('ERROR DECRYPTING')
        
            return b'-1'
        
    except:
        print('ERROR DECRYPTING')
        
        return b'-1'
    
#Def of callback function for Bluetooth Serial Client:
def data_received(data):
    global nack_send
    global ack_recv
    
    recv_msg = BLUEdecrypt(data)
    recv_msgstr = recv_msg.decode()
    
    if(recv_msgstr == '0x1001ACK'):
        print('ACK received: ready to send a new package')
        akc_recv = 1
    elif(recv_msgstr == '0x1001NACK'):
        if(nack_send < 3):
            nack_send += 1
            BLUEcryptosend(last_package)
            print('NACK received: last package resend')
        else:
            ack_recv = 0
            nack_send = 0
            print('NACK received: maximun packages resend. NACK ignore.')
    else:
        if(nack_send < 3):
            nack_send += 1
            BLUEcryptosend(b'0x1001NACK')
            print('Error packet: NACK send')
        else:
            ack_recv = 0
            nack_send = 0
            print('Error packet: maximun packages resend. Ignoring package.')

#Def of sending loginfo to Bluetooth Serial Server:
def BLUEsendlog(type, text):
    pretext = ''
    if(type == 0):
        pretext = '0x0011'
    elif(type == 1):
        pretext = '0x1100'
    elif(type == 2):
        pretext = '0x1001'
        
    last_package = bytes(pretext + text, 'utf-8')
    BLUEcryptosend(last_package)

def BLUEsendimg(path, number):
    
    image = open(path+'/img'+repr(number)+'.jpg', 'rb')
    image_data = image.read()
    image_encode64 = base64.encodestring(image_data)
        
    last_package = image_encode64 #image 
    BLUEcryptosend(last_package)
    
#Def of training data preparation for face recognition:
def prepare_data(data_folder_path):
    
    faces = []
    labels = []
    
    #indexado: for dir_name
    subject_images_names = os.listdir(data_folder_path) #set into cs.path
    
    label = 0
    
    for image_name in subject_images_names:
            
        if image_name.startswith("."):
            continue;
            
        image_path = data_folder_path + "/" + image_name #setup current_image.path
        image = cv2.imread(image_path) #read face for current_subjet
            
        togray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
        faces.append(togray)
        labels.append(label)
            
    return faces, labels

#Def of face detect function:
def detect_face(image):
    
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.2, minNeighbors=5);
        
    if(len(faces) == 1):
            
        (x, y, w, h) = faces[0]
        return gray_image[y:y+w, x:x+h], faces[0]
    
        
    return [-1], len(faces)
    

#Def of image capture and face detection:
def capture_n_detect():
    
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        
        image = frame.array
        
        face, rect = detect_face(image)
        
        if(len(face) != 1):
        
            rawCapture.truncate(0)
            return face, rect
        
        elif(rect > 0):
            global doscaras
            s = 'Detecting ' + repr(rect) + ' faces in image'
            print(s)
            cv2.imwrite('/doscaras/save'+ repr(doscaras) +'.jpg', image)
            doscaras += 1
            
            
        rawCapture.truncate(0)
        
#Def of rectangle-drawing and name-writing functions:
def draw_rectangle(img, rect):
    (x, y, w, h) = rect
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

def draw_text(img, text, x, y):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
    
#Def recognition fuction:
def predict(image):

    label, confidence = face_recognizer.predict(image)
    
    print('Confidence value: ' + repr(confidence))
    
    if(confidence > CONFIDENCE_THRESHOLD):
        
        return 0
    
    else:
    
        return 1

#Def face to save into a defined path:
def save_subject_face(image, path):
        
    subject_images_names = os.listdir(path) #set into cs.path
        
    for image_name in subject_images_names:
            
        if image_name.startswith("."):
            subject_images_names.remove(image_name)
            
    s = path + '/img' + repr(len(subject_images_names)) + '.jpg'
    cv2.imwrite(s, image)
    
    return len(subject_images_names) #, folder_label #number of the image in the path

#Def of showface function:
def show_face(text, face):
    
    cv2.imshow(text, face)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()
    
#----------------------------------------------------------------------------
#Main function:
    
#Starting Bluetooth Serial Client:
c = BluetoothClient(mac2NAME(MAC_BL), data_received)

last_package = b''

if(first_conn == 1):
    
    print('Hola serial: ' + SERIAL)
    
    BLUEcryptosend(bytes(SERIAL + HOUR, 'utf-8'))
    time.sleep(5)

face_recognizer = cv2.face.LBPHFaceRecognizer_create()

config_folders()

folder_label = -1
previous_img_number = -1

Mode = 0

block_system = 0

Nframes_added = 0
refresh_training_data = 1 #Por defecto en cada reentrada se entrena el sistema con las fotos recien tomadas

Nalerts = 0

for x in range(0, 50):

   face, rect = capture_n_detect()
   
   previous_img_number = save_subject_face(face, train_img_path)

BLUEsendlog(0, 'System up, preparing data and starting temporal tracking')
       
while True: 
    
    if(block_system == 1):
        
        pause()
        
    if(refresh_training_data == 1):
    
        faces, labels = prepare_data(train_img_path)

        face_recognizer.train(faces, np.array(labels))
        
        refresh_training_data = 0
        BLUEsendlog(0, 'Training_images refreshed: ' + repr(len(faces)) + ' images found')
        
    if(Mode == 0):
        
        time.sleep(TIME_INTER_NORMAL_FRAME)
        
        face, rect = capture_n_detect()
        match = predict(face)
        
        if(match == 0):
            
            Mode = 1
            
            previous_img_number = save_subject_face(face, alert_img_path)
            
            BLUEsendlog(0, 'ALERT_MODE: Unknown Subject')
            BLUEsendlog(1, 'alertimg'+repr(previous_img_number)+'.jpg')
            
            BLUEsendimg(alert_img_path, previous_img_number)
            
            show_face('UNKNOWN', face)
            print('Entering ALERT_MODE: Unknown Subject')
        
        elif(match == 1):
            
            show_face('KNOWN', face)
            previous_img_number = save_subject_face(face, train_img_path)
            
            Nframes_added +=1;
        
            if(Nframes_added >= 10):
                refresh_training_data = 1
                Nframes_added = 0
            
        
    elif(Mode == 1):
        
        if(Nalerts <= 11):
            
            time.sleep(TIME_INTER_ALERT_FRAME)
            
            face, rect = capture_n_detect()
            match = predict(face)
    
            if(match == 0):
                
                show_face('UNKNOWN YET', face)
                previous_img_number = save_subject_face(face, alert_img_path)
                Nalerts += 1
                
                BLUEsendlog(0, 'ALERT_MODE: Unknown Subject. Alert number ' + repr(Nalerts))
                
                if(Nalerts == 4) or (Nalerts == 8):
                    BLUEsendlog(1, 'alertimg'+repr(previous_img_number)+'.jpg')
                    BLUEsendimg(alert_img_path, previous_img_number)
                
                Alerts_time_remain = (12-Nalerts)*TIME_INTER_ALERT_FRAME
                print('Continious at ALERT_MODE: alert_number='+repr(Nalerts)+', you have ' + repr(Alerts_time_remain) + ' secons to identificate yourself')
        
            elif(match == 1):
                
                Mode = 0
                Nalerts = 0 #recuperamos la normalidad, proxima entrada en Alert Mode con nAlert 0
                
                show_face('KNOWN NOW', face)
                previous_img_number = save_subject_face(face, train_img_path)
                
                BLUEsendlog(0, 'NORMAL_MODE: Known Subject')
                BLUEsendlog(1, 'img'+repr(previous_img_number)+'.jpg')
            
                BLUEsendimg(train_img_path, previous_img_number)
                
                print('Entering NORMAL_MODE: Known Subjet')
                
            
        else:
            
            Mode = 2
            BLUEsendlog(0, 'BLOCKING_MODE: Number max. of alerts surpassed')
            
            
            print('Entering BLOCKING_MODE: Auth_denied, you must have high_level_authorization to release the system to NORMAL_MODE')
        
    elif(Mode == 2):
        
        block_system = 1 #Modo bloqueo


        
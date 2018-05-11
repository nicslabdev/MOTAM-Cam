# **MOTAM-Cam** #

MOTAM-Cam is a part of a complete project you can found at [MOTAM - Gateway](https://github.com/nicslabdev/MOTAM-Gateway), and for its part it makes possible real tracking of subjects and determine if they are or not where they have to, or in other cases if this subject is authorizated to manage the system where MOTAM where implemented; all of that by face recognition and machine learning, involving secure transport layers and visual libraries like Open-CV, Bluedot, Crypto, etc.

# Gateway Server #

The gateway implements a bluetooth serial server that allows any authorizated cam client (but only one cam at time) to pair and connect with it to star a new cicle of recognition, tracking and learning for ever y time the system start or restart.

It is the manager of the important backup files or data and it controls the state of the whole system, determinating wheter it stoping or resuming if it necessary depending of the situation requeriments.

  -*BLE_test.py*: This code is the implementation of the bluetooth server, that **is not** a bluetooth low energy server. It makes posible the data transmision between both Raspberries and make a secure backup of the files that the camera send to it.
  
  -*Throw_out.sh*: This is a bash code that exclude an current client of the pair list of the gateway. Thats disallow  comunications between this interfaces and it is call when a camera that have not authorization to pair with the gateway try to force the pairment. It is not blocking for futures pairements between they, but it prevend transacions of corrupt or forbiden data to the gateway or from it. 
  
# Camera Client #

Camera client generates a bluetooth link between two interfaces (in this case two RaspberriesPi 3B) by a *pairing_process* that idetificates the cam into the gateway and also certificates the transmision by cryptography codes, so this link is a strong serial port by where the transmision protocol implemented too can transfer files or data from the cam to the gateway and by where the gateway can answerthe cam for the transmited packets it received.

In this files there are the implementation of the necesary resources for the recognition, tracking and face-machine learnig and also the states-machine that cominicates with the gateway to keep it informated about all the events that have been produce.

  -*Camera_software.py*: About that file, here it is the sofware that implements the client socket for bluetooth serial, the recognition system and the state-machine, also it calls the pairing_process explained below this lines to make a pairement with the gateway after read a QR code that gives it the necessary information for a secure encrypted pairement.
  
  -*Pairing_process.sh*: A bash code that iniciates the pairement process from the cam to the gateway. He makes the necessary changes into the bluetooth adapter to allows the software make a pairement petition to the gateway which can be accepted or denied by the gateway dependig of the confidence that the cam put into the secure transport layer what is the unique information that the gateway will receive to confirm or not the pairement.

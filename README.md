# **MOTAM-Cam** #

MOTAM-Cam is a part of a complete project you can found at [MOTAM - Gateway](https://github.com/nicslabdev/MOTAM-Gateway), and for its part it makes possible real tracking of subjects and determine if they are or not where they have to, or in other cases if this subject is authorizated to manage the system where MOTAM where implemented; all of that by face recognition and machine learning, involving secure transport layers and visual libraries like Open-CV, Bluedot, Crypto, etc.

# Gateway Server #

The gateway implements a bluetooth serial server that allows any authorizated cam client (but only one cam at time) to pair and connect with it to star a new cicle of recognition, tracking and learning for ever y time the system start or restart.

It is the manager of the important backup files or data and it controls the state of the whole system, determinating wheter it stoping or resuming if it necessary depending of the situation requeriments.


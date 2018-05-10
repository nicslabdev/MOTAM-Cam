#!/bin/bash

echo -e 'power on\n'
sleep 2
echo -e 'discoverable on\n'
sleep 1
echo -e 'pairable on\n'
sleep 1
echo -e 'scan on\n'
sleep 20
echo -e "pair $1\n"
sleep 5
echo -e 'quit\n'
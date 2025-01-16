#!/bin/bash

mkdir -p ~/.ssh

if [ ! -f ~/.ssh/id_rsa ]; then
  # Generate a new SSH key, that the user should copy to the submission host of qsub.
  ssh-keygen -t rsa -N "" -C "PCNportal" -f ~/.ssh/id_rsa
  echo "copy the following content to ~/.ssh/authorized_keys"
  cat ~/.ssh/id_rsa.pub
fi
env > /tmp/env.txt

chmod -R 600 /root/
gunicorn --timeout=1000 --workers=5 --threads=1 -b 0.0.0.0:80 app:server

#!/bin/bash
# Environment variables necessary to run the PCNportal client

# username and host for the PCNportal server
MYUSER=stijdboe@mentat005.dccn.nl

# root directory on the PCNportal server
PROJECTDIR=/project_cephfs/3022051.01

# script directory on the server 
SCRIPTDIR=scripts/server

# model directory
MODELS=models

# script to fetch the directory information on the server
LISTDIR=list_subdirs.py

# script to perform downstream modelling on the server
EXECUTEFILE=execute_modelling.sh

# testing mode (prefix session id with test_session_xxx)
LOCALTESTING=False

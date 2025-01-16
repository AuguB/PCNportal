#!/bin/bash
# Environment variables necessary to run the PCNportal client

# username and host for the PCNportal server
export MYUSER=user@hostname

# root directory on the PCNportal server
export PROJECTDIR=/project_cephfs/3022051.01

# script directory on the server 
export SCRIPTDIR=scripts/server

# model directory
export MODELS=models

# script to fetch the directory information on the server
export LISTDIR=list_subdirs.py

# script to perform downstream modelling on the server
export EXECUTEFILE=execute_modelling.sh

# testing mode (prefix session id with test_session_xxx)
export LOCALTESTING=False

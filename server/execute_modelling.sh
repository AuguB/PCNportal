#! /bin/bash
# @author: Pieter Barkema
# A bash script executed on the server side to start modelling.
#
# Variables:
# 1 = path to the project dir
# 2 = model name
# 3 = data type dir
# 4 = session id
# 5 = model directory
# 6 = user email address

PROJECTDIR=$1
SCRIPTDIR=`dirname $0`

# Activate our virtual environment
cd $PROJECTDIR
module load "anaconda3/2021.05"
source activate ${PROJECTDIR}/pcnptk033

# Start modelling
echo "Bash script activated..."
python ${SCRIPTDIR}/transfer_normative_models_online.py $1 $2 $3 $4 $5 $6


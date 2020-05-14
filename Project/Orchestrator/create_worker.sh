#!/bin/bash
ls -s
echo $1
WORKER="slave$1"
cp  master.db $WORKER.db
ls -s
chmod ugo+rwx $WORKER.db
pwd
python slave.py $1
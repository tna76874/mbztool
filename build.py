#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import secrets
import argparse
sys.setrecursionlimit(5000)

parser = argparse.ArgumentParser()
parser.add_argument("--web", help="build web app", action="store_true")
args = parser.parse_args()

# generate random key
key = str(secrets.token_urlsafe(32))
# optmize level
optimize=1
# version
version="0.2"

if sys.platform == 'win32':
    cmdargs = ["set","PYTHONOPTIMIZE="+str(optimize),'&&']
    delimiter = ';'
else:
    cmdargs = ["PYTHONOPTIMIZE="+str(optimize)]
    delimiter = ':'

cmdargs = cmdargs + [ 
                    "pyinstaller", 
                    "--key="+key,
                    '-F',
                    '--clean',
                    '--hidden-import cmath',
                    ]

if args.web:
    name="mbztool"
    webargs = cmdargs + [
                        '-n',name+'_'+version,
                        '--add-data=\"web'+delimiter+'./web\"',
                        'app.py',
                        ]
    os.system(" ".join(webargs))
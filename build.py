#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import secrets
import argparse
import git
sys.setrecursionlimit(5000)

parser = argparse.ArgumentParser()
parser.add_argument("--web", help="build web app", action="store_true")
parser.add_argument("-v", help="generate version file", action="store_true")
args = parser.parse_args()

# generate random key
key = str(secrets.token_urlsafe(32))
# optmize level
optimize=1
# version
version="0.3"

def generate_version():
    local_repo = git.Repo(".")
    COMMIT=list(local_repo.iter_commits("master"))[0]

    VERSION =   [
                COMMIT.hexsha,
                COMMIT.committed_datetime.strftime("%Y-%m-%d"),
                ]

    with open('VERSION', mode='wt', encoding='utf-8') as f:
        f.write("\n".join(VERSION))

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
    generate_version()
    name="mbztool"
    webargs = cmdargs + [
                        '-n',name+'_'+version,
                        '--add-data=\"web'+delimiter+'./web\"',
                        '--add-data=\"VERSION'+delimiter+'.\"',
                        'app.py',
                        ]
    os.system(" ".join(webargs))

if args.v:
    generate_version()
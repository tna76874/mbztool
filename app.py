#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask webserver to extract the files of a moodle backup (mbz)
* The mbz-file gets uploaded to the upload folder
* After an upload, the file gets converted to a zip-File using mbzbot.py. After the conversion
  (successful or not) the uploaded file gets deleted immediately
* The zip-file gets streamed into memory gets deleted afterwards immediately
* The converted file gets streamed from memory to download.
"""

__author__ = "tna76874"
__credits__ = ["", "", ""]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "tna76874"
__email__ = "dev@hilberg.eu"
__status__ = "Prototype"

###########################################################################
##                                                                       ##
# Moodle .mbz Extract Utility Flask Frontend
##                                                                       ##
# python 3
##                                                                       ##
###########################################################################
##                                                                       ##
## NOTICE OF COPYRIGHT                                                   ##
##                                                                       ##
## This program is free software; you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation; either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details:                          ##
##                                                                       ##
##          http:##www.gnu.org/copyleft/gpl.html                         ##
##                                                                       ##
###########################################################################

import os
import io
import sys
from flask import *  
from werkzeug.utils import secure_filename
from mbzbot import mbzbot

# Read env vars
## root folder
if hasattr(sys, '_MEIPASS'):
    ROOT_DIR = os.path.abspath(sys._MEIPASS)
    print('ENTERING FROZEN MODE. TEMP DIR: {:}'.format(ROOT_DIR))
    TEMPLATES = ROOT_DIR + '/'
else:
    ROOT_DIR = os.getcwd()
    TEMPLATES = ''

## upload limit
if hasattr(sys, 'UPLOAD_LIMIT_GB'):
    UPLOAD_LIMIT_GB = int(float(os.path.abspath(sys.UPLOAD_LIMIT_GB))* 1024 * 1024 * 1024)
elif os.getenv("UPLOAD_LIMIT_GB") != None:
    UPLOAD_LIMIT_GB = int(float(os.getenv("UPLOAD_LIMIT_GB")) * 1024 * 1024 * 1024)
elif hasattr(sys, '_MEIPASS'):
    UPLOAD_LIMIT_GB = 5 * 1024 * 1024 * 1024 # 5GB
else:
    UPLOAD_LIMIT_GB = 5 * 1024 * 1024 * 1024 # 5GB

## allow converting
if hasattr(sys, '_MEIPASS') | (os.getenv("ALLOW_COMPRESSION")=="yes"):
    allow_convert = True
else:
    allow_convert = False

# define some functions
def read_version():
    with open(os.path.join(ROOT_DIR,'VERSION')) as f:
        lines = [line.rstrip() for line in f]
    return lines

def allowed_types(filename):
    """
    function to check for allowed filetypes
    """
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[-1]

    if ext.upper() in app.config["ALLOWED_EXTENSIONS"]:
        return True
    else:
        return False

# Initialize Flask app
app = Flask(__name__,
            static_url_path='', 
            static_folder="{:}web/static".format(TEMPLATES),
            template_folder="{:}web/templates".format(TEMPLATES))

app.config['UPLOAD_FOLDER'] = os.path.abspath(ROOT_DIR+"/uploads")
app.config['DOWNLOAD_FOLDER'] = os.path.abspath(ROOT_DIR+"/downloads")
app.config['MAX_CONTENT_LENGTH'] = UPLOAD_LIMIT_GB
app.config["ALLOWED_EXTENSIONS"] = ["MBZ"]
app.config["SOURCE"] = "https://github.com/tna76874/mbztool"
app.config["VERSION"] = read_version()
app.config["SOURCE_URL_DESCRIPTION"] = "git-{}-{}".format(app.config["VERSION"][1],app.config["VERSION"][0][:4])

# create mandatory folders, of not exist
for i in ['UPLOAD_FOLDER','DOWNLOAD_FOLDER']:
    if not os.path.exists(app.config[i]):
        os.makedirs(app.config[i])

# routings
@app.route('/')  
def upload():
    """
    return 'index.html' when access '/'
    """
    return render_template("index.html",
                            SOURCE_URL=app.config["SOURCE"],
                            SOURCE_URL_DESCRIPTION=app.config["SOURCE_URL_DESCRIPTION"],
                            THIS_COMMIT=app.config["VERSION"][0])

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/static/<path:path>')
def serve_static(path):
    return app.send_static_file(os.path.join(path))
 
@app.route('/upload', methods = ['POST'])  
def success():
    """
    define upload function. Redirect to '/' if upload not allowed filetype.
    convert uploaded mbz file with mbzbot
    """
    if request.method == 'POST':  
        f = request.files['file']
        filename = secure_filename(f.filename)

        if (request.form.get('compress')=='yes') & allow_convert:
            compress = True
        else:
            compress = False

        if allowed_types(filename):
            savepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            convertpath = os.path.splitext(os.path.basename(savepath))[0]+'.zip'
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            try:
                mbzbot({'file':savepath,'zipdir':app.config['DOWNLOAD_FOLDER'], 'rootdir': ROOT_DIR, 'compress': compress, })
                os.remove(savepath)
            except:
                os.remove(savepath)
                return redirect('/')
            return redirect('/downloads/'+ convertpath)
        else:
            return redirect('/')

@app.route('/downloads/<path:filename>')
def download_file(filename):
    """
    Download converted zip file. For security reasons, first stream the file into memory, delete it from download-folder
    and serve it for download directely from memory.
    """
    file_path = os.path.abspath(app.config['DOWNLOAD_FOLDER']+'/'+filename)

    return_data = io.BytesIO()
    with open(file_path, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)

    os.remove(file_path)

    return send_file(return_data, mimetype='application/zip',
                     attachment_filename=filename)

    
  
if __name__ == '__main__':
    import webbrowser, threading
    import time
    URL = "http://localhost:5000"
    threading.Timer(1, lambda: webbrowser.open(URL, new = 2) ).start()
    app.run(debug = False, host='localhost')
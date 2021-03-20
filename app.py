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
from flask import *  
from werkzeug.utils import secure_filename
from mbzbot import mbzbot

# Initialize Flask app
app = Flask(__name__,
            static_url_path='', 
            static_folder='web/static',
            template_folder='web/templates')  

app.config['UPLOAD_FOLDER'] = os.path.abspath(os.getcwd()+"/uploads")
app.config['DOWNLOAD_FOLDER'] = os.path.abspath(os.getcwd()+"/downloads")
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024 # 2GB Limit
app.config["ALLOWED_EXTENSIONS"] = ["MBZ"]

# create mandatory folders, of not exist
for i in ['UPLOAD_FOLDER','DOWNLOAD_FOLDER']:
    if not os.path.exists(app.config[i]):
        os.makedirs(app.config[i])

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

@app.route('/')  
def upload():
    """
    return 'index.html' when access '/'
    """
    return render_template("index.html")

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
        if allowed_types(filename):
            savepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            convertpath = os.path.splitext(os.path.basename(savepath))[0]+'.zip'
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            try:
                mbzbot({'file':savepath,'zipdir':app.config['DOWNLOAD_FOLDER']})
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
    # Run Flask-app and bind the web-server to 0.0.0.0
    app.run(debug = True,host='0.0.0.0')  

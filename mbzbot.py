#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MBZ moodle converter
"""

__author__ = "tna76874"
__credits__ = ["https://github.com/Swarthmore/extract-mbz"]
__license__ = "GPL"
__version__ = "0.3"
__maintainer__ = "tna76874"
__email__ = "dev@hilberg.eu"
__status__ = "Prototype"

###########################################################################
##                                                                       ##
# Moodle .mbz Extract Utility
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

import pandas as pd
import pandas_read_xml as pdx
import glob2
import os
import numpy as np
import shutil
import zipfile
import tarfile
from PIL import Image
from queue import Queue
import threading, multiprocessing

class ConvertWorker(threading.Thread):
    def __init__(self, queue, maxlen = 1500, quality = 75, optimize = True):
        threading.Thread.__init__(self)
        self.queue = queue
        self.maxlen = maxlen
        self.quality = 75
        self.optimize = True

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            convertfile = self.queue.get()
            try:
                self.process_data(convertfile)
            finally:
                self.queue.task_done()

    def process_data(self,i):
        picture = Image.open(i)
        size = picture.size
        factor = self.maxlen / np.max(picture.size)
        resize = tuple((int(k*factor) for k in size))
        try:
            picture.resize(resize).save(i, optimize = self.optimize, quality = self.quality)
        except: print("Error")


class mbzbot:
    """
    converting .mbz moodle backup files to a human readable zip file
    """
    def __init__(self,config=None):
        """
        insert config dictionary:
        config =    {
                    'file'      : 'example.mbz',            # mbz-file to convert
                    'zipdir'    : './myspecialdirectory',   # optional: a directory the zip file is exported
                    }
        """
        self.rootdir = os.getcwd()
        self.extractroot = os.path.abspath(self.rootdir + '/extract')
        self.extractdir = None
        self.exportroot = os.path.abspath(self.rootdir + '/export')
        self.exportdir = None
        self.zipdir = None
        self.compress = False
        
        if config!=None:
            if 'zipdir' in config.keys():
                self.zipdir = os.path.abspath(config['zipdir'])
            if 'rootdir' in config.keys():
                self.rootdir = os.path.abspath(config["rootdir"])
                self.extractroot = os.path.abspath(self.rootdir + '/extract')
                self.exportroot = os.path.abspath(self.rootdir + '/export')
            if 'compress' in config.keys():
                self.compress = config["compress"]
            # run mbzbot
            self.extractmbz(os.path.splitext(os.path.abspath(config['file']))[0]+'.mbz')
        else:
            self.parser = argparse.ArgumentParser()
            self.parser.add_argument("-f", help="mbz file to extract", required=False)
            self.parser.add_argument("-c", help="compress images after extraction", action="store_true")
            self.parser.add_argument("-a", help="convert all mbz files in current directory", action="store_true")
            self.args = self.parser.parse_args()
            
            self.compress = self.args.c
            
            if self.args.a:
                mbzlist = glob2.glob(self.rootdir+"/*.mbz")
                for i in mbzlist:
                    self.extractmbz(os.path.abspath(i))
            elif (not self.args.a) & (self.args.f != None):
                self.extractmbz(self.args.f)

    def unzip(self,mbz_filepath,destination):
        """
        unzip a file to a certain destination
        """
        # mbz dict contains information about the mbz file
        mbz = dict()

        if not os.path.exists(destination):
            os.makedirs(destination)

        # Older version of mbz files are zip files
        # Newer versions are gzip tar files
        # Figure out what file type we have and access appropriately

        if zipfile.is_zipfile(mbz_filepath):
            mbz['type'] = 'zip'
            mbz['content'] = zipfile.ZipFile(mbz_filepath, 'r')
            mbz['filelist'] = mbz['content'].namelist()

        elif tarfile.is_tarfile(mbz_filepath):
            mbz['type'] = 'tar'
            mbz['content'] = tarfile.open(mbz_filepath)
            mbz['filelist'] = mbz['content'].getnames()

        else:
            print("Can't figure out what type of archive file this is")
            return -1
        mbz['content'].extractall(destination)
        
    def compress_files(self,COMPRESSDIR, optimize = True, quality = 75, maxlen = 1500):
        """
        Compress files under given path
        """
        compressdir = os.path.abspath(str(COMPRESSDIR))
        files = []
        for ext in ('png', 'jpg','JPG','PNG'):
           files.extend(glob2.glob(compressdir+"/**/*.{:}".format(ext)))

        # initialize Queue
        queue = Queue()

        # initialize workers
        for x in range(multiprocessing.cpu_count()-1):
            worker = ConvertWorker(queue,maxlen = maxlen, quality = quality, optimize = optimize)
            worker.daemon = True
            worker.start()

        # fill up queue
        for file in files:
            queue.put(file)
        queue.join()

    def extractmbz(self,zfile):
        """
        extract files to human readable format from moodle backup files
        """
        self.extractdir=os.path.join(self.extractroot,os.path.basename(zfile))
        self.exportdir=os.path.join(self.exportroot,os.path.basename(zfile))

        # ensure clean working directories
        for i in [self.extractdir, self.exportdir]:
            if os.path.exists(i): shutil.rmtree(i)
            os.makedirs(i)
        
        # unzip mbz file
        self.unzip(zfile,self.extractdir)

        # define savepath for zip file
        if self.zipdir==None: self.zipdir = os.path.dirname(os.path.abspath(zfile))

        ## Parse data from xml-files
        DF_files = pdx.read_xml(os.path.abspath(self.extractdir + "/files.xml"), ['files','file'])
        DF_files = DF_files[DF_files['mimetype']!='$@NULL@$']
        
        DF_user = pdx.read_xml(os.path.abspath(self.extractdir + "/users.xml"), ['users','user']).rename(columns = {'@contextid':'contextid','@id':'id_user'})
        DF_user = DF_user[[
                            'id_user',
                            'username',
                            'email',
                            'firstname',
                            'lastname'
                            ]]

        DF_things = pd.DataFrame({'path':glob2.glob(self.extractdir+"/**/*")})

        DF_things.loc[:,'path'] = DF_things.loc[:,'path'].apply(lambda x: os.path.abspath(x))
        DF_things.loc[:,'filen'] = DF_things.loc[:,'path'].apply(lambda x: os.path.basename(x))

        # item: recources
        DF_resource = pd.DataFrame()
        for i in DF_things[DF_things['filen']=='resource.xml']['path']:
            DF_tmp = pdx.read_xml(i).T.rename(columns = {'@contextid':'contextid','@id':'id_resource'})
            DF_tmp = pd.concat([DF_tmp.reset_index(drop=True),pd.DataFrame.from_dict(dict(DF_tmp['resource']['activity']),orient='index').T.reset_index(drop=True)],axis=1,sort=False)
            DF_tmp.drop(columns=['resource','@id','timemodified'],inplace=True)
            DF_resource = pd.concat([DF_resource,DF_tmp])

        # item: grades
        DF_grade = pd.DataFrame()
        for i in DF_things[DF_things['filen']=='grades.xml']['path']:
            try:
                DF_tmp = pdx.read_xml(i,['activity_gradebook','grade_items']).T.rename(columns = {'@contextid':'contextid','@id':'id_assignment'}).reset_index(drop=True)
                # DF_tmp = pd.concat([DF_tmp.reset_index(drop=True),pd.DataFrame.from_dict(dict(DF_tmp['assign']['activity']),orient='index').T.reset_index(drop=True)],axis=1,sort=False)
                # DF_tmp.drop(columns=['assign','@id','timemodified'],inplace=True)
                DF_grade = pd.concat([DF_grade,DF_tmp])
            except: pass
        DF_grade.reset_index(drop=True,inplace=True)
        DF_grades = pd.DataFrame()
        DF_grades['id_assignment'] = np.nan
        for i in DF_grade.index:
            try:
                DF_tmp = pd.DataFrame.from_dict(DF_grade.loc[i,'grade_grades']['grade_grade']).reset_index(drop=True).rename(columns = {'@contextid':'contextid','@id':'id_grades'})
                DF_tmp['id_assignment'] = DF_grade.loc[i,'id_assignment']
                DF_grades = pd.concat([DF_grades,DF_tmp])
            except: pass
        if len(DF_grades) > 0:
            DF_grades.reset_index(drop=True,inplace=True)
            DF_grades = pd.merge(DF_grade,DF_grades, on="id_assignment")
            DF_grades = pd.merge(DF_grades,DF_user,left_on="userid",right_on="id_user")
            DF_grades = DF_grades[['itemname','username', 'email', 'firstname', 'lastname', 'rawgrade', 'finalgrade','feedback','userid']]
            DF_grades.replace("$@NULL@$",'---',inplace=True)

        # item: assignments
        DF_assign = pd.DataFrame()
        for i in DF_things[DF_things['filen']=='assign.xml']['path']:
            DF_tmp = pdx.read_xml(i).T.rename(columns = {'@contextid':'contextid','@id':'id_assignment'})
            DF_tmp = pd.concat([DF_tmp.reset_index(drop=True),pd.DataFrame.from_dict(dict(DF_tmp['assign']['activity']),orient='index').T.reset_index(drop=True)],axis=1,sort=False)
            DF_tmp.drop(columns=['assign','@id','timemodified'],inplace=True)
            DF_assign = pd.concat([DF_assign,DF_tmp])
       
        # merge item informations
        DF_items = pd.concat([DF_assign,DF_resource])
        DF_files = pd.merge(DF_files,DF_items,on="contextid")
        DF_files = pd.merge(DF_files,DF_things,left_on="contenthash",right_on="filen",how="outer")
        DF_files = DF_files[['userid',
                              '@id',
                              'filearea',
                              'contextid',
                              'filen',
                              'contenthash',
                              'name',
                              'path',
                              '@moduleid',
                              'id_assignment',
                              'filename',
                              'component',
                              'filepath']]
        
        # Dataframes to work with
        DF_feedback = DF_files[DF_files['filearea']=='download'].rename(columns = {'@contextid':'contextid','@id':'id_feedback'})
        DF_files = pd.merge(DF_files,DF_user,left_on="userid",right_on="id_user")
        DF_assign = DF_files[DF_files['component'].str.contains('assign')].rename(columns = {'@contextid':'contextid','@id':'id_assign'})
        
        
        ## Converting files
        # convert course files
        for i in DF_things[DF_things['filen']=='section.xml']['path']:
            DF_resource = pdx.read_xml(i).T.reset_index(drop=True)
            try:
                DF_filescopy = DF_files[DF_files['@moduleid'].isin(DF_resource['sequence'].str.split(',')[0])]
                DF_filescopy = DF_filescopy[~DF_filescopy['component'].str.contains('assign')]
                foldername = "%.2d"%DF_resource['number']+'_'+DF_resource['name'][0].replace(' ','_')
                folderpath = os.path.join(os.path.abspath(self.exportdir), 'course' , foldername)
                if not os.path.exists(folderpath):
                    os.makedirs(folderpath)
                for j in DF_filescopy.index:
                    shutil.copy(DF_filescopy.loc[j,'path'],folderpath)
                    shutil.move(os.path.abspath(folderpath+'/'+DF_filescopy.loc[j,'filen']),os.path.abspath(folderpath+'/'+DF_filescopy.loc[j,'filen'][:4] + '_' + DF_filescopy.loc[j,'filename']))
            except: pass
        
        # convert assignment files
        for i in DF_assign.index:
            try:
                name = DF_assign.loc[i,'lastname'].replace(' ','_')+'_'+DF_assign.loc[i,'firstname']
                assignment = DF_assign.loc[i,'name']
                hashval = DF_assign.loc[i,'contenthash'][:5]
                folderpath = os.path.join(os.path.abspath(self.exportdir), 'assign' , assignment, name)
                if not os.path.exists(folderpath):
                    os.makedirs(folderpath)
                shutil.copy(DF_assign.loc[i,'path'],folderpath)
                shutil.move(os.path.abspath(folderpath+'/'+DF_assign.loc[i,'filen']),os.path.abspath(folderpath+'/'+hashval+'_'+DF_assign.loc[i,'filename']))
            except: pass
        
        # convert feedbacks
        for i in DF_feedback.index:
            try:
                name = DF_feedback.loc[i,'filename'].split(".")[0]
                assignment = DF_feedback.loc[i,'name']
                hashval = DF_feedback.loc[i,'contenthash'][:5]
                folderpath = os.path.join(os.path.abspath(self.exportdir), 'feedback' , assignment, name)
                if not os.path.exists(folderpath):
                    os.makedirs(folderpath)
                shutil.copy(DF_feedback.loc[i,'path'],folderpath)
                shutil.move(os.path.abspath(folderpath+'/'+DF_feedback.loc[i,'filen']),os.path.abspath(folderpath+'/'+hashval+'_'+DF_feedback.loc[i,'filename']))
            except: pass
        
        # convert gradings
        for i in DF_grades.index:
            try:
                name = DF_grades.loc[i,'lastname'].replace(' ','_')+'_'+DF_grades.loc[i,'firstname']
                assignment = DF_grades.loc[i,'itemname']
                folderpath = os.path.join(os.path.abspath(self.exportdir), 'assign' , assignment, name)
                if not os.path.exists(folderpath):
                    os.makedirs(folderpath)
                with open(os.path.join(folderpath,'rating.html'), mode='wt', encoding='utf-8') as f:
                    f.write("{:}\n\nRating:{:}".format(DF_grades.loc[i,'feedback'],DF_grades.loc[i,'finalgrade']))
            except: pass
            
        # delete the extracted mbz files
        shutil.rmtree(self.extractdir)
        # compress images, if selected
        if self.compress: self.compress_files(self.exportdir)
        # zip all extracted files into one file
        shutil.make_archive(os.path.abspath(self.zipdir + '/' + os.path.splitext(os.path.basename(zfile))[0]), 'zip', self.exportdir)
        # delete the extracted files and have only the zip file left
        shutil.rmtree(self.exportdir)

if __name__ == "__main__":
    # if runn locally, import argparse and use mbzbot as an command-line tool
    import argparse
    bot = mbzbot()
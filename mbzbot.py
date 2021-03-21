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
        if config!=None:
            if 'zipdir' in config.keys():
                self.zipdir = os.path.abspath(config['zipdir'])
            if 'rootdir' in config.keys():
                self.rootdir = os.path.abspath(config["rootdir"])
            self.extractmbz(os.path.splitext(os.path.abspath(config['file']))[0]+'.mbz')
        else:
            self.parser = argparse.ArgumentParser()
            self.parser.add_argument("-f", help="mbz file to extract", required=False)
            self.parser.add_argument("-a", help="convert all mbz files in current directory", action="store_true")   
            self.args = self.parser.parse_args()
            
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

        # extracting data
        DF_files = pdx.read_xml(os.path.abspath(self.extractdir + "/files.xml"), ['files','file'])
        DF_files = DF_files[DF_files['mimetype']!='$@NULL@$']
        
        DF_user = pdx.read_xml(os.path.abspath(self.extractdir + "/users.xml"), ['users','user']).rename(columns = {'@contextid':'contextid','@id':'id2'})
        DF_user = DF_user[[
                            'id2',
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
            DF_tmp = pdx.read_xml(i).T.rename(columns = {'@contextid':'contextid','@id':'id2'})
            DF_tmp = pd.concat([DF_tmp.reset_index(drop=True),pd.DataFrame.from_dict(dict(DF_tmp['resource']['activity']),orient='index').T.reset_index(drop=True)],axis=1,sort=False)
            DF_tmp.drop(columns=['resource','@id','timemodified'],inplace=True)
            DF_resource = pd.concat([DF_resource,DF_tmp])
            
        # item: assignments
        DF_assign = pd.DataFrame()
        for i in DF_things[DF_things['filen']=='assign.xml']['path']:
            DF_tmp = pdx.read_xml(i).T.rename(columns = {'@contextid':'contextid','@id':'id2'})
            DF_tmp = pd.concat([DF_tmp.reset_index(drop=True),pd.DataFrame.from_dict(dict(DF_tmp['assign']['activity']),orient='index').T.reset_index(drop=True)],axis=1,sort=False)
            DF_tmp.drop(columns=['assign','@id','timemodified'],inplace=True)
            DF_assign = pd.concat([DF_assign,DF_tmp])
       
        # merge item informations
        DF_items = pd.concat([DF_assign,DF_resource])
        DF_files = pd.merge(DF_files,DF_items,on="contextid")
        DF_files = pd.merge(DF_files,DF_things,left_on="contenthash",right_on="filen",how="outer")
        
        # Dataframes to work with
        DF_feedback = DF_files[DF_files['filearea']=='download'].rename(columns = {'@contextid':'contextid','@id':'id1'})
        DF_files = pd.merge(DF_files,DF_user,left_on="userid",right_on="id2")
        DF_assign = DF_files[DF_files['component'].str.contains('assign')]
        
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
            
        # delete the extracted mbz files
        shutil.rmtree(self.extractdir)
        # zip all extracted files into one file
        shutil.make_archive(os.path.abspath(self.zipdir + '/' + os.path.splitext(os.path.basename(zfile))[0]), 'zip', self.exportdir)
        # delete the extracted files and have only the zip file left
        shutil.rmtree(self.exportdir)

if __name__ == "__main__":
    # if runn locally, import argparse and use mbzbot as an command-line tool
    import argparse
    bot = mbzbot()
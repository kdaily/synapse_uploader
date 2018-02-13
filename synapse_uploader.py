#!/usr/bin/python

# Copyright 2017-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, os, argparse
import synapseclient
from synapseclient import Project, Folder, File

class SynapseUploader:


    def __init__(self, synapse_project, local_path, remote_path=None, dry_run=False):
        self._dry_run = dry_run
        self._synapse_project = synapse_project
        self._local_path = local_path.rstrip(os.sep)
        self._remote_path = None
        self._synapse_folders = {}
        
        if remote_path != None and len(remote_path.strip()) > 0:
            self._remote_path = remote_path.strip().lstrip(os.sep).rstrip(os.sep)
            if len(self._remote_path) == 0:
                self._remote_path = None

    def start(self):
        if self._dry_run:
            print('~~ Dry Run ~~')
        print('Uploading to Project: {0}'.format(self._synapse_project))
        print('Uploading Directory: {0}'.format(self._local_path))

        if self._remote_path != None:
            print('Uploading To: {0}'.format(self._remote_path))

        self.login()

        project = self._synapse_client.get(Project(id = self._synapse_project))
        self.set_synapse_folder(self._synapse_project, project)

        # Create the remote_path if specified.
        if self._remote_path != None:
            full_path = ''
            for folder in filter(None, self._remote_path.split(os.sep)):
                full_path = os.path.join(full_path, folder)
                self.create_directory_in_synapse(full_path, virtual_path=True)

        # Create the folders and upload the files.
        for dirpath, dirnames, filenames in os.walk(self._local_path):
            
            if dirpath != self._local_path:
                self.create_directory_in_synapse(dirpath)

            for filename in filenames:
                full_file_name = os.path.join(dirpath, filename)
                self.upload_file_to_synapse(full_file_name)

        if self._dry_run:
            print('Dry Run Completed Successfully.')
        else:
            print('Upload Completed Successfully.')



    def get_synapse_folder(self, synapse_path):
        return self._synapse_folders[synapse_path]



    def set_synapse_folder(self, synapse_path, parent):
        self._synapse_folders[synapse_path] = parent



    def login(self):
        print('Logging into Synapse...')
        syn_user = os.environ['SYNAPSE_USER']
        syn_pass = os.environ['SYNAPSE_PASSWORD']
        
        self._synapse_client = synapseclient.Synapse()
        self._synapse_client.login(syn_user, syn_pass, silent=True)



    def get_synapse_path(self, local_path, virtual_path=False):
        if virtual_path:
            return os.path.join(self._synapse_project, local_path)
        else:
            return os.path.join(self._synapse_project
                                ,(self._remote_path if self._remote_path else '')
                                ,local_path.replace(self._local_path + os.sep, '')
                                )



    def create_directory_in_synapse(self, path, virtual_path=False):
        print('Processing Folder: {0}'.format(path))
        
        full_synapse_path = self.get_synapse_path(path, virtual_path)
        synapse_parent_path = os.path.dirname(full_synapse_path)
        synapse_parent = self.get_synapse_folder(synapse_parent_path)
        folder_name = os.path.basename(full_synapse_path)

        print('  -> {0}'.format(full_synapse_path))

        synapse_folder = Folder(folder_name, parent=synapse_parent)

        if self._dry_run:
            # Give the folder a fake id so it doesn't blow when this folder is used as a parent.
            synapse_folder.id = 'syn0'
        else:
            synapse_folder = self._synapse_client.store(synapse_folder, forceVersion=False)
            
    
        self.set_synapse_folder(full_synapse_path, synapse_folder)



    def upload_file_to_synapse(self, local_file):
        print('Processing File: {0}'.format(local_file))

        full_synapse_path = self.get_synapse_path(local_file)
        synapse_parent_path = os.path.dirname(full_synapse_path)
        synapse_parent = self.get_synapse_folder(synapse_parent_path)
        
        print('  -> {0}'.format(full_synapse_path))

        if not self._dry_run:
            self._synapse_client.store(File(local_file, parent=synapse_parent), forceVersion=False)



def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('project_id', metavar='project-id', help='Synapse Project ID to upload to (e.g., syn123456789).')
    parser.add_argument('local_folder_path', metavar='local-folder-path', help='Path of the folder to upload.')
    parser.add_argument('-r', '--remote-folder-path', help='Folder to upload to in Synapse.', default=None)
    parser.add_argument('-d', '--dry-run', help='Dry run only. Do not upload any folders or files.', default=False, action='store_true')
    args = parser.parse_args()
    
    SynapseUploader(
        args.project_id
        ,args.local_folder_path
        ,remote_path=args.remote_folder_path
        ,dry_run=args.dry_run
        ).start()



if __name__ == "__main__":
    main(sys.argv[1:])

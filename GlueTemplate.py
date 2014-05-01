#!/usr/bin/env python
# encoding: utf-8

from GlueInk import Template, Renderer
from GlueIO import FileReader, FileWriter

import os

class TemplateCommander(object):
    def __init__(self, template_name="", outfile_name="", current_directory="", templates_directory=""):
        self.template_name = template_name  # the name of the template to check for in Glue-Templates directory
        self.outfile_name = outfile_name # the file name (to be concatenated to the CWD path)
        self.current_directory = current_directory # current working directory
        self.templates_directory = templates_directory # the absolute path to the Glue-Templates directory
        self.response_code = -1
        self.response_message = "" # response message for the calling code, set based upon result of the logic in this module

    def run(self):
        # initial logic, distinguish remote from local file request
        if self.template_name.startswith('http://') or self.template_name.startswith('https://'):
            local_key_path = "" # the path to the template key or empty string if not present (the key is optional)
            test_key_path = os.path.join(self.current_directory, 'key.glue') # the location to search for the template key (the key is optional)
            if self._path_exists(test_key_path):
                local_key_path = test_key_path # assign the test path to the local key path if it is present, otherwise remains empty string
            # instantiate a RemoteTemplate to pull the text and perform the replacement
            remote_template = RemoteTemplate(self.template_name, local_key_path)
            remote_template.pull_file()
            remote_template.perform_replacement()

        else:
            pass # LOCAL FILES


        if self.template_name.endswith('.glue-template'): # user can be explicit about whether it is a .glue-template or .glue-paths file (if same file name)
            template_test_path = os.path.join(self.templates_directory, self.template_name)
            key_test_path = os.path.join(self.current_directory, 'key.glue')
            if self._path_exists(template_test_path):
                template_text_raw = self._get_local_template(template_test_path) # get the template text
                if self._path_exists(key_test_path): # does user have a key.glue file in the current directory for template tag replacements?
                    template_text_final = self._perform_text_replacements(template_text_raw) # perform template tag replacements as specified in the file
                else:
                    template_text_final = template_text_raw # otherwise use the raw string for the file write

                # write the file to disk
                if len(self.outfile_name) > 0:
                    outfile_path = os.path.join(self.current_directory, self.outfile_name)
                    ## TODO: write the file to this filepath, ? automatically open file in a new view
                else:
                    ## TODO: pass info back to calling code with response code indicator and response_message text to be handled in main script
                    pass # instead of writing without proper name, open in the editor and allow user to save
                self._write_template(template_text_final)


            else:
                # user entered a template path that does not exist, set response code and message for calling code and return
                self.response_code = 1
                self.response_message = "The requested template '" + self.template_name + "' could not be found.  Please confirm that it is in your Glue-Templates directory.\n"
                return 1 # abort
        elif self.template.endswith('.glue-paths'):
            template_test_path = os.path.join(self.templates_directory, self.template_name)
            if self._path_exists(template_test_path):
                template = self.template_name # assign the existing template path to the `template` variable
            else:
                # user entered a template path that does not exist, set response code and message for calling code and return
                self.response_code = 1
                self.response_message = "The requested template '" + self.template_name + "' could not be found.  Please confirm that it is in your Glue-Templates directory.\n"
                return 1 # abort
        else: # user was not explicit about which one they are using, so let's test for it
            glue_template_name = self.template_name + '.glue-template'
            glue_paths_name = self.template_name + '.glue-paths'
            template_test_path = os.path.join(self.templates_directory, glue_template_name)
            paths_test_path = os.path.join(self.templates_directory, (self.template_name + '.glue-paths'))

            # tests for existence of requested file
            if self._path_exists(template_test_path):
                template = template_test_path
            elif self._path_exists(paths_test_path):
                template = template_test_path
            else:
                self.response_code = 1
                self.response_message = "There is no " + glue_template_name + " or " + glue_paths_name + " file in your Glue-Templates directory. Please add the file to the directory or request a different template file.\n"
                return 1 # abort


    #------------------------------------------------------------------------------
    # [ _path_exists method ] - test for existence of a file on the `file_path` argument
    #------------------------------------------------------------------------------
    def _path_exists(self, file_path):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return True
        else:
            return False


class LocalTemplate(object):
    def __init__(self, local_template_path="", local_key_path=""):
        self.local_template_path = local_template_path
        self.local_key_path = local_key_path
        self.template_text = "" # attribute that holds the final template text


class RemoteTemplate(object):
    def __init__(self, remote_template_url="", local_key_path=""):
        self.remote_template_url = remote_template_url
        self.local_key_path = local_key_path
        self.template_text = "" # attribute that holds the final template text

    ## TODO determine .glue-template vs glue-paths, then handle accordingly

    def pull_file(self):
        pass

    def perform_replacement(self):
        pass





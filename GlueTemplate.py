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
        # the execution depends upon whether a .glue-template or .glue-paths file is being used
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


    def _get_local_template(self, template_path):
        pass

    def _get_remote_template(self):
        pass

    def _perform_text_replacements(self, template_text):
        pass

    def _write_template(self, template_text, outfile_path):
        pass

    #------------------------------------------------------------------------------
    # [ _path_exists method ] - test for existence of a file on the `file_path` argument
    #------------------------------------------------------------------------------
    def _path_exists(self, file_path):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return True
        else:
            return False

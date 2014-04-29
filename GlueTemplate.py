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
        self.response_message = ""

    def run(self):
        # create test file paths (either a .glue-template or .glue-paths file)
        template = "" # the template file that will be used after the following tests
        if self.template_name.endswith('.glue-template'): # user can be explicit about whether it is a .glue-template or .glue-paths file (if same file name)
            template_test_path = os.path.join(self.templates_directory, self.template_name)
            if self._path_exists(template_test_path):
                template = self.template_name # assign the existing template path to the `template` variable
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

        #

    def _get_local_template(self):
        pass

    def _get_remote_template(self):
        pass

    def _write_template(self):
        pass

    def _path_exists(self, file_path):
        pass

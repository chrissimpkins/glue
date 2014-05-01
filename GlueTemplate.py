#!/usr/bin/env python
# encoding: utf-8

from GlueInk import Template, Renderer
from GlueIO import FileReader, FileWriter

import os

try:
    # Python 3
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from urllib2 import urlopen

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
            remote_template = RemoteTemplate(self.template_name, local_key_path) # template_name will be a URL for remote requests
            remote_template.pull_file()
            remote_template.perform_replacement()
            if len(remote_template.template_text) > 0:
                pass # write to disk
            else:
                pass # pass error message to user (no text was returned)

        else:
            pass # LOCAL FILES


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

    def read_file(self):
        pass

    def perform_replacement(self):
        pass

    def get_final_template(self):
        pass


class RemoteTemplate(object):
    def __init__(self, remote_template_url="", local_key_path=""):
        self.remote_template_url = remote_template_url
        self.local_key_path = local_key_path
        self.local_key_exists = (len(self.local_key_path) > 0) # if set then it exists (tested in code prior to instantiation of RemoteTemplate)
        self.template_text = "" # defined with the text of the template in pull_file method
        self.write_text = "" # defined with the final write text in the perform_replacement method

    ## TODO determine .glue-template vs glue-paths, then handle accordingly

    def pull_file(self):
        the_text = urlopen(self.remote_template_url).read().decode('utf-8')
        if len(the_text) > 0:
            self.template_text = the_text

    def perform_replacement(self):
        pass

    def get_final_template(self):
        pass # return the template text to the calling code


if __name__ == '__main__':
    tc = TemplateCommander('https://raw.githubusercontent.com/chrissimpkins/glue/master/LICENSE', 'LICENSE', '/Users/ces/Desktop/test', '/Users/ces/Library/Application\ Support/Sublime\ Text\ 3/Packages/Glue-Templates')
    tc.run()




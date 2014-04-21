#!/usr/bin/env python
# encoding: utf-8

import sublime
import sublime_plugin
import os
from glob import glob

#------------------------------------------------------------------------------
# [ GlueFileOpenerCommand class ] - executed from glue open command
#------------------------------------------------------------------------------
class GlueFileOpenerCommand(sublime_plugin.WindowCommand):
    def run(self, paths=[], current_dir="", file_list=[]):
        if len(file_list) > 1:
            for the_file in file_list:
                abs_filepath = os.path.join(current_dir, the_file)
                self.file_opener(abs_filepath)
        else:
            abs_filepath = os.path.join(current_dir, file_list[0])
            self.file_opener(abs_filepath)

    def file_opener(self, file_path):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.window.open_file(file_path)

#------------------------------------------------------------------------------
# [ GlueFileWildcardOpenerCommand class ] - executed from glue wco command
#------------------------------------------------------------------------------
class GlueFileWildcardOpenerCommand(sublime_plugin.WindowCommand):
    def run(self, paths=[], current_dir="", match_pattern=""):
        if len(current_dir) > 0 and len(match_pattern) > 0:
            os.chdir(current_dir)
            file_list = glob(match_pattern)
            if len(file_list) > 0:
                for the_file in file_list:
                    abs_filepath = os.path.join(current_dir, the_file)
                    self.file_opener(abs_filepath)

    def file_opener(self, file_path):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.window.open_file(file_path)

#!/usr/bin/env python
# encoding: utf-8

import sublime
import sublime_plugin
import os
from sys import version_info

if version_info[0] == 3:
    from .GlueIO import FileWriter
else:
    from GlueIO import FileWriter

class GlueSidebarOpenerCommand(sublime_plugin.WindowCommand):
    def run(self, paths=[]):
        path = paths[0] # only use the first of the paths in the passed argument (prevents multiple terminals from opening)
        if os.path.exists(path) and os.path.isfile(path) and path.endswith('.glue'):
            self.erase_existing_glue_file(path) # clear the terminal text in .glue files
            self.open_the_file(path)
            self.window.active_view().run_command('glue')
        elif os.path.exists(path) and os.path.isfile(path):
            file_path = os.path.join(os.path.dirname(path), 'terminal.glue')
            FileWriter(file_path).write_utf8(" ")
            self.open_the_file(file_path)
            self.window.active_view().run_command('glue')
        elif os.path.exists(path) and os.path.isdir(path):
            # create a .glue terminal file in the directory if it does not exist
            os.chdir(path) # make the directory the current directory
            glue_filenames = [name for name in os.listdir(path) if name.endswith('.glue')]
            if len(glue_filenames) > 0:
                path = os.path.join(path, glue_filenames[0])
                if path.endswith('.glue'):
                    self.erase_existing_glue_file(path) # clear the terminal text in .glue files
                self.open_the_file(path)
                self.window.active_view().run_command('glue')
            else:
                # write a terminal.glue file in the selected directory
                new_glue_path = os.path.join(path, 'terminal.glue')
                FileWriter(new_glue_path).write_utf8(" ")
                if os.path.exists(new_glue_path):
                    self.open_the_file(new_glue_path)
                    self.window.active_view().run_command('glue')
        else:
            sublime.error_message("Glue Plugin Error : Glue was not able to launch the terminal from the selected path.  Try opening the file in your editor and then launching Glue from the Command Palette.")

    def open_the_file(self, path):
        window = sublime.active_window()
        view = window.open_file(path)
        # window.set_view_index(view, view_index[0], view_index[1])
        sublime.active_window().focus_view(view)

    def go_to_end(self):
        line, row = self.window.active_view().rowcol(self.window.active_view().size())
        pt = self.window.active_view().text_point(line, 0)
        self.window.active_view().sel().clear()
        self.window.active_view().sel().add(sublime.Region(pt))
        self.window.active_view().show(pt)

    def erase_existing_glue_file(self, file_path):
        FileWriter(file_path).write_utf8(' ')



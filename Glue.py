#!/usr/bin/env python
# encoding: utf-8

import sublime
import sublime_plugin
from sys import version_info
import subprocess
import sys
import time
import os

class GlueCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        self.stdout = ""
        self.stderr = ""
        self.exitcode = 1
        self.ready = False
        self.py2 = (version_info[0] == 2)
        self.userpath = '/usr/local/bin/'
        # self.userpath = '/usr/bin/'
        self.current_dirpath = ""
        self.current_filepath = ""
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        # self.settings = sublime.load_settings('Mab.sublime-settings')

    def run(self, edit):
        self.current_filepath = self.view.file_name()
        self.current_dirpath = os.path.dirname(self.current_filepath)
        os.chdir(self.current_dirpath)
        self.view.window().show_input_panel("$ ", '', self.muterun, None, None)

    def muterun(self, user_command):
        # test for an exit command and close the input panel
        if user_command == "exit":
            self.view.run_command('glue_writer', {'text': '', 'command': '', 'exit': True})
        else:
            try:
                command = self.userpath + user_command
                response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
                self.exitcode = 0
                self.stdout = response.decode('utf-8')
                self.print_response()
                self.view.run_command('glue_writer', {'text': self.stdout, 'command': user_command})
            except subprocess.CalledProcessError as cpe:
                self.stderr = cpe.output.decode('utf-8')
                if cpe.returncode:
                    self.exitcode = cpe.returncode
                else:
                    self.exitcode = 1
                self.print_response()
                self.view.run_command('glue_writer', {'text': self.stderr, 'command': user_command})
            except Exception as e:
                sys.stderr.write("Glue Plugin Error: unable to run the shell command.")
                raise e

    def print_response(self):
        if self.exitcode == 0:
            print(self.stdout)
        else:
            print(self.stderr)


class GlueWriterCommand(sublime_plugin.TextCommand):
    def run(self, edit, text="", command="", exit=False):
        PS1 = "█"
        path_string = "[ " + os.getcwd() + " ]"
        if not exit:
            command_line = PS1 + " " + path_string + " " + command + "\n"
            self.view.insert(edit, self.view.sel()[0].begin(), command_line)
            text = text + '\n'
            self.view.insert(edit, self.view.sel()[0].begin(), text)
            self.view.show(self.view.sel()[0].begin())
            # keeps the input panel open for more commands
            self.view.run_command('glue')
        else:
            # do not reopen the input panel with the run_command call above
            exit_command = PS1 + " " + path_string + " exit" + "\n"
            exit_string = "Bye Bye. ♥ Glue\n"
            self.view.insert(edit, self.view.sel()[0].begin(), exit_command)
            self.view.insert(edit, self.view.sel()[0].begin(), exit_string)
            self.view.show(self.view.sel()[0].begin())
            return True



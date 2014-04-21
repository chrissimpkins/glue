#!/usr/bin/env python
# encoding: utf-8

import sublime
import sublime_plugin
from sys import version_info
import subprocess
import os
import threading
import shlex
import json
import traceback

if version_info[0] == 3:
    import io
    from .GlueIO import FileReader
else:
    import StringIO
    from GlueIO import FileReader

class GlueCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        self.settings = sublime.load_settings('Glue.sublime-settings')
        self.stdout = ""
        self.stderr = ""
        self.exitcode = 1
        self.userpath = self.settings.get('glue_userpath')
        self.shellpath = self.settings.get('glue_shellpath')
        self.original_env_path = os.environ['PATH']
        self.ps1 = self.settings.get('glue_ps1')
        self.start_dirpath = ""
        self.current_dirpath = self.settings.get('glue_working_directory')
        self.current_filepath = ""
        self.attr_lock = threading.Lock() # thread lock for attribute reads/writes
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)

    #------------------------------------------------------------------------------
    # [ run method ] - plugin start method
    #------------------------------------------------------------------------------
    def run(self, edit):
        try:
            #------------------------------------------------------------------------------
            # Establish Current Working Directory
            # 1. check for current_dirpath attribute (empty string by default)
            # 2. if not set, set it
            # 3. if file does not exist, make it in current directory if detected, User dir if not
            # 4. if directory exists after above, then chdir into it to establish as working directory
            #------------------------------------------------------------------------------
            st_buffer = 0 # flag that indicates use of buffer with unsaved terminal.glue file
            create_file = 0 # flag that indicates a new file should be generated to run the terminal view
            self.current_filepath = self.view.file_name() # file path if file exists and is saved, otherwise None

            # check the settings to see if start directory is set
            if len(self.start_dirpath) == 0:
                # if the buffer has been saved and the filepath exists
                if self.current_filepath:
                    # set start directory with the file user has open
                    self.start_dirpath = os.path.dirname(self.current_filepath)
                else:
                    # set current directory with User directory
                    self.start_dirpath = os.path.expanduser('~')
                    st_buffer = 1 # indicate that user is attempting to use an unsaved buffer, do not create new .glue file

            if len(self.current_dirpath) == 0:
                self.current_dirpath = self.start_dirpath # if it hasn't been set yet, set it to the same directory as the start dir
                sublime.status_message('Glue: Current directory: ' + self.current_dirpath) # notify user of CWD

            # confirm that current directory exists and chdir into it
            if os.path.isdir(self.current_dirpath):
                os.chdir(self.current_dirpath) # make it the current working directory
            else:
                bad_dir_error_msg = "Glue Plugin Error: Unable to establish your working directory. Please confirm your settings if you changed the default directory. If this is not the problem, please report this as a new issue on the GitHub repository."
                sublime.error_message(bad_dir_error_msg) # launch an error dialog

            #------------------------------------------------------------------------------
            # Establish current buffer / file
            # 1. if using unsaved buffer (i.e. buffer = 1), set current path to <user-dir>/terminal.glue
            #------------------------------------------------------------------------------
            if st_buffer:
                self.current_filepath = os.path.join(self.start_dirpath, 'terminal.glue')
            else:
                if self.current_filepath: # if it is set
                    if self.current_filepath.endswith('.glue'):
                        pass # a .glue file is being used, do nothing because this is desired behavior
                    else:
                        self.current_filepath = os.path.join(self.start_dirpath, 'terminal.glue')
                        create_file = 1 # switch the create file flag so that a new file is generated with this path
                else: # otherwise the currentdir is set and need to establish the current filepath
                    self.current_filepath = os.path.join(self.start_dirpath, 'terminal.glue')
                    create_file = 0

            #------------------------------------------------------------------------------
            # Establish Active View as Appropriate File
            #------------------------------------------------------------------------------
            if self.current_filepath.endswith('.glue'):
                if self.current_filepath == self.view.file_name():
                    pass # do nothing, the active view is the appropriate .glue terminal file
                elif self.view.file_name() == None:
                    self.view.set_name('terminal.glue') #set the tab name on an unsaved buffer
                elif self.current_filepath != self.view.file_name(): # another file in the directory is opened
                    # check for an existing .glue file and open if present
                    gluefile_test_list = [name for name in os.listdir(self.start_dirpath) if name.endswith('.glue')]
                    if len(gluefile_test_list) > 0: # if there is a .glue terminal file, open it
                        self.view = self.view.window().open_file(os.path.join(self.start_dirpath, gluefile_test_list[0]))
                    else:
                        self.view = self.view.window().new_file()
                        self.view.set_name('terminal.glue')
            else:
                if st_buffer:
                    self.view.set_name('terminal.glue')
                elif create_file:
                    # confirm that there is not a .glue file in the current directory, open it if there is
                    gluefile_test_list = [name for name in os.listdir(self.start_dirpath) if name.endswith('.glue')]
                    if len(gluefile_test_list) > 0: # if there is a .glue terminal file, open it
                        self.view.window().open_file(os.path.join(self.start_dirpath, gluefile_test_list[0]))
                    else: # otherwise, create a new one
                        self.view = self.view.window().new_file() # create a new file at the file path established above
                        self.view.set_name('terminal.glue')

            #------------------------------------------------------------------------------
            # Launch the Input Panel for User Input - off to the races...
            #------------------------------------------------------------------------------
            self.view.window().show_input_panel(self.ps1 + ' ', '', self.muterun_runner, None, None)
        except Exception:
            self.exception_handler()

    #------------------------------------------------------------------------------
    # [ cleanup method ] - odds and ends before close of plugin when 'exit' called
    #------------------------------------------------------------------------------
    def cleanup(self):
        self.current_dirpath = "" # clear the saved working directory path
        self.start_dirpath = "" # clear the start directory path for the file
        self.settings.set('glue_working_directory', '') # clear the saved directory path
        if sublime.platform() == "osx":
            os.environ['PATH'] = self.original_env_path # cleanup any environ PATH changes that Glue performed on Mac systems

    #------------------------------------------------------------------------------
    # [ exception_handler ] - print stack trace for raised exceptions from Glue plugin in the editor view
    #------------------------------------------------------------------------------
    def exception_handler(self, user_command=''):
        glue_exc_message = "Glue encountered an error.  Please report this as a new issue on the GitHub repository.  Here is the stack trace:\n\n"
        if version_info[0] == 2:
            exc_string = StringIO.StringIO()
        else:
            exc_string = io.StringIO()
        # push the stack trace stream to the StringIO
        traceback.print_exc(file=exc_string)
        # get the string value of the stack trace string and assign to variable
        stack_trace = exc_string.getvalue()
        # create the user message
        user_exc_message = glue_exc_message + '\n\n' + stack_trace
        # write
        self.view.run_command('glue_writer', {'text': user_exc_message, 'command': user_command, 'exit': False})
        # close the StringIO stream
        exc_string.close()

    #------------------------------------------------------------------------------
    # [ muterun_runner ] - runner method for the main execution method
    #   here simply to wrap it in an exception handler
    #------------------------------------------------------------------------------
    def muterun_runner(self, user_command):
        try:
            self.muterun(user_command)
        except Exception:
            self.exception_handler(user_command)

    #------------------------------------------------------------------------------
    # [ muterun method ] - parse command + runner for execution of system command
    #------------------------------------------------------------------------------
    def muterun(self, user_command):
        # create a parsed command line string
        if version_info[0] == 3:
            com_args = shlex.split(user_command) # use shlex for command line handling in ST3 / Py3
        else:
            com_args = user_command.split() # use simple split on whitespace in ST2, Py2.6 does not support unicode in shlex
        # Handle missing command when user presses enter/return key
        if not com_args:
            no_command_msg = "Please enter a command"
            self.view.run_command('glue_writer', {'text': no_command_msg, 'command': '', 'exit': False})
        # EXIT command
        elif com_args[0] == "exit":
            self.cleanup() # run the cleanup method
            self.view.run_command('glue_writer', {'text': '', 'command': '', 'exit': True})
        # CD command
        elif com_args[0] == "cd":
            if len(com_args) > 1:
                # include the ~ user home directory idiom
                if com_args[1] == "~":
                    change_path = os.path.expanduser('~')
                else:
                    change_path = com_args[1]
                if os.path.exists(change_path) and os.path.isdir(change_path):
                    os.chdir(change_path)
                    directory_change_abspath = os.getcwd()
                    dir_change_text = directory_change_abspath + '\n'
                    directory_change_cmd = "cd " + change_path
                    self.current_dirpath = directory_change_abspath
                    self.settings.set('glue_working_directory', directory_change_abspath)
                    sublime.status_message('Glue: Current directory: ' + directory_change_abspath) # notify user of CWD
                    self.view.run_command('glue_writer', {'text': dir_change_text, 'command': directory_change_cmd, 'exit': False})
                else:
                    directory_change_cmd = "cd " + change_path
                    dirchange_error_message = "Directory path '" + change_path + "' does not exist\n"
                    self.view.run_command('glue_writer', {'text': dirchange_error_message, 'command': directory_change_cmd, 'exit': False})
            else:
                dirchange_error_message = "Please enter a path following the 'cd' command\n"
                self.view.run_command('glue_writer', {'text': dirchange_error_message, 'command': 'cd', 'exit': False})
        # GLUE commands
        elif com_args[0] == 'glue':
            glue_command = ' '.join(com_args)
            if len(com_args) > 1:
                # HELP Command
                if com_args[1] == "--help" or com_args[1] == "-h" or com_args[1] == "help":
                    help_text = get_help_text()
                    self.view.run_command('glue_writer', {'text': help_text, 'command': glue_command, 'exit': False})
                # BROWSE command
                elif com_args[1] == "browse":
                    if len(com_args) > 2:
                        import webbrowser
                        browse_string = com_args[2]
                        # if they requested a url with protocol, just open it
                        if browse_string.startswith('http://') or browse_string.startswith('https://'):
                            webbrowser.open(browse_string)
                        else:
                            # check if it is a local file that user wants to open in browser
                              # remove the initial OS dependent filepath separator character if added (will be added back in .join method below)
                            if browse_string.startswith(os.sep):
                                browse_string = browse_string[1:] # remove the first char (?are there typically two chars '\\' in Windows?)
                            elif os.altsep != None:
                                if browse_string.startswith(os.altsep): # if there is an alternate separator (i.e. / on windows)
                                    browse_string = browse_string[1:] # then remove it
                            check_path = os.path.join(os.path.abspath(self.current_dirpath), browse_string)
                            # test for existence of local file on the path
                            if self.is_file_here(check_path):
                                webbrowser.open('file://' + check_path) # if it is a local file, open it in browser
                            else:
                                webbrowser.open('http://' + browse_string) # if not, assume that it is a URL without protcol and add it
                        browser_msg = "glue browse [ " + browse_string + " ] complete\n"
                        self.view.run_command('glue_writer', {'text': browser_msg, 'command': glue_command, 'exit': False})
                    else:
                        browser_error_msg = "Please enter a URL or local filepath after the glue browse command\n"
                        self.view.run_command('glue_writer', {'text': browser_error_msg, 'command': glue_command, 'exit': False})
                # CLEAR command
                elif com_args[1] == "clear":
                    self.view.run_command('glue_clear_editor')
                    # keeps the input panel open for more commands
                    self.view.run_command('glue')
                # FINDER command
                elif com_args[1] == "finder":
                    # user is requesting a directory as an argument
                    if len(com_args) > 2:
                        finder_dirpath = com_args[2]
                        if os.path.isdir(finder_dirpath):
                            self.view.window().run_command("open_dir", {"dir": os.path.abspath(finder_dirpath)}) # open it
                            curdir_finder_msg = "The requested directory was opened in your finder\n"
                        elif os.path.isfile(finder_dirpath):
                            finder_dirpath = os.path.dirname(finder_dirpath)
                            self.view.window().run_command("open_dir", {"dir": os.path.abspath(finder_dirpath)}) # open it
                            curdir_finder_msg = "The requested directory was opened in your finder\n"
                        else:
                            curdir_finder_msg = "Unable to find the requested directory path.  Please try again.\n"
                        # provide Glue view output to user after execution of the finder reveal
                        self.view.run_command('glue_writer', {'text': curdir_finder_msg, 'command': glue_command, 'exit': False})
                    # user is requesting the current working directory (i.e. no argument)
                    else:
                        if len(self.current_dirpath) > 0 and os.path.isdir(self.current_dirpath):
                            self.view.window().run_command("open_dir", {"dir": self.current_dirpath})
                            curdir_finder_msg = "The current directory was opened in your finder.\n"
                            self.view.run_command('glue_writer', {'text': curdir_finder_msg, 'command': glue_command, 'exit': False})
                        else:
                            curdir_finderror_msg = "Unable to detect the current working directory.  Please restart the Glue plugin and try again.\n"
                            self.view.run_command('glue_writer', {'text': curdir_finderror_msg, 'command': glue_command, 'exit': False})
                # GOTO command
                elif com_args[1] == "goto":
                    if len(com_args) > 2:
                        goto_user_msg = "goto " + com_args[2] + " completed\n"
                        self.view.window().run_command("show_overlay", {"overlay": "goto", "show_files": True, "text": com_args[2]})
                        self.view.run_command('glue_writer', {'text': goto_user_msg, 'command': glue_command, 'exit': False})
                    else:
                        # if no query string, just open the overlay
                        goto_user_msg = "goto overlay launch completed\n"
                        self.view.window().run_command("show_overlay", {"overlay": "goto", "show_files": True})
                        self.view.run_command('glue_writer', {'text': goto_user_msg, 'command': glue_command, 'exit': False})
                # LOCALHOST command
                elif com_args[1] == "localhost":
                    import webbrowser
                    localhost_url = 'http://localhost:8000'
                    if len(com_args) > 2:
                        protocol = com_args[2] # the argument is the requested protocol (doesn't perform sanity check)
                        localhost_url = 'http://localhost:' + protocol
                    webbrowser.open(localhost_url)
                    localhost_browse_msg = "glue localhost complete\n"
                    self.view.run_command('glue_writer', {'text': localhost_browse_msg, 'command': glue_command, 'exit': False})
                # NEW command
                elif com_args[1] == "new":
                    filenew_text = "glue new command completed\n"
                    self.view.run_command('glue_writer', {'text': filenew_text, 'command': glue_command, 'exit': False})
                    self.view.window().new_file()
                # OPEN command
                elif com_args[1] == "open":
                    if len(com_args) > 2:
                        fileopen_text = "glue open command completed\n"
                        self.view.run_command('glue_writer', {'text': fileopen_text, 'command': glue_command, 'exit': False})
                        self.view.window().run_command('glue_file_opener', {'current_dir': self.current_dirpath, 'file_list': com_args[2:]})
                    else:
                        missing_file_error_msg = "Please enter at least one filepath after the open command.\n"
                        self.view.run_command('glue_writer', {'text': missing_file_error_msg, 'command': glue_command, 'exit': False})
                # PATH command
                elif com_args[1] == "path":
                    if len(self.userpath) == 0:
                        # obtain the 'real' mac osx path using the get_mac_path method if not set by user
                        if sublime.platform() == "osx":
                            # get the PATH
                            updated_path = self.get_mac_path() # attempt to obtain the PATH set in the user's respective shell startup file
                            # set the Mac environ PATH to the obtained PATH
                            os.environ['PATH'] = updated_path
                            # assign the PATH to the self.userpath attribute for the executable search below (and for reuse while running)
                            self.userpath = updated_path
                            the_path = self.userpath
                        elif sublime.platform() == "windows":
                            the_path = os.environ['PATH']
                            # do not set the PATH in Windows, letting Win shell handle the command
                        elif sublime.platform() == "linux":
                            self.userpath = os.environ['PATH']
                            the_path = self.userpath
                    else:
                        # if there is a self.userpath that is set (user set in settings, previously set above) then set Python environ PATH string
                        the_path = self.userpath
                    self.view.run_command('glue_writer', {'text': the_path + '\n', 'command': glue_command, 'exit': False})
                # USER command
                elif com_args[1] == "user":
                    uc_file_path = os.path.join(sublime.packages_path(), 'Glue-Commands', 'glue.json')
                    if self.is_file_here(uc_file_path):
                        fr = FileReader(uc_file_path)
                        user_json = fr.read_utf8()
                        usercom_dict = json.loads(user_json)
                        if len(usercom_dict) > 0:
                            if len(usercom_dict) == 1:
                                com_extension_string = 'extension'
                                com_number_string = 'lonely'
                            else:
                                com_extension_string = 'extensions'
                                com_number_string = str(len(usercom_dict))
                            number_com_msg = "Your " + com_number_string + " Glue " + com_extension_string + ":\n\n"
                            com_list = []
                            for key, value in self.xitems(usercom_dict):
                                com_string = key + " : " + value
                                com_list.append(com_string)
                            com_string = '\n'.join(sorted(com_list))
                            com_string = number_com_msg + com_string + '\n'
                            self.view.run_command('glue_writer', {'text': com_string, 'command': glue_command, 'exit': False})
                        else:
                            user_error_msg = "Your glue.json file does not contain any commands\n"
                            self.view.run_command('glue_writer', {'text': user_error_msg, 'command': glue_command, 'exit': False})
                    else:
                        usercom_error_msg = "The glue.json file could not be found.  Please confirm that this is contained in a Glue-Commands directory in your Sublime Text Packages directory.\n"
                        self.view.run_command('glue_writer', {'text': usercom_error_msg, 'command': glue_command, 'exit': False})
                # WCO command
                elif com_args[1] == "wco":
                    if len(com_args) > 2:
                        fileopen_text = "glue wco command completed\n"
                        self.view.run_command('glue_writer', {'text': fileopen_text, 'command': glue_command, 'exit': False})
                        self.view.window().run_command('glue_file_wildcard_opener', {'current_dir': self.current_dirpath, 'match_pattern': com_args[2]})
                    else:
                        missing_file_error_msg = "Please enter at least one filepath after the open command.\n"
                        self.view.run_command('glue_writer', {'text': missing_file_error_msg, 'command': glue_command, 'exit': False})
                # TEST command
                elif com_args[1] == "test":
                    pass
                    # test open containing folder

                    #self.view.window().run_command("open_dir", {"dir": self.current_dirpath})

                    # self.view.run_command('glue_writer', {'text': current_proj, 'command': glue_command, 'exit': False})
                # USER ALIAS commands
                else:
                    if len(com_args) > 1:
                        uc_file_path = os.path.join(sublime.packages_path(), 'Glue-Commands', 'glue.json')
                        if self.is_file_here(uc_file_path):
                            fr = FileReader(uc_file_path)
                            user_json = fr.read_utf8()
                            usercom_dict = json.loads(user_json)
                            # if arguments from command, add those in location indicated by the file
                            if len(com_args) > 2:
                                # arguments were included on the command line, pass them to the user command
                                arguments = ' '.join(com_args[2:])
                            else:
                                # no additional arguments were included so pass empty string if there is an {{args}} tag
                                arguments = ''
                            if com_args[1] in usercom_dict:
                                user_command = usercom_dict[com_args[1]]
                                user_command = user_command.replace('{{args}}', arguments) # replace with CL args
                                user_command = user_command.replace('{{pwd}}', os.getcwd()) #  replace with working dir path
                                user_command = user_command.replace('{{clipboard}}', sublime.get_clipboard()) # replace with contents of clipboard
                                self.muterun(user_command) # execute the command
                            else:
                                # didn't find a glue alias with the requested name in the existing glue alias settings file
                                bad_cmd_error_msg = "Glue could not identify that command.  Please try again.\n"
                                self.view.run_command('glue_writer', {'text': bad_cmd_error_msg, 'command': glue_command, 'exit': False})
                        # Didn't find a glue alias setting file, provide error message
                        else:
                            bad_cmd_error_msg = "Glue could not identify that command.  Please try again.\n"
                            self.view.run_command('glue_writer', {'text': bad_cmd_error_msg, 'command': glue_command, 'exit': False})
            else:
                missing_arg_error_msg = "Glue requires an argument.  Please use 'glue help' for for more information.\n"
                self.view.run_command('glue_writer', {'text': missing_arg_error_msg, 'command': glue_command, 'exit': False})
        # Execute the system command that was entered
        else:
            try:
                if len(com_args) > 0:
                    arguments = ' '.join(com_args[1:])
                else:
                    arguments = ''

                command = os.path.join(self.get_path(com_args[0]), com_args[0]) + " " + arguments
                t = threading.Thread(target=self.execute_command, args=(command, user_command))
                t.start() # launch the thread to execute the command
                self.progress_indicator(t) # provide progress indicator
                self.print_on_complete(t, user_command) # polls for completion of the thread and prints to editor
            except Exception as e:
                raise e

    #------------------------------------------------------------------------------
    # [ is_file_here ] - returns boolean for presence of filepath
    #------------------------------------------------------------------------------
    def is_file_here(self, filepath):
        if os.path.exists(filepath) and os.path.isfile(filepath):
            return True
        else:
            return False

    #------------------------------------------------------------------------------
    # [ get_mac_path method ] - obtain the user PATH setting on the Mac from bash
    #------------------------------------------------------------------------------
    def get_mac_path(self):
        pathgetter = "bash -ilc 'echo -n $PATH'"
        updated_path = subprocess.Popen(pathgetter, stdout=subprocess.PIPE, shell=True).stdout.read()
        # update the shell PATH with this path
        return updated_path.decode("utf-8").rstrip().rstrip(':')

    #------------------------------------------------------------------------------
    # [ get_path method ] - find the correct path to the executable from the user's PATH settings
    #------------------------------------------------------------------------------
    def get_path(self, executable):
        # if it is not set, attempt to use the environment PATH variable that Python returns
        if len(self.userpath) == 0:
            # set the mac osx PATH with os.environ['PATH'] - fix for OSX PATH set issue in with Python subprocess module
            if sublime.platform() == "osx":
                # get the PATH
                updated_path = self.get_mac_path() # obtain the PATH set in the user's respective shell rc file
                # set the Mac environ PATH to the obtained PATH
                os.environ['PATH'] = updated_path
                # assign the PATH to the self.userpath attribute for the executable search below (and for reuse while running)
                self.userpath = updated_path
            elif sublime.platform == "windows":
                pass # do nothing, do not want to set path on Win, let Win shell handle it...
            elif sublime.platform == "linux":
                self.userpath = os.environ['PATH']
        else:
            # fix for Mac OSX users PATH settings
            if sublime.platform() == "osx":
                os.environ['PATH'] = self.userpath
        # need to keep the Windows ; PATH separator logic first because the : will match in Windows paths like C:\blah
        if ';' in self.userpath:
            paths = self.userpath.split(';')
            for path in paths:
                test_path = os.path.join(path, executable)
                # Windows unicode test in Py2
                if version_info[0] == 2:
                    if os.path.isfile(unicode(test_path)):
                        return path
                # otherwise perform standard string comparisons
                if os.path.isfile(test_path):
                    return path
                elif os.path.islink(test_path):
                    return os.path.dirname(os.path.realpath(test_path))
            # if the method did not return with found path, just return empty path and keep fingers crossed...
            return ''
        elif ':' in self.userpath:
            paths = self.userpath.split(':')
            for path in paths:
                test_path = os.path.join(path, executable)
                # Unicode test in Py2, determine whether unicode string matches for OS that encodes as unicode
                if version_info[0] == 2:
                    if os.path.isfile(unicode(test_path)):
                        return path
                # otherwise perform standard string comparisons (Py3 str incorporates unicode type from Py2)
                if os.path.isfile(test_path):
                    return path
                elif os.path.islink(test_path):
                    return os.path.dirname(os.path.realpath(test_path))
            # if the method did not return with found path, just return empty path and keep fingers crossed...
            return ''
        else:
            # there was one path in the setting, so return it as the proper path to executable
            return self.userpath

    #------------------------------------------------------------------------------
    # [ print_on_complete method ] - print to editor from main thread when cmd execution complete
    #------------------------------------------------------------------------------
    def print_on_complete(self, thread, user_command):
        if thread.is_alive():
            sublime.set_timeout(lambda: self.print_on_complete(thread, user_command), 20)
            return
        else:
            # command was successful
            if self.exitcode == 0:
                # clean the standard output string
                clean_stdout = self.clean_output(self.stdout)
                self.view.run_command('glue_writer', {'text': clean_stdout, 'command': user_command})
            # command was not successful (non-zero exit status)
            else:
                self.view.run_command('glue_writer', {'text': self.stderr, 'command': user_command})

            # print to stdout as well - removed
            # self.print_response()

    #------------------------------------------------------------------------------
    # [ clean_output method ] - remove special characters that should not be printed to standard output view
    #------------------------------------------------------------------------------
    def clean_output(self, stdout_string):
        # remove carriage return char (they display as CR in ST)
        stdout_string = stdout_string.replace('\r\n', '\n') # include this above the '\r' statement so that user does not get '\n\n' replacements
        stdout_string = stdout_string.replace('\r', '\n')
        return stdout_string

    #------------------------------------------------------------------------------
    # [ progress_indicator method ] - display progress indicator for long running processes
    #------------------------------------------------------------------------------
    def progress_indicator(self, thread, i=0, direction=1):
        if thread.is_alive():
            before = i % 8
            after = (7) - before
            if not after:
                direction = -1
            if not before:
                direction = 1
            i += direction
            self.view.set_status('glue_status_indicator', 'Glue: Running command [%s|%s]' % (' ' * before, ' ' * after))
            sublime.set_timeout(lambda: self.progress_indicator(thread, i, direction), 75)
            return
        else:
            self.view.erase_status('glue_status_indicator')
            sublime.status_message('Glue: Command completed.')

    #------------------------------------------------------------------------------
    # [ execute_command method ] - execute a system command
    #   run in a separate thread from muterun() method above
    #   assigns stdout stderr and exitcode in instance attributes
    #------------------------------------------------------------------------------
    def execute_command(self, command, user_command):
        # Python 3 version = Sublime Text 3 version
        if version_info[0] == 3:
            try:
                # execute the system command (with user assigned shell if glue_shellpath is set)
                if len(self.shellpath) == 0:
                    response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
                elif os.path.exists(self.shellpath) and os.path.isfile(self.shellpath):
                    response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, executable=self.shellpath)
                else:
                    # run the default shell type if cannot identify the shellpath that the user assigned
                    response = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
                # acquire thread lock on attribute data
                with self.attr_lock:
                    self.exitcode = 0
                    self.stdout = response.decode('utf-8')
            except subprocess.CalledProcessError as cpe:
                # acquire thread lock on the attribute data
                with self.attr_lock:
                    self.stderr = cpe.output.decode('utf-8')
                    if cpe.returncode:
                        self.exitcode = cpe.returncode
                    else:
                        self.exitcode = 1
            except Exception as e:
                raise e
        # Python 2 version = Sublime Text 2 version
        else:
            try:
                if len(self.shellpath) == 0:
                    response = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
                elif os.path.exists(self.shellpath) and os.path.isfile(self.shellpath):
                    response = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               executable=self.shellpath)
                else:
                    # run the default shell if cannot identify the shellpath that the user assigned
                    response = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
                stdout, stderr = response.communicate()
                with self.attr_lock: # use the attribute lock (separate thread)
                    self.stdout = stdout.decode('utf-8')
                    self.stderr = stderr.decode('utf-8')
                    self.exitcode = response.returncode
            except Exception as e:
                raise e

    #------------------------------------------------------------------------------
    # [ print_response method ] - print a string to the stdout on ST console
    #------------------------------------------------------------------------------
    def print_response(self):
        with self.attr_lock:
            excode = self.exitcode
        if excode == 0:
            with self.attr_lock:
                print(self.stdout)
        else:
            with self.attr_lock:
                print(self.stderr)

    #------------------------------------------------------------------------------
    # [ xitems iterator ] - uses appropriate method from Py2 and Py3 to iterate through dict items
    #------------------------------------------------------------------------------
    def xitems(self, the_dict):
        if version_info[0] == 3:
            return the_dict.items()
        else:
            return the_dict.iteritems()


#------------------------------------------------------------------------------
# [ GlueWriterCommand class ] - writes to a ST view
#------------------------------------------------------------------------------
class GlueWriterCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        self.settings = sublime.load_settings('Glue.sublime-settings')
        self.ps1 = self.settings.get('glue_ps1')
        self.show_path = self.settings.get('glue_display_path')
        self.exit_message = self.settings.get('glue_exit_message')
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)

    def run(self, edit, text="", command="", exit=False):
        path_string = "[ " + os.getcwd() + " ]"
        if not exit:
            if self.show_path:
                command_line = self.ps1 + " " + path_string + " " + command + "\n"
            else:
                command_line = self.ps1 + " " + command + "\n"
            self.view.insert(edit, self.view.sel()[0].begin(), command_line)
            text = text + '\n'
            self.view.insert(edit, self.view.sel()[0].begin(), text)
            self.view.show(self.view.sel()[0].begin())
            # keeps the input panel open for more commands
            self.view.run_command('glue')
        else:
            # do not reopen the input panel with the run_command call above
            if self.show_path:
                exit_command = self.ps1 + " " + path_string + " exit\n"
            else:
                exit_command = self.ps1 + " exit\n"
            exit_string = self.exit_message + "\n"
            self.view.insert(edit, self.view.sel()[0].begin(), exit_command)
            self.view.insert(edit, self.view.sel()[0].begin(), exit_string)
            self.view.show(self.view.sel()[0].begin())

#------------------------------------------------------------------------------
# [ GlueClearEditorCommand class ] - clears the editor window
#------------------------------------------------------------------------------
class GlueClearEditorCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        the_viewer = sublime.Region(0, self.view.size())
        self.view.erase(edit, the_viewer)


#------------------------------------------------------------------------------
# [ get_help_text function ] - returns the user help string
#------------------------------------------------------------------------------
def get_help_text():
    help_string = """
        __
 .-----|  .--.--.-----.
 |  _  |  |  |  |  -__|
 |___  |__|_____|_____|
 |_____|

Copyright 2014 Christopher Simpkins | MIT License

Glue joins your shell to Sublime Text in quasi-perfect harmony.

USAGE

  <command> [option(s)]

  Enter a system command in the input panel at the bottom of your editor using the same syntax that you use in your terminal.  The standard output stream from the executable is printed in the active view of your editor after it returns.

  To quit Glue, submit the command 'exit'.

COMMANDS

  Glue provides the following additional commands:

    glue browse <url,path>    Open default browser to <url> or local <path>
    glue clear                Clear the text in the Glue view
    glue finder [path]        Reveal current directory (default) or [path] directory in finder
    glue goto <query>         Sublime Text Goto Anything search for <query>
    glue help                 Glue help
    glue localhost [port]     Open browser to localhost:8000 or optional localhost:[port]
    glue new                  Create a new Sublime Text buffer
    glue open <path>          Open a file at <path> in the editor. Accepts multiple <path>
    glue path                 View your PATH settings
    glue user                 View your Glue extensions (if present)
    glue wco <pattern>        Open file(s) with wildcard <pattern> in the editor

USER COMMANDS

  Create a `Glue-Commands` directory inside your Sublime Text `Packages` directory.  Create a `glue.json` file inside the `Glue-Commands` directory.  Then map your JSON key:value as "command-name": "system command string".

  You have the option to include the following replacement tags in your system command string:

    {{args}}              additional arguments that you include on the command line
    {{clipboard}}         the contents of the clipboard
    {{pwd}}               the current working directory path

  Launch Glue and run your command extension(s) with the following syntax:

     glue <command-name> [args]

  Your command is executed from your current working directory. Please see the documentation for additional details.

NAVIGATION

  The working directory is initially set to the directory containing the buffer in which you are using Glue (when you open from sidebar right click menu or with a project file open in the editor).

  Change directories with the 'cd' command:

  cd <directory path>        Make `directory path` the working directory
  cd ..                      Make parent directory the working directory
  cd ~                       Make user home directory the working directory

  Note that your working directory defaults to the system User directory if you launch Glue from the Command Palette without having an open project file in the editor (or in a clean editor window without an open project).

ISSUES

  Please submit bug reports on the GitHub repository @ https://github.com/chrissimpkins/glue/issues

HELP

  Detailed help is available @ http://gluedocs.readthedocs.org/

"""
    return help_string

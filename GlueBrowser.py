#!/usr/bin/env python
# encoding: utf-8

import sublime
import sublime_plugin
import webbrowser

class GlueBrowseThisCommand(sublime_plugin.TextCommand):
    def run(self, edit, url=""):
        if len(url) > 0:
            webbrowser.open(url)

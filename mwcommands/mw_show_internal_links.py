#!/usr/bin/env python\n
# -*- coding: utf-8 -*-

import sys
import webbrowser

import sublime
import sublime_plugin

pythonver = sys.version_info[0]
if pythonver >= 3:
    from . import mw_utils as mw
    from . import mw_parser as par
else:
    import mw_utils as mw
    import mw_parser as par


class MediawikerShowInternalLinksCommand(sublime_plugin.TextCommand):

    actions = ['Find', 'Open page in editor', 'Open page in browser']

    def run(self, edit):
        if mw.get_setting('offline_mode'):
            return

        self.item = None

        red_link_icon = mw.get_setting('red_link_icon')
        page = mw.api.get_page(mw.get_title())
        linksgen = mw.api.get_page_links(page, generator=True)

        self.p = par.Parser(self.view)
        self.p.register_all(par.Comment, par.Pre, par.Source, par.Link, par.TemplateAttribute, par.Template)
        if not self.p.parse():
            return

        self.menu_items = ['%s %s' % (mw.api.page_attr(v, 'name'), red_link_icon if not v.exists else '  ') for v in linksgen]
        self.find_items = [v.strip_namespace(mw.api.page_attr(v, 'name')) for v in linksgen]
        self.open_items = [mw.api.page_attr(v, 'name') for v in linksgen]
        self.ns_items = [mw.api.page_attr(v, 'namespace') for v in linksgen]

        if self.menu_items:
            sublime.set_timeout(lambda: self.view.window().show_quick_panel(self.menu_items, self.on_select), 1)
        else:
            mw.status_message('Internal links was not found.')

    def on_select(self, index):
        if index >= 0:
            self.item = {
                'find': self.find_items[index],
                'open': self.open_items[index],
                'ns': self.ns_items[index]
            }
            sublime.set_timeout(lambda: self.view.window().show_quick_panel(self.actions, self.on_done), 1)

    def on_done(self, index):
        if index == 0:
            self.select_item()
        elif index == 1:
            self.edit_item()
        elif index == 2:
            self.browse_item()

    def find_item(self):
        last_found_position = self.view.sel()[-1].b + 1
        for l in self.p.links:
            if l.get_spaced(l.name) == self.item['find'] and l.region.a > last_found_position:
                return l.region
        for l in self.p.links:
            if l.get_spaced(l.name) == self.item['find']:
                return l.region

    def select_item(self):
        if self.item is not None:
            r = self.find_item()
            if r:
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(r.a, r.a))
                self.view.show(r)

    def edit_item(self):
        if self.item is not None:
            sublime.set_timeout(lambda: self.view.window().run_command(mw.cmd('page'), {
                'action': mw.cmd('show_page'),
                'action_params': {'title': self.item['open']}
            }), 1)

    def browse_item(self):
        if self.item is not None:
            url = mw.get_page_url(self.item['open'])
            webbrowser.open(url)

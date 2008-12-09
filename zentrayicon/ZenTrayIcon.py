#!/bin/env python
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
"""
ZenTray is a system tray gadget that watches and displays the current alert level/severity from a Zenoss monitoring server.

Clicking the icon will launch Zenoss in the default web browser. Right-clicking the icon will allow you to edit your server connection settings.

New in version 0.2: The program will authenticate to the Zenoss (Zope) server using a form and cookies, which is the default login method.
"""

__version__ = '0.2'
__author__ = 'Todd Davis <tdavis@anpisolutions.com> (initial version)\nEric Wallace <e@ewall.org> (version 0.2 edits)'

import logging as log
import pygtk
import gtk
import gtk.glade
import gtk.gdk
import gobject
import urllib2
import cookielib
import urllib
import string
import webbrowser
import config
import os.path
from __init__ import DIR

_summary_path_ = '/zport/dmd/ZenEventManager/getEventSummary'
STATUS_RED = 'red'
STATUS_GREEN = 'green'
STATUS_CLEAR = 'clear'
STATUS_ORANGE = 'orange'
STATUS_YELLOW = 'yellow'
STATUS_BLUE = 'blue'
STATUS_ERROR = 'error'

levels = { '5': 'red', '4': 'orange', '3': 'yellow', '2': 'blue', '1': 'clear' }

class TrayIcon(gtk.StatusIcon):
    """
    A status icon that displays the zenoss status.
    """
    server = 'http://nmc02.anpinetwork.com:8101'
    current_status = None
    tooltip_tmpl = string.Template("""Zenoss Status
R: $red_ack/$red_tot  O: $orange_ack/$orange_tot  
Y: $yellow_ack/$yellow_tot  B: $blue_ack/$blue_tot  C: $clear_ack/$clear_tot
    """
    )
    tooltip = None
    def __init__(self, server=None):
        self.running = False
        gtk.StatusIcon.__init__(self)

        self.clear_icon = get_image('zenoss.ico')
        self.red_icon = get_image('zenoss-red.ico')
        self.green_icon = get_image('zenoss-green.ico')
        self.blue_icon = get_image('zenoss-blue.ico')
        self.yellow_icon = get_image('zenoss-yellow.ico')
        self.orange_icon = get_image('zenoss-orange.ico')
        self.error_icon = get_image('zenoss-err.ico')
        self.set_status(STATUS_ERROR)
        self.config = config.Config(self)
        self._load_config()
        self._createMenu()
        self.connect("activate", self.activate)
        self.connect("popup-menu", self._showMenu)

    def run(self):
        self._authenticate_with_cookies()
        self._get_status()
        gobject.timeout_add(1000 * self.refresh, self._get_status)
        self.running = True

    def _edit_config(self, *args):
        """
        Display the edit configuration dialog.
        """
        self.config.edit_config()
        self._load_config()
        
    def _load_config(self):
        if self.config.config_loaded:
            self.server = '%s://%s:%s' % (self.config.get('protocol'), self.config.get('server'), self.config.get('port'))
            self.refresh = int(self.config.get('refresh'))
            self.username = self.config.get('username')
            self.password = self.config.get('password')
            if not self.running:
                self.run()
        
    def _createMenu(self):
        """
        Creates the pop-up menu for the icon.
        """
        self.menu = gtk.Menu()
        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect("activate", self.destroy)
        about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        about.connect("activate", self.ShowAbout)
        configure = gtk.ImageMenuItem(gtk.STOCK_PROPERTIES)
        configure.connect("activate", self._edit_config)

        self.menu.add(about)
        self.menu.add(configure)
        self.menu.add(quit)

        self.menu.show_all()
        
    def _showMenu(self, status_icon, button, activate_time):
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, status_icon)

    def _authenticate_with_cookies(self):
        """
        Establishes cookie management, then POSTs to the site's login form. If
        successful, this will save the session cookie and use it for future HTTP
        requests made via 'opener'.
        """

        # set up CookieJar to receive and keep cookies from Zope server
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)

        # submit form to authentication page
        form_path = "/zport/acl_users/cookieAuthHelper/login"
        form_params = urllib.urlencode({
                "came_from" : self.server + "/zport/dmd",
                "submitted" : "true",
                "__ac_name" : self.username,
                "__ac_password" : self.password })
        self.opener.open(self.server + form_path, form_params)
        
    def _get_status(self):
        """ 
        Gets the status from the Zenoss server and calls set_status to display the 
        correct icon.  The status set will be the highest unacknowledged severity.
        
        This method always returns True so that the gobject.timeout_add(...) 
        continues to invoke the routine.
        
        @return True
        """
        tooltip = { 'server': self.server }
        log.debug("Reading Zenoss status...")
        try:
            response = self.opener.open(self.server + _summary_path_)
            status = eval(response.read())
            (red_stat, orange_stat, yellow_stat, blue_stat, clear_stat) = status

            if self._is_status(red_stat):
                cur_stat = STATUS_RED
            elif self._is_status(orange_stat):
                cur_stat = STATUS_ORANGE
            elif self._is_status(yellow_stat):
                cur_stat = STATUS_YELLOW
            elif self._is_status(blue_stat):
                cur_stat = STATUS_BLUE
            elif self._is_status(clear_stat):
                cur_stat = STATUS_CLEAR
            else:
                cur_stat = STATUS_GREEN
            log.debug("Status is %s" % cur_stat)
        
            tooltip['status'] = cur_stat
            for (name, ack, tot) in status:
                lvl = name.split('_')[1]
                tooltip[levels[lvl] + '_ack'] = ack
                tooltip[levels[lvl] + '_tot'] = tot
                
            self.set_tooltip(self.tooltip_tmpl.substitute(tooltip))
        except Exception,e:
            cur_stat = STATUS_ERROR
            log.warn(str(e))
            self.set_tooltip(str(e))
        
        self.set_status(cur_stat)

        return True
        
    def _is_status(self, level):
        """
        Checks the given status level to see if there are unacknowledged events.  
        If there are, it will return true.
        
        @param level is the list of [name, ACK, EVENTS]
        @return True if this level has unacknowledged events
        """
        (name, ack, tot) = level
        if int(tot) > int(ack):
            return True
        else:
            return False

    def set_status(self,status_id):
        """
        Sets the status icon based on the ID.  Should be one of:
            STATUS_GREEN
            STATUS_YELLOW
            STATUS_ORANGE
            STATUS_RED
            STATUS_CLEAR
            STATUS_BLUE
        @param status_id the id of the status
        """
        if not self.current_status == status_id:
            self.current_status = status_id
            if status_id == STATUS_CLEAR:
                self.set_from_pixbuf(self.clear_icon)
            else:
                self.set_from_pixbuf(getattr(self, '%s_icon' % status_id))
            self.set_blinking(status_id == STATUS_RED)

    def activate(self, status_icon, *args):
        """ 
        Activate the icon -- launches the webbrowser to view the status.
        """
        try:
            webbrowser.open(self.server + '/zport/dmd/Events/viewEvents?state=New')
        except Exception, e:
            log.warn(str(e))

    def destroy(self, *args):
        self.set_visible(False)
        gtk.main_quit()

    def ShowAbout(self, *args):
        import re
        if not hasattr(gtk,'AboutDialog'):
            return
        REV = re.compile(r"""\$Revision:(.*)\$""")
        m = REV.match(__version__)
        if m:
            ver = "r"+m.group(1).strip()
        else:
            ver = __version__

    #        'logo' : self._get_image('anpilogo.gif'),
    #        'artists' : ['Jan Ritter'],

        PROPS = {
            'name' : 'ZenTrayIcon',
            'comments' : __doc__,
            'version' : ver,
            'authors' : [__author__],
            'icon' : self.clear_icon,
            'copyright' : "http://www.fsf.org/licensing/licenses/info/GPLv2.html",
            'website' : 'http://www.zenoss.com/',
        }
        try:
            f = open(os.path.join('share', 'doc', 'zentrayicon', 'COPYRIGHT'))
            PROPS['license'] = f.read()
            f.close()
            del f
        except: pass
        ad = gtk.AboutDialog() #GTK 2.6
        for k,v in PROPS.items():
            try:
                ad.set_property(k,v)
            except Exception, err:
                print type(err), err
        def resp(dlg, r):
            if r in [gtk.RESPONSE_OK, gtk.RESPONSE_CANCEL, gtk.RESPONSE_CLOSE, 
                    gtk.RESPONSE_YES, gtk.RESPONSE_NO]:
                dlg.hide()
                dlg.destroy()
        ad.connect('response', resp)
        ad.present()	        

def get_image(filename):
    """
    Retrieves the given image file.
    """
    return gtk.gdk.pixbuf_new_from_file(os.path.join(DIR, 'pixmaps', filename))
    
def main():
    """
    Start the main GTK loop.
    """
    gtk.main()
    
if __name__ == '__main__':
    zenstatus = TrayIcon()
    main()

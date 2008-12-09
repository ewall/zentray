# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.


import ConfigParser
import user
import logging as log
import os.path
import gtk
import gtk.glade
from __init__ import DIR

home =  user.home
configfilename = ".ZenTrayIcon.ini"

class _fauxfield(object):
    """ Fake field for setting default values. """
    def __init__(self,value):
        """ Create a new field setting the value """
        self.value = value
        
    def get_text(self):
        return self.value
        
class Config(object):
    cfg_options = [ 'port', 'server', 'protocol', 'refresh', 'username', 'password' ]
    
    """
    Represents the configuration for the TrayIcon.
    """
    def __init__(self, mainWin):
        self.config_loaded = False
        self.mainWin = mainWin
        self.cfg = ConfigParser.ConfigParser()
        self.load_config()
        
    def load_config(self):
        """ 
        Loads the configuration from the file.
        """
        try:
            loaded_files = self.cfg.read(self._get_configfile())
            if not loaded_files:
                log.warn("Config file not loaded: %s" % self._get_configfile())
                self._load_default_config()
                self.edit_config()
            else:
                self.config_loaded = True
        except Exception, e:
            log.warn("Error loading config file %s: %s" % (self._get_configfile(), str(e)))
            self._load_default_config()
            self.edit_config()
            
    def _load_default_config(self):
        """
        Creates a default configuration file.
        """
        self._set_config_option(_fauxfield('localhost'), 'server')
        self._set_config_option(_fauxfield('8080'), 'port')
        self._set_config_option(_fauxfield('15'), 'refresh')
        self._set_config_option(_fauxfield('http'), 'protocol')
        self._set_config_option(_fauxfield('your_zenoss_username'), 'username')
        self._set_config_option(_fauxfield('your_zenoss_password'), 'password')
        self.write_config()
    
    def get(self, option):
        """
        Gets a configuration option.
        @param option The option to retrieve.
        @return the value of the option
        
        >>> config.get('server')
        localhost
        """
        value = ''
        if self.cfg.has_section('TrayIcon') and self.cfg.has_option('TrayIcon', option):
            value = self.cfg.get('TrayIcon', option)
        return value
        
    def get_configs(self):
        return self.cfg
        
    def _get_configfile(self):
        """
        Builds the configuration file name.
        @return the filename/path for the configuration
        """
        return os.path.join(home, configfilename)
        
    def save_config(self, *args):
        """
        Saves the configuration to disk.
        """
        log.debug("Saving config...")
        for option in self.cfg_options:
            obj = getattr(self, option + '_entry')
            if option == 'protocol':
                obj = obj.child
            self._set_config_option(obj, option)
        self.write_config()
        self._close_dialog()
        self.mainWin._load_config()
        
    def write_config(self):
        """
        Writes the current configuration to the file.
        """
        try:
            fd = open(self._get_configfile(), 'w')
            self.cfg.write(fd)
            fd.close()
            self.config_loaded = True
        except Exception, e:
            log.error("Cannot save configuration: " + str(e))
        
    def _set_config_option(self, entry, field):
        if not self.cfg.has_section('TrayIcon'):
            self.cfg.add_section('TrayIcon')
        self.cfg.set('TrayIcon', field, entry.get_text())
        
    def _close_dialog(self, *args):
        if self.cfg_dialog:
            self.cfg_dialog.destroy()
            if __name__ == '__main__':
                gtk.main_quit()
            
    def edit_config(self):
        """
        Allows the user to edit the configuration.
        """
        signals = { "on_save_button_clicked" : self.save_config,
            "on_cancel_button_clicked" : self._close_dialog,
            }
        self.dialog_xml = gtk.glade.XML(os.path.join(DIR, 'zentrayicon.glade'))
        self.dialog_xml.signal_autoconnect(signals)
        self.cfg_dialog = self.dialog_xml.get_widget('cfg_dialog')
        for option in self.cfg_options:
            widget = option + '_entry'
            setattr(self, widget, self.dialog_xml.get_widget(widget))
            obj = getattr(self, option + '_entry')
            if option == 'protocol':
                obj = obj.child
            obj.connect("changed", self._set_config_option, option)
            value = self.get(option)
            if option == 'refresh' and value == '':
                value = '0'
            obj.set_text(value)

        
        
if __name__ == '__main__':
    log.getLogger().setLevel(log.DEBUG)
    config = Config()
    gtk.main()

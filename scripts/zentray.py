#!/bin/env python
"""
Script to launch the ZenTrayIcon app.
"""

import zentrayicon.ZenTrayIcon as zti
import gtk


def main():
    """
    Start the main GTK loop.
    """
    gtk.main()
    
if __name__ == '__main__':
    zenstatus = zti.TrayIcon()
    main()
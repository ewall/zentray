from distutils.core import setup
import glob
import os.path

import sys
import zentrayicon.ZenTrayIcon as app

import os
if os.name == 'nt':
    import py2exe

#sys.stdout = open('screen.txt','w',0)
#sys.stderr = open('errors.txt','w',0)

def get_datafiles():
    import glob
    lst = [["zentrayicon", ['zentrayicon/zentrayicon.glade']]]
    icons = glob.glob( os.path.join('zentrayicon', 'pixmaps', '*.ico'))
    lst.append( [os.path.join('zentrayicon', 'pixmaps'), icons] )
    lst.append( [os.path.join('share','doc','zentrayicon'), ['COPYRIGHT']])
    return lst
    
    

setup(name='zentrayicon',
    version=app.__version__,
    author='Todd Davis; Eric Wallace',
    author_email = "todd@davisnetonline.com; e@ewall.org",
    license = 'GPL',
    description = 'Systray status monitor for Zenoss',
    long_description = app.__doc__,
    packages = [ 'zentrayicon' ],
    package_dir = { 'zentrayicon': 'zentrayicon' }, 
    package_data = { 'zentrayicon': [ '*.glade', 'pixmaps/*.ico'] },
    url = 'http://www.zenoss.com',
    scripts = glob.glob('scripts/*'),
    windows=[{'script':'scripts/zentray.py',  }],
    options = {
        'py2exe': {
            'dist_dir': os.path.join('dist', 'py2exe'), 
            'skip_archive': 1,
            'packages':'encodings, zentrayicon',
            'includes': 'cairo, pango, pangocairo, atk, gobject',
        }
    },
    data_files = get_datafiles(),
)

# for py2exe:
# xcopy /e /i \gtk\etc dist\py2exe\etc
# xcopy /e /i \gtk\share dist\py2exe\share
# xcopy /e /i \gtk\lib dist\py2exe\lib
# del /s /q dist\py2exe\share\locale\*    

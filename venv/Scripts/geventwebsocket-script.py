#!D:\PycharmProjects\flask_deemo\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'geventwebsocket==0.1.1','console_scripts','geventwebsocket'
__requires__ = 'geventwebsocket==0.1.1'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('geventwebsocket==0.1.1', 'console_scripts', 'geventwebsocket')()
    )

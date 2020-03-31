#!"C:\Users\ymamo\Google Drive\MultiLevel_Mesa\multilevel_mesa\venv\Scripts\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'Mesa==0.8.6','console_scripts','mesa'
__requires__ = 'Mesa==0.8.6'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('Mesa==0.8.6', 'console_scripts', 'mesa')()
    )

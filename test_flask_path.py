import os
from flask import Flask
import sys

app = Flask(__name__, static_folder='.', static_url_path='')
print("CWD:", os.getcwd())
print("Flask root_path:", app.root_path)
print("Flask static_folder:", app.static_folder)
print("sys.executable:", sys.executable)
if hasattr(sys, '_MEIPASS'):
    print("_MEIPASS:", sys._MEIPASS)

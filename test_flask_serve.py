import sys, os
from flask import Flask

frontend_folder = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, static_folder=frontend_folder, static_url_path='')

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    print("Static folder:", app.static_folder)
    app.run(port=5002)

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    # Read the MY_NAME environment variable from the container's environment
    return f"<h1>Hello from the Python Container, my name is {os.environ.get('MY_NAME', 'Stranger')}!</h1>"

if __name__ == '__main__':
    # 0.0.0.0 is necessary so the app is accessible outside the container's localhost
    app.run(debug=True, host='0.0.0.0', port=5000)

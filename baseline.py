from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'PLEASE WORK'

if __name__ == '__main__':
    app.run(debug=False, port=10000)
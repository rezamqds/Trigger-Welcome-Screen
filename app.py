from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import sqlite3
import time
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = "people.db"
TRIGGER_FILE = "trigger.txt"

@app.route("/")
def index():
    return '''
    <h1>Welcome Page</h1>
    <ul id="welcome-messages"></ul>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js"></script>
    <script>
        var socket = io();

        socket.on("new_entry", function(data) {
            let li = document.createElement("li");
            li.innerText = "🎉 Welcome " + data.name + " " + data.lastname + "!";
            document.getElementById("welcome-messages").appendChild(li);
        });
    </script>
    '''

def watcher_thread():
    last_code = None
    while True:
        try:
            if os.path.exists(TRIGGER_FILE):
                with open(TRIGGER_FILE, "r") as f:
                    code = f.read().strip()

                if code and code != last_code:
                    last_code = code
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, lastname FROM list WHERE code = ?", (code,))
                    row = cursor.fetchone()
                    conn.close()

                    if row:
                        name, lastname = row
                        socketio.emit("new_entry", {"name": name, "lastname": lastname})
                
                
                open(TRIGGER_FILE, "w").close()

        except Exception as e:
            print("Watcher error:", e)

        time.sleep(1)

threading.Thread(target=watcher_thread, daemon=True).start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050)
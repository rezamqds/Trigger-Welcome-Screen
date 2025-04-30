from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import sqlite3
import time
import os
import eventlet
eventlet.monkey_patch()


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = "personel"
TRIGGER_FILE = "trigger.txt"

@app.route("/")
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome Portal</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            body {
                background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #fff;
            }

            .container {
                width: 90%;
                max-width: 800px;
                padding: 2rem;
            }

            .header {
                text-align: center;
                margin-bottom: 2rem;
            }

            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 1rem;
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: fadeIn 1s ease-out;
            }

            .welcome-messages {
                list-style: none;
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }

            .welcome-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 1.5rem;
                transform: translateY(20px);
                opacity: 0;
                animation: slideUp 0.5s ease forwards;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
            }

            .welcome-card:hover {
                transform: translateY(-5px);
            }

            .welcome-card .name {
                font-size: 1.5rem;
                font-weight: 600;
                color: #4ecdc4;
                margin-bottom: 0.5rem;
            }

            .welcome-card .time {
                font-size: 0.9rem;
                color: #888;
            }

            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .particles {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
            }

            .particle {
                position: absolute;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                animation: float 15s infinite linear;
            }

            @keyframes float {
                0% {
                    transform: translateY(0) rotate(0deg);
                }
                100% {
                    transform: translateY(-100vh) rotate(360deg);
                }
            }
        </style>
    </head>
    <body>
        <div class="particles" id="particles"></div>
        <div class="container">
            <div class="header">
                <h1>Welcome Portal</h1>
            </div>
            <ul class="welcome-messages" id="welcome-messages"></ul>
        </div>

        <script>
            // Create floating particles
            function createParticles() {
                const particlesContainer = document.getElementById('particles');
                for (let i = 0; i < 50; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.width = Math.random() * 5 + 'px';
                    particle.style.height = particle.style.width;
                    particle.style.left = Math.random() * 100 + 'vw';
                    particle.style.animationDuration = Math.random() * 15 + 5 + 's';
                    particle.style.animationDelay = Math.random() * 5 + 's';
                    particlesContainer.appendChild(particle);
                }
            }

            createParticles();

            // Socket.io connection
            var socket = io();

            socket.on("new_entry", function(data) {
                const welcomeMessages = document.getElementById('welcome-messages');
                const li = document.createElement('li');
                li.className = 'welcome-card';
                
                const nameDiv = document.createElement('div');
                nameDiv.className = 'name';
                nameDiv.innerHTML = `🎉 Welcome ${data.name} ${data.lastname}!`;
                
                const timeDiv = document.createElement('div');
                timeDiv.className = 'time';
                timeDiv.textContent = new Date().toLocaleTimeString();
                
                li.appendChild(nameDiv);
                li.appendChild(timeDiv);
                
                welcomeMessages.insertBefore(li, welcomeMessages.firstChild);

                // Remove old messages if there are more than 10
                while (welcomeMessages.children.length > 10) {
                    welcomeMessages.removeChild(welcomeMessages.lastChild);
                }
            });
        </script>
    </body>
    </html>
    '''

def watcher_thread():
    last_code = None
    while True:
        try:
            if os.path.exists(TRIGGER_FILE):
                try:
                    with open(TRIGGER_FILE, "r") as f:
                        code = f.read().strip()
                        print(f"[Watcher] Got code from file: {code}")

                    if code and code != last_code:
                        print(f"[Watcher] New code detected: {code}")
                        last_code = code
                        
                        try:
                            conn = sqlite3.connect(DB_PATH)
                            conn.row_factory = sqlite3.Row 
                            cursor = conn.cursor()
                            
                            cursor.execute("SELECT * FROM list WHERE code = ?", (code,))
                            result = cursor.fetchall()

                            if result:
                                details = [dict(row) for row in result]
                                name = details[0]["name"]
                                lastname = details[0]["lastname"]
                                print(f"[Watcher] Found in DB: {name} {lastname}")
                                socketio.emit("new_entry", {"name": name, "lastname": lastname})
                            else:
                                print("[Watcher] No matching record found in database")
                                
                        except sqlite3.Error as e:
                            print(f"[Watcher] Database error: {e}")
                        finally:
                            if 'conn' in locals():
                                conn.close()
                                
                    # Clear the trigger file
                    with open(TRIGGER_FILE, "w") as f:
                        pass
                        
                except IOError as e:
                    print(f"[Watcher] File operation error: {e}")

        except Exception as e:
            print(f"[Watcher] Unexpected error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    threading.Thread(target=watcher_thread, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5050)

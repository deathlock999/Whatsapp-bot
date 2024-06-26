from flask import Flask, request  # Import Flask and request object

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome server!"
# Route to trigger the bot execution
@app.route('/run_bot', methods=['POST'])
def run_bot_task():
    from tasks import app as celery_app  # Import Celery app from tasks.py
    celery_app.send_task('tasks.run_bot')
    return "Bot execution initiated!", 202  # Accepted response

if __name__ == '__main__':
    # Set the port (adjust as needed)
    app.run(host='0.0.0.0', port=5000)  # Bind to all interfaces and port 5000

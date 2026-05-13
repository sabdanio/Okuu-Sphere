from multiprocessing import Process
import subprocess

def run_bot():
    subprocess.run(["python", "bot.py"])

def run_api():
    subprocess.run([
        "uvicorn", "api:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    Process(target=run_bot).start()
    Process(target=run_api).start()

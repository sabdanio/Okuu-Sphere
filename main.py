from multiprocessing import Process
import os

def run_bot():
    os.system("python bot.py")

def run_api():
    os.system("python -m uvicorn api:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    p1 = Process(target=run_bot)
    p2 = Process(target=run_api)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
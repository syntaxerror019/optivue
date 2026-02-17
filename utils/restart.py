import sys
import os
import psutil

def restart_script():
    try:
        process = psutil.Process(os.getpid())

        for handler in process.open_files() + process.connections():
            os.close(handler.fd)
    except Exception as e:
        print(e)

    python = sys.executable
    os.execl(python, python, *sys.argv)
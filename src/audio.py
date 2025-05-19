from pathlib import Path
import subprocess
import time


def get_files(path):
    d = Path(path)

    files = []
    if d.is_dir():
        files = sorted([f for f in d.iterdir() \
            if (f.is_file() and f.suffix == ".wav")])

    return files

def play(dev, path):
    return subprocess.Popen(['aplay', f'-D{dev}', path])

def killall():
    p = subprocess.Popen(['killall', 'aplay'])
    while True:
        if p.poll() is not None:
            if p.returncode == 0:
                return True
            else:
                return False

        time.sleep(1)

if __name__ == "__main__":
    import sys

    try:
        dev = sys.argv[1]
    except:
        print("No argument for audio device provided")
        sys.exit(1)

    try:
        path = sys.argv[2]
    except:
        print("No argument for audio file provided")
        sys.exit(1)

    p = play(dev, path)
    while True:
        time.sleep(1)
        print('Playing...')
        if p.poll() is not None:
            print(f"Finished with return code {p.returncode}.")
            break

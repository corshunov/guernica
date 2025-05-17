from pathlib import Path
import subprocess


def get_files(path):
    return sorted([i for i in Path(path).iterdir() \
        if (i.is_file() and i.suffix == ".wav")])

def play(path):
    return subprocess.Popen(['aplay', '-Dhdmi:CARD=vc4hdmi', path])

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
    import time

    try:
        path = sys.argv[1]
    except:
        print("No argument for audio file provided")
        sys.exit(1)

    p = play(path)
    while True:
        print('Playing...')
        if p.poll() is not None:
            print("Finished with return code {p.returncode}")
            break

        time.sleep(1)

from pathlib import Path
import subprocess


def get_files():
    p = Path("/home/tami/audio")
    return sorted([i for i in p.iterdir() \
        if (i.is_file() and i.suffix == ".wav")])

def play(path):
    #return subprocess.Popen(['aplay', '-Dhdmi:CARD=vc4hdmi', path])
    return subprocess.Popen(['aplay', path])

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
        time.sleep(1)
        if p.poll() is not None:
            break

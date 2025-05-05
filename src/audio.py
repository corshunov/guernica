from pathlib import Path
import subprocess

def get_files(path):
    return sorted([i for i in Path(path).iterdir() \
        if (i.is_file() and i.suffix == ".wav")])

def play_audio(path):
    return subprocess.Popen(['aplay', '-Dhdmi:CARD=vc4hdmi', path])

if __name__ == "__main__":
    import sys
    import time

    try:
        path = sys.argv[1]
    except:
        print("No argument for audio file provided")
        sys.exit(1)

    p = play_audio(path)
    while True:
        print('Playing...')
        time.sleep(1)
        if p.poll() is not None:
            break

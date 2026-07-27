import os


def probe(paths):
    for p in paths:
        try:
            os.stat(p)
        except OSError:
            continue  # slopcheck: ok — probe is best-effort

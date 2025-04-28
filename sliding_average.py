import random

class SlidingAverage():
    @classmethod
    def show_check(cls, n, ws):
        if n <= 0:
            raise Exception("Argument 'n' must be greater than 0")

        sla = cls(ws)

        options = list(range(-100, 101))
        vals = [random.choice(options) for _ in range(n)]

        for i, v in enumerate(vals):
           if i < ws:
               ivals = vals[:i+1] + [0] * (ws-i-1)
           else:
               ivals = vals[i+1-ws:i+1]

           ivals_avg = round(sum(ivals) / ws, sla.ndec)
           sla_avg = sla.add(v)

           ivals_text = " ".join([f"{i:4}" for i in ivals])
           sla_text = " ".join([f"{i:4}" for i in sla.vals])
           check_text = "yes" if ivals_avg == sla_avg else "no"
           print(f"{v:4} | {ivals_text} | {sla_text} | {ivals_avg:6.2f} {sla_avg:6.2f} | {check_text}")

    def __init__(self, ws, ndec=2):
        if ws <= 0:
            raise Exception("Invalid window size")

        self._ws = ws
        self._ndec = ndec
        self._i = 0
        self._vals = [0] * self.ws
        self._sum = 0.

    @property
    def ws(self):
        return self._ws

    @property
    def ndec(self):
        return self._ndec

    @property
    def avg(self):
        return round(self._sum / self._ws, self._ndec)

    @property
    def vals(self):
        return self._vals

    def add(self, v):
        self._sum -= self._vals[self._i]
        self._sum += v

        self._vals[self._i] = v
        self._i = (self._i + 1) % self._ws

        return self.avg

if __name__ == "__main__":
    import sys

    try:
        n = sys.argv[1]
    except:
        n = 12

    try:
        n = int(n)
        if n <= 0:
            raise Exception
    except:
        print("List length must be integer greater than 0")
        sys.exit(1)

    try:
        ws = sys.argv[2]
    except:
        ws = 4

    try:
        ws = int(ws)
        if (ws <= 0) or (ws > n):
            raise Exception
    except:
        print("Window size must be integer in range (0, <list_length>]")
        sys.exit(1)

    print(f"List length: {n}\nWindow size: {ws}\n")
    SlidingAverage.show_check(ws, n)

class SlidingAverage():
    def __init__(self, ws):
        if ws <= 0:
            raise Exception("Invalid window size")

        self._ws = ws
        self._i = 0
        self._vals = [0] * self.ws
        self._sum = 0.

    @property
    def ws(self):
        return self._ws

    @property
    def avg(self):
        return round(self._sum / self._ws, 2)

    @property
    def values(self):
        return self._vals

    def add(self, v):
        self._sum -= self._vals[self._i]
        self._sum += v

        self._vals[self._i] = v
        self._i = (self._i + 1) % self._ws

        return self.avg


if __name__ == "__main__":
    import random

    ws = 10
    avg = SlidingAverage(ws)

    options = list(range(100))
    vals = [random.choice(options) for _ in range(20)]

    for i, v in enumerate(vals):
       if i < ws:
           vs = vals[:i+1] + [0] * (ws-i-1)
       else:
           vs = vals[i+1-ws:i+1]

       vs_res = round(sum(vs) / ws, 2)

       res = avg.add(v)
       
       print(v)
       print(vs)
       print(avg.values)
       print(res, vs_res)
       print()

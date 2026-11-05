"""A sampling profiler (0.225): another thread looks at the main thread's stack every ms; counts per function
(inclusive: each function on the stack once per sample) and the commonest whole stacks — where cProfile loses its
way in IfcOpenShell's calls.

    from sonda_amostras import Sampler
    with Sampler() as sm:
        ...  # what is slow
    print(sm.report())
"""
import collections
import sys
import threading
import time


class Sampler:
    def __init__(self, interval=0.001, only="BIM/"):
        self.interval, self.only = interval, only
        self.inclusive = collections.Counter()
        self.leaf = collections.Counter()
        self.stacks = collections.Counter()
        self.samples = 0
        self._stop = threading.Event()
        self._main = threading.main_thread().ident

    def _run(self):
        while not self._stop.is_set():
            frame = sys._current_frames().get(self._main)
            if frame is not None:
                names = []
                f = frame
                while f is not None:
                    code = f.f_code
                    names.append("{}:{}({})".format(code.co_filename.replace("/opt/arqbim/venv/lib/python3.12/site-packages/", ""),
                                                    f.f_lineno, code.co_name))
                    f = f.f_back
                self.samples += 1
                for n in set(names):
                    self.inclusive[n.rsplit(":", 1)[0] + ":" + n.split("(")[-1]] += 1
                self.leaf[names[0]] += 1
                ours = [n for n in names if self.only in n][:6]
                self.stacks[" <- ".join(ours)] += 1
            time.sleep(self.interval)

    def __enter__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()

    def report(self, top=40):
        out = ["samples: {}".format(self.samples), "-- inclusive (ours) --"]
        for n, c in self.inclusive.most_common(400):
            if self.only in n:
                out.append("{:5.1f}%  {}".format(100.0 * c / max(self.samples, 1), n.replace(self.only, "")))
                if len(out) > top:
                    break
        out.append("-- leaf --")
        for n, c in self.leaf.most_common(15):
            out.append("{:5.1f}%  {}".format(100.0 * c / max(self.samples, 1), n))
        out.append("-- stacks (ours) --")
        for n, c in self.stacks.most_common(12):
            out.append("{:5.1f}%  {}".format(100.0 * c / max(self.samples, 1), n.replace(self.only, "")))
        return "\n".join(out)

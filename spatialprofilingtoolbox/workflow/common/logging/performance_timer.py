import time

import pandas as pd
import numpy as np


class PerformanceTimer:
    """
    An object of this class makes it easy to track which part of complex
    branching code is taking a long time, with only a few additional lines of
    monitoring code.

    Use record_timepoint at key moments, supplying a short message/title that
    indicates what the context, typically an indication of what has just completed.
    Whenever you want to assess the time performance, use report (as_string=True)
    to get a markdown representation of a table of times, on the basis of *pairs*
    of code locations (as indicated by your messages) occurring consecutively.
    Included in the report are fraction of time spent, total time spent (seconds),
    average time spent per occurrence, frequency of occurrence.
    """
    def __init__(self):
        self.times = {}
        self.previous_time = None
        self.message_order = {}

    def record_timepoint(self, message):
        now = time.perf_counter()
        if self.previous_time != None:
            diff = now - self.previous_time
            transition = (message, self.previous_message)
            if not transition in self.times:
                self.times[transition] = []
            self.times[(message, self.previous_message)].append(diff)
        self.previous_time = now
        self.previous_message = message
        if not message in self.message_order:
            n = len(self.message_order)
            self.message_order[message] = n

    def report(self, as_string=False, by=None):
        transitions = sorted(
            list(self.times.keys()),
            key=lambda x: (self.message_order[x[0]], self.message_order[x[1]]),
        )
        records = []
        all_totals = sum([np.sum(self.times[t]) for t in transitions])
        for t in transitions:
            total = np.sum(self.times[t])
            frequency = len(self.times[t])
            records.append({
                'from' : t[1],
                'to' : t[0],
                'average time spent' : total / frequency,
                'total time spent' : total,
                'frequency' : frequency,
                'fraction' : total / all_totals,
            })
        df = pd.DataFrame(records)
        if by in ['average time spent', 'total time spent', 'frequency']:
            df.sort_values(by=by, inplace=True, ascending=False)
        if as_string:
            return df.to_markdown(index=False)
        else:
            return df

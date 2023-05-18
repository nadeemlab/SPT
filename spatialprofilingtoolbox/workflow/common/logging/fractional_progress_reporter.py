"""Logs basic indicator of amount of progress, at a configurable interval."""
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

class FractionalProgressReporter:
    """Logs basic indicator of amount of progress, at a configurable interval."""
    def __init__(self, size, parts=2, task_description='task', done_message='Done.'):
        self.size = size
        self.parts = parts
        self.task_description = task_description
        self.done_message = done_message
        self.counter = 0
        self.key_times = [round((i+1) * (size / parts)) for i in range(parts)]

    def increment(self, iteration_details=None):
        self.counter = self.counter + 1
        if self.counter in self.key_times:
            percent = round(100 * (self.counter / self.size))
            self.report(percent, iteration_details=iteration_details)

    def report(self, percent, iteration_details=None):
        arguments = [percent, self.task_description]
        message = '%s%% finished with %s.'
        if iteration_details is not None:
            arguments.append(iteration_details)
            message = '%s%% finished with %s. (%s ...)'
        logger.info(message, *arguments)

    def done(self):
        logger.info(self.done_message)

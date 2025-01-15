import logging
import time

LOG_LEVEL = logging.DEBUG

class WLWLogger(logging.Logger):
    """
    Custom logger class that implements special utility functions.

    Automatically sets the file handler and formatter on __init__.
    """
    def __init__(self, name, level = 0):
        super().__init__(name, level)

        self.setLevel(LOG_LEVEL)
        # self.log_file_handler = logging.FileHandler(f"wlw_{str(time.time()).split('.')[0]}.log", "w")
        self.log_file_handler = logging.FileHandler("wlw.log", "w")
        self.log_formatter = logging.Formatter('%(asctime)s:%(threadName)s/%(module)s/[%(levelname)s] - %(message)s')
        self.log_file_handler.setFormatter(self.log_formatter)
        self.addHandler(self.log_file_handler)


    def log_blank(self):
        """
        Insert a completely blank line into the log file.

        Should be threadsafe, but use sparingly just in case.
        """
        for handler in self.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.acquire() # ensure we're still threadsafe
                try:
                    handler.stream.write("\n")
                    handler.flush()
                finally:
                    handler.release()


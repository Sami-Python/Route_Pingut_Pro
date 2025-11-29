import sys
import logging
from logging.handlers import RotatingFileHandler

class PrintLogger:
    """
    A custom file-like object that:
    1. Writes to a logger (so it goes to the log file with timestamps)
    2. Writes to the original stdout/stderr (so it still shows in Docker logs)
    """
    def __init__(self, logger, level=logging.INFO, original_stream=sys.stdout):
        self.logger = logger
        self.level = level
        self.original_stream = original_stream

    def write(self, message):
        # Write to the original stream (console)
        self.original_stream.write(message)
        self.original_stream.flush()
        
        # Log to file (strip to avoid extra newlines since logger adds them)
        if message.strip():
            self.logger.log(self.level, message.strip())

    def flush(self):
        self.original_stream.flush()

def setup_logging(log_file="api.log"):
    """
    Setup logging to write to a file and capture print() statements.
    """
    # 1. Configure the root logger to write to a file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
        ]
    )

    # 2. Redirect sys.stdout and sys.stderr to capture print() statements
    sys.stdout = PrintLogger(logging.getLogger("STDOUT"), logging.INFO, sys.__stdout__)
    sys.stderr = PrintLogger(logging.getLogger("STDERR"), logging.ERROR, sys.__stderr__)

import logging
import sys
import json


class JsonFormatter(logging.Formatter):
    def format(self, record):
        # Start with the standard metadata
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "level": record.levelname,
            "event": record.msg
        }

        
        return json.dumps(log_entry)




def setup_logging():
    # Create a base formatter
    approach_handler = logging.FileHandler('approach_history.json')
    approach_handler.setFormatter(JsonFormatter())
    approach_logger = logging.getLogger('approach')
    approach_logger.addHandler(approach_handler)
    approach_logger.setLevel(logging.INFO)
    approach_logger.propagate = False  # Prevent approach logs from cluttering the console
    # 2. Telemetry Logger (JSON for Plotting)
    telemetry_handler = logging.FileHandler('string_metrics.json')
    telemetry_handler.setFormatter(JsonFormatter())
    telemetry_logger = logging.getLogger('telemetry')
    telemetry_logger.addHandler(telemetry_handler)
    telemetry_logger.setLevel(logging.INFO)
    # Prevent telemetry from cluttering the console
    telemetry_logger.propagate = False 


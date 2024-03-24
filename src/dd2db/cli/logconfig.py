import logging
import time

DEFAULT_LOG_FORMAT = "%(created)d.%(msecs)03d|%(asctime)s|%(levelname)s|%(name)s|%(funcName)s|%(message)s"


def logging_config(log_format, log_level, log_file):
    logging.Formatter.converter = time.gmtime
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid Python log level: {log_level}")

    if log_file:
        logging.basicConfig(
            level=numeric_level,
            filename=log_file,
            format=log_format,
            datefmt="%Y/%m/%d %I:%M:%S%z %Z %p",
        )
    else:
        logging.basicConfig(
            level=numeric_level,
            format=log_format,
            datefmt="%Y/%m/%d %I:%M:%S%z %Z %p",
        )

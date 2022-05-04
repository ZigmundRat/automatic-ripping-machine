#!/usr/bin/env python3
"""
Main code for setting up the logging for all of A.R.M
Also triggers CD identification
"""
# set up logging

import os
import logging
import logging.handlers
import time

from arm.config.config import cfg


def setup_logging(job):
    """Setup logging and return the path to the logfile for
    redirection of external calls
    We need to return the full logfile path but set the job.logfile to just the filename
    """
    # This isn't catching all of them
    if job.label == "" or job.label is None:
        if job.disctype == "music":
            logfile = job.logfile = job.identify_audio_cd()
        else:
            logfile = "empty.log"
        # set a logfull for empty.log and music_cd.log
        logfull = os.path.join(cfg['LOGPATH'], logfile)
    else:
        logfile = job.label + ".log"
        new_log_file = f"{job.label}_{round(time.time() * 100)}.log"
        temp_log_full = os.path.join(cfg['LOGPATH'], logfile)
        logfile = new_log_file if os.path.isfile(temp_log_full) else logfile
        # If log already exist use the new_log_file
        logfull = os.path.join(cfg['LOGPATH'], new_log_file) if os.path.isfile(temp_log_full) \
            else os.path.join(cfg['LOGPATH'], str(job.label) + ".log")
        job.logfile = logfile
    clean_loggers()
    # Debug formatting
    if cfg['LOGLEVEL'] == "DEBUG":
        logging.basicConfig(filename=logfull,
                            format='[%(asctime)s] %(levelname)s ARM: %(module)s.%(funcName)s %(message)s',
                            datefmt=cfg['DATE_FORMAT'], level=cfg['LOGLEVEL'])
    else:
        logging.basicConfig(filename=logfull, format='[%(asctime)s] %(levelname)s ARM: %(message)s',
                            datefmt=cfg['DATE_FORMAT'], level=cfg['LOGLEVEL'])

    # This stops apprise spitting our secret keys when users posts online
    logging.getLogger("apprise").setLevel(logging.WARN)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)

    # Return the full logfile location to the logs
    return logfull


def clean_loggers():
    """
    try to catch any old loggers and remove them
    :return: None
    """
    try:
        logging.getLogger().removeHandler(logging.getLogger().handlers[0])
    except IndexError:
        return


def clean_up_logs(logpath, loglife):
    """
    Delete all log files older than {loglife} days\n
    if {loglife} is 0 don't delete anything\n
    :param logpath: path of log files\n
    :param loglife: days to let logs live\n
    :return:
    """
    if loglife < 1:
        logging.info("loglife is set to 0. Removal of logs is disabled")
        return False
    now = time.time()
    logging.info(f"Looking for log files older than {loglife} days old.")

    for filename in os.listdir(logpath):
        fullname = os.path.join(logpath, filename)
        if fullname.endswith(".log") and os.stat(fullname).st_mtime < now - loglife * 86400:
            logging.info(f"Deleting log file: {filename}")
            os.remove(fullname)
    return True


def create_logger(app_name, log_level=logging.DEBUG, stdout=True, syslog=False, file=False):
    """
    From: https://gist.github.com/danielkraic/a1657f19bad9c158cbf9532e1ed1503b\n
    Create logging object with logging to syslog, file and stdout\n
    Will log to `/var/log/arm.log`\n
    :param app_name: app name
    :param log_level: logging log level
    :param stdout: log to stdout
    :param syslog: log to syslog
    :param file: log to file
    :return: logging object
    """
    # disable requests logging
    # logging.getLogger("requests").setLevel(logging.ERROR)
    # logging.getLogger("urllib3").setLevel(logging.ERROR)

    # create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)

    # set log format to handlers
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s ARM: %(module)s.%(funcName)s %(message)s')

    if file:
        # create file logger handler
        file_handler = logging.FileHandler('/home/arm/logs/arm.log')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if syslog:
        # create syslog logger handler
        stream_handler = logging.handlers.SysLogHandler(address='/dev/log')
        stream_handler.setLevel(log_level)
        stream_file = logging.Formatter('%(name)s: %(message)s')
        stream_handler.setFormatter(stream_file)
        logger.addHandler(stream_handler)

    if stdout:
        # create stream logger handler
        stream_print = logging.StreamHandler()
        stream_print.setLevel(log_level)
        stream_print.setFormatter(formatter)
        logger.addHandler(stream_print)

    return logger

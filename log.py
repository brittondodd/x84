"""
Logging handler for x/84 BBS, http://github.com/jquast/x84
"""
import logging
import copy

_last_line = ('', '', '', '', '', '')

FMT_TXT = '%(levelname)s' \
        '%(space)s%(filename)s%(colon)s%(lineno)s' \
        '%(space)s%(processName)s%(threadName)s' \
        '%(sep)s%(prefix)s%(message)s'


def get_stderr(level=logging.INFO):
    """
    Return log handler suitable for logging to sys.stderr.
    """
    import sys
    import blessings
    term = blessings.Terminal(stream=sys.stderr, force_styling=True)
    stderr_format = logging.Formatter (FMT_TXT)
    wscons = ColoredConsoleHandler(term)
    wscons.setFormatter (stderr_format)
    level = level if level != None else logging.INFO # default
    if level != None:
        wscons.setLevel(level) # default level
    return wscons


def line_cmp(record):
    """ Return tuple of levelname, filename, lineno, and threadName. """
    return (record.levelname, record.filename,
            record.lineno, record.threadName,
            record.processName)


def line_blank(record):
    """ Blank out various redundant fields of a record. """
    record.colon = record.space = record.sep = record.levelname \
      = record.filename = record.lineno = record.threadName \
      = record.processName = ''
    return record


def skip_repeat_line1(record):
    """
    If this record is very similar to the last record, blank out the
    redundant bits. This especially makes tracebacks & etc. more readable.
    """
    #pylint: disable=W0603
    #        Using the global statement
    global _last_line
    cur_line1 = line_cmp(record)
    if cur_line1 == _last_line \
    and _last_line[0].lower().strip() == 'error':
        # avoid repeating unnecessarily,
        record = line_blank(record)
    _last_line = cur_line1
    return record


class ColoredConsoleHandler(logging.StreamHandler):
    """
    A stream handler that colors the levelname and avoids
    printing too much processName, Info, Time, etc. for
    very long errors such as traceback (last_line global)
    """

    def __init__(self, term):
        self.term = term
        logging.StreamHandler.__init__ (self)

    def color_levelname (self, record):
        """ Modify levelname field to include terminal color sequences.  """
        record.levelname = '%s%s%s' % \
            (self.term.bold_red if record.levelno >= 50 else \
             self.term.bold_red if record.levelno >= 40 else \
             self.term.bold_yellow if record.levelno >= 30 else \
             self.term.bold_white if record.levelno >= 20 else \
             self.term.yellow, record.levelname.title(), self.term.normal)
        return record

    def transform(self, src_record):
        """ Return a modified log record """
        src_record.colon = ':'
        src_record.space = ' '
        src_record.sep = ' - '
        src_record.prefix = ''
        return \
          (self.color_levelname \
            (skip_repeat_line1 \
                  (src_record)))

    def emit(self, src_record):
        """ Emit record to console """
        # transform
        dst_record = self.transform \
            (copy.copy(src_record))

        # emit to console
        logging.StreamHandler.emit \
          (self, dst_record)

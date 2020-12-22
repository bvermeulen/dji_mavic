from functools import wraps
import logging
import time
'''  plogger is a module with logging tools which can be either called directly
     or to be used as decorators

     timed - logs the time duration of a decorated function
     func_args - logs the arguments (*args, **kwargs) and results of a
                 decorated function

'''
class Logger:

    @classmethod
    def set_logger(cls, log_file, logformat, level):
        ''' set the logger parameters
        '''
        cls.logger = logging.getLogger(__name__)
        formatter = logging.Formatter(logformat)
        cls.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        cls.logger.addHandler(file_handler)

        return cls.logger


    @classmethod
    def getlogger(cls):
        return cls.logger


def parameterized(decorator_func):
    def layer(*args, **kwargs):
        def replace_func(func):
            return decorator_func(func, *args, **kwargs)
        return replace_func
    return layer


@parameterized
def timed(func, logger, print_log=False):
    """This decorator logs the execution time for the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        log_str = f'==> {func.__name__} ran in {round(end - start, 3)} s'
        logger.info(log_str)
        if print_log:
            print(log_str)
        return result
    return wrapper


@parameterized
def func_args(func, logger):
    """This decorator logs the arguments for the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        logger.info('\n==>{0}: arguments: {1}, key arguments: {2}\n'
                    '==>{0}: result: {3}'.
                    format(func.__name__, args, kwargs, result))
        return result
    return wrapper

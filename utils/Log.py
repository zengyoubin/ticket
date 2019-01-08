import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

fh = logging.FileHandler('./logs/app.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


class Log(object):

    # def __print(msg, color):
    #     if type(msg) == str:
    #         print(color + msg + Fore.RESET)
    #     else:
    #         print(color)
    #         print(msg)
    #         print(Fore.RESET)
    @staticmethod
    def debug(msg):
        logger.info(msg)
        # Log.__print(msg, Fore.BLUE)

    @staticmethod
    def info(msg):
        logger.info(msg)
        # Log.__print(msg, Fore.GREEN)

    @staticmethod
    def warning(msg):
        logger.warning(msg)
        # Log.__print(msg, Fore.YELLOW)

    @staticmethod
    def error(msg):
        logger.error(msg)
        # Log.__print(msg, Fore.RED)


if __name__ == '__main__':
    Log.debug('123')

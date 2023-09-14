import logging

logger = logging
logger.basicConfig(filename='app.log', filemode='a',format='%(asctime)s | %(filename)s | %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG)
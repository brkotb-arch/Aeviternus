# Ядро Дипа. Это его сердце.
import logging
import os

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/dip.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger('deep_core')
logger.info("Ядро Дипа активно.")
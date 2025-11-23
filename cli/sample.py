import logging
import time

logging.basicConfig(level=logging.INFO)
for i in range(500):
    print("Gotcha")
    time.sleep(0.01)

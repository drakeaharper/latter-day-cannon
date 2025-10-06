#!/usr/bin/env python3
"""
Simple parallel launcher - starts all remaining scrapers
"""

import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def launch_scrapers():
    """Launch all remaining scrapers in parallel"""

    # Check current NT progress
    logger.info("New Testament already running...")

    # Start Book of Mormon
    logger.info("Starting Book of Mormon scraping...")
    bofm_process = subprocess.Popen(['python3', 'scrape_bofm.py'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

    # Start Old Testament
    logger.info("Starting Old Testament scraping...")
    ot_process = subprocess.Popen(['python3', 'scrape_ot.py'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

    logger.info("All scrapers launched!")
    logger.info(f"Book of Mormon PID: {bofm_process.pid}")
    logger.info(f"Old Testament PID: {ot_process.pid}")

    logger.info("Monitor progress with:")
    logger.info("- ls scriptures/*/[*].md | wc -l")
    logger.info("- tail -f nt_scraping.log")
    logger.info("- tail -f bofm_scraping.log")
    logger.info("- tail -f ot_scraping.log")

if __name__ == "__main__":
    launch_scrapers()
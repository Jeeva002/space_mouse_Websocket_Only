#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os

class LogManagement:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        # Open the file in append mode and store the file object
        self.file = open(self.log_file_path, 'a')

    def _write_log(self, level, msg):
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        milliseconds = now.microsecond // 1000  # Convert microseconds to milliseconds
        self.file.write(f'{timestamp}.{milliseconds:03d} - {level} - {msg}\n')
        self.file.flush()  # Ensure the message is written to disk

    def writeRawData(self, msg):
        self._write_log('rawData', msg)

    def writeBeforeWebsocket(self, msg):
        self._write_log('BeforeWebsocket', msg)

    def writeAfterWebsocket(self, msg):
        self._write_log('AfterWebsocket', msg)

    def writeBeforeRos(self, msg):
        self._write_log('BeforePublishingToRos', msg)

    def writeAfterRos(self, msg):
        self._write_log('AfterRos', msg)

    def robotTime(self, msg):
        self._write_log('robotExecution', msg)

    def close(self):
        # Close the file when done
        self.file.close()

# Determine the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize the log management with a relative file path
log_file_path = os.path.join(script_dir, 'collectedData.txt')
log_management = LogManagement(log_file_path)

# Example usage
# log_management.writeRawData('This is a raw data message')
# log_management.writeBeforeWebsocket('Preparing for websocket')
# log_management.writeAfterWebsocket('Websocket communication complete')
# log_management.writeBeforeRos('Preparing to publish to ROS')
# log_management.writeAfterRos('ROS publishing complete')
# log_management.robotTime('Robot execution started')

# Remember to close the file when done
# log_management.close()

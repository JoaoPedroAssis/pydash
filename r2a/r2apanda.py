# -*- coding: utf-8 -*-
"""
@author: João Pedro Assis (17/0146367)
@author: Jonas de Souza (18/0076272)

@description: PyDash Project

This is the Probe AND Adapt algorithm

the quality list is obtained with the parameter of handle_xml_response() method and the choice
is made inside of handle_segment_size_request(), before sending the message down.

"""

from r2a.ir2a import IR2A
from player.parser import *
from time import perf_counter as get_curr_time

class R2APanda(IR2A):

    def __init__(self, id):
        IR2A.__init__(id)

        # Throughputs
        self.throughputs = []
        self.target_throughputs = []
        self.filtered_throughputs = []

        # Time mesurements
        self.request_time = 0
        self.inter_request_time = []

        # Quality List
        self.qi = []

        self.segment_duration = 1
        self.selected_qi

        self.min_buffer_size = 20

    def handle_xml_request(self, msg):

        self.request_time = get_curr_time()
        self.send_down(msg)


    def handle_xml_response(self, msg):
        # Get quality list from message payload
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        request_duration = get_curr_time() - self.request_time
        
        # If throughput list is empty, initialize values
        if not self.throughputs:
            bitrate = msg.get_bit_lenght() / request_duration

            self.throughputs.append(bitrate)
            self.target_throughputs.append(bitrate)
            self.filtered_throughputs.append(bitrate)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        pass

    def handle_segment_size_response(self, msg):
        pass

    def initialize(self):
        pass

    def finalization(self):
        pass


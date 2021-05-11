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
import sys

class R2APanda(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)

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
        self.selected_qi = []

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
            bitrate = msg.get_bit_length() / request_duration

            self.throughputs.append(bitrate)
            self.target_throughputs.append(bitrate)
            self.filtered_throughputs.append(bitrate)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = get_curr_time()
        x = 0
        w = 0.35 * 1000000 # incremento de prova do bitrate
        k = 0.14  # taxa de convergência de prova
        E = 0.15 # margem de multiplicação
        alfa = 0.2 # taxa de convergência de suavização do throughput alvo
        limit_calc_throughput = False

        if len(sys.argv) >= 2: # permite usar o w como um argumento
            w = float(sys.argv[1]) * 1000000
        
        if len(sys.argv) >= 4: # permite definir se será usado um limitador para o throughput alvo em relação ao real
            limit_calc_throughput = True

        y = self.throughputs[0]
        if len(self.throughputs) == 1: # inicialização o throughput alvo com o valor obtido ao transferir o arquivo mpd
            x = self.throughputs[0]
        else:

            x = abs(
                (w - max((0, self.target_throughputs[-1] - self.throughputs[-1] + w))) * 
                k *
                self.inter_request_time[-1] + self.target_throughputs[-1]
            ) 

            # Limits the maximum throughput to 4 times the value
            if (self.whiteboard.get_amount_video_to_play() < self.min_buffer_size and
                x > 4 * self.throughputs[-1] and
                limit_calc_throughput):
                # limitador para o valor máximo do throughput, está definido como 4x o valor do real
                x = 4 * self.throughputs[-1]
                y = 4 * self.throughputs[-1]
            else:

                y = abs(
                    -alfa * 
                    (self.filtered_throughputs[-1] - x) * 
                    self.inter_request_time[-1] + self.filtered_throughputs[-1]
                )

            # Salves target and filtered throughputs
            self.target_throughputs.append(x)
            self.filtered_throughputs.append(y)

        # Implements the algorithms deadzone

        selected_rup = self.qi[0]
        selected_rdown = self.qi[0]

        rup = y * (1 - E)
        rdown = y

        for i in self.qi:
            if rup > i:
                selected_rup = i
            if rdown > i:
                selected_rdown = i

        if len(self.selected_qi) == 0:
            self.selected_qi.append(selected_rdown)
        elif self.selected_qi[-1] < selected_rup:
            self.selected_qi.append(selected_rup)
        elif selected_rup <= self.selected_qi[-1] < selected_rdown:
            self.selected_qi.append(self.selected_qi[-1])
        else:
            self.selected_qi.append(selected_rdown)


        # Selects the last added quality value after deadzone 
        msg.add_quality_id(self.selected_qi[-1])
        self.send_down(msg)
        

    def handle_segment_size_response(self, msg):
        beta = 0.2

        if len(sys.argv) >= 3:
            self.min_buffer_size = float(sys.argv[2])

        B = self.whiteboard.get_amount_video_to_play()
        if len(self.throughputs) == 1:
            B = (1 - msg.get_bit_length() / self.target_throughputs[0]) * \
            self.segment_duration / beta + self.min_buffer_size

        target_inter_time = msg.get_bit_length() * self.segment_duration / \
        self.filtered_throughputs[-1] + beta * (B - self.min_buffer_size)

        inter_time = get_curr_time() - self.request_time

        self.inter_request_time.append(max((target_inter_time, inter_time)))
        self.throughputs.append(msg.get_bit_length() * self.segment_duration / inter_time)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass


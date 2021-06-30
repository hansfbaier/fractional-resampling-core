#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: CERN-OHL-W-2.0

from nmigen import *
from nmigen.lib.fifo import SyncFIFO
from nmigen_library.stream import StreamInterface
from .filterbank import Filterbank

class FractionalResampler(Elaboratable):
    def __init__(self, *, input_samplerate: int,
                 upsample_factor: int, downsample_factor: int,
                 filter_instances = 3,
                 filter_cutoff: int = 20000,
                 bitwidth: int = 16) -> None:
        self.signal_in  = StreamInterface(payload_width=bitwidth)
        self.signal_out = StreamInterface(payload_width=bitwidth)

        self.input_samplerate = input_samplerate
        self.upsample_factor = upsample_factor
        self.downsample_factor = downsample_factor
        self.filter_instances = filter_instances
        self.filter_cutoff = filter_cutoff
        self.bitwidth = bitwidth

    def elaborate(self, platform) -> Module:
        m = Module()

        m.submodules.antialiasingfilter = antialiasingfilter = \
            Filterbank(self.filter_instances,
                       self.input_samplerate * self.upsample_factor,
                       bitwidth=self.bitwidth,
                       cutoff_freq=self.filter_cutoff,
                       filter_order=2)

        m.submodules.downsamplefifo = downsamplefifo = \
            SyncFIFO(width=self.bitwidth, depth=self.upsample_factor)

        # upsampling
        upsampled_signal  = Signal.like(self.signal_in.payload)
        upsample_counter  = Signal(range(self.upsample_factor))
        input_data        = Signal.like(self.signal_in.payload)
        input_ready       = Signal()
        input_valid       = Signal()

        m.d.comb += [
            self.signal_in.ready.eq(input_ready),
            input_valid.eq(self.signal_in.valid),
            input_ready.eq((upsample_counter == 0) & (downsamplefifo.w_rdy)),
            input_data.eq(self.signal_in.payload),
            antialiasingfilter.signal_in.eq(upsampled_signal),
            antialiasingfilter.enable_in.eq(upsample_counter > 0),
            downsamplefifo.w_en.eq(downsamplefifo.w_rdy & antialiasingfilter.enable_in),
        ]

        with m.If(input_valid & input_ready):
            m.d.comb += [
                upsampled_signal.eq(self.signal_in.payload),
                antialiasingfilter.enable_in.eq(1),
            ]
            m.d.sync += upsample_counter.eq(self.upsample_factor - 1)
        with m.Elif(upsample_counter > 0):
            m.d.comb += upsampled_signal.eq(0)
            m.d.sync += upsample_counter.eq(upsample_counter - 1)

        # downsampling and output
        downsample_counter = Signal(range(self.downsample_factor))

        m.d.comb += [
            downsamplefifo.w_data.eq(antialiasingfilter.signal_out),
            self.signal_out.valid.eq(downsamplefifo.r_rdy),
        ]

        with m.If(downsamplefifo.r_rdy & self.signal_out.ready):
            m.d.comb += downsamplefifo.r_en.eq(1)

            with m.If(downsample_counter == 0):
                m.d.sync += downsample_counter.eq(self.downsample_factor - 1)
                m.d.comb += [
                    self.signal_out.payload.eq(downsamplefifo.r_data),
                    self.signal_out.valid.eq(1),
                ]
            with m.Else():
                m.d.sync += downsample_counter.eq(downsample_counter - 1)
                m.d.comb += self.signal_out.valid.eq(0)

        with m.Else():
            m.d.comb += [
                downsamplefifo.r_en.eq(0),
                self.signal_out.valid.eq(0),
            ]

        return m
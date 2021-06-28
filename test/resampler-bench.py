#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: MIT

import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick
from resampler.resampler import FractionalResampler

if __name__ == "__main__":
    dut = FractionalResampler(input_samplerate=56000, upsample_factor=6, downsample_factor=7, filter_cutoff=20000)
    sim = Simulator(dut)

    def sync_process():
        for _ in range(10): yield Tick()
        yield dut.signal_out.ready.eq(1)
        for i in range(600):
            yield Tick()
            if i < 250:
                if i % 6 == 0:
                    yield dut.signal_in.valid.eq(1)
                    yield dut.signal_in.payload.eq(2**14)
                else:
                    yield dut.signal_in.valid.eq(0)
            else:
                if i % 6 == 0:
                    yield dut.signal_in.valid.eq(1)
                    yield dut.signal_in.payload.eq(-2**14)
                else:
                    yield dut.signal_in.valid.eq(0)

    sim.add_sync_process(sync_process)
    sim.add_clock(10e-9)
    with sim.write_vcd('resampler.vcd', traces=[dut.signal_in.payload, dut.signal_in.valid, dut.signal_out.valid, dut.signal_out.payload]):
        sim.run()

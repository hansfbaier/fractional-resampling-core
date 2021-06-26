#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: MIT

import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick
from resampler.fixedpointiirfilter import FixedPointIIRFilter

if __name__ == "__main__":
    dut = FixedPointIIRFilter(336000)
    sim = Simulator(dut)

    def sync_process():
        yield dut.enable_in.eq(1)
        for _ in range(20): yield Tick()
        yield dut.signal_in.eq(2**16)
        for _ in range(100): yield Tick()
        yield dut.signal_in.eq(-2**16)
        for _ in range(5): yield Tick()
        yield dut.enable_in.eq(0)
        for _ in range(20): yield Tick()
        yield dut.enable_in.eq(1)
        for _ in range(60): yield Tick()
        yield dut.signal_in.eq(0)
        for _ in range(100): yield Tick()
        for i in range(10):
           yield dut.signal_in.eq(32768)
           yield Tick()
           yield dut.signal_in.eq(0)
           yield Tick()
           for _ in range(6): yield Tick()
           yield dut.signal_in.eq(-32768)
           yield Tick()
           yield dut.signal_in.eq(0)
           yield Tick()
           for _ in range(6): yield Tick()

    sim.add_sync_process(sync_process)
    sim.add_clock(10e-9)
    with sim.write_vcd('fixedpointiirfilter.vcd', traces=[dut.signal_in, dut.signal_out]):
        sim.run()

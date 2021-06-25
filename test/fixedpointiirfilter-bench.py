#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: MIT

import sys
sys.path.append('.')

from nmigen.sim import Simulator, Tick
from resampler.antialiasingfilter import AntialiasingFilter

if __name__ == "__main__":
    dut = AntialiasingFilter(336000)
    sim = Simulator(dut)

    def sync_process():
        for _ in range(20): yield Tick()
        yield dut.signal_in.eq(-32767)
        yield Tick()
        yield Tick()
        for _ in range(5000): yield Tick()

    sim.add_sync_process(sync_process)
    sim.add_clock(10e-9)
    with sim.write_vcd('antialiasingfilter.vcd', traces=[dut.signal_in, dut.signal_out]):
        sim.run()

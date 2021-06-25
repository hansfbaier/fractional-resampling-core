#!/usr/bin/env python3
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
        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()

    sim.add_sync_process(sync_process)
    sim.add_clock(1e-6)
    with sim.write_vcd('antialiasingfilter.vcd', traces=[dut.audio_in, dut.audio_out]):
        sim.run()

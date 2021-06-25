#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: MIT
from nmigen import *

class AntialiasingFilter(Elaboratable):
    def __init__(self) -> None:
        self.audio_in = Signal(signed(16))
        self.audio_out = Signal(signed(16))

    def elaborate(self, platform):
        m = Module()

        # the recursive coefficiens
        a_f40 = [2588524, 15531147, 38827867, 51770490, 38827867, 15531147, 2588524]

        m.d.sync += [
            self.p.eq(self.a * self.b)
        ]

        return m
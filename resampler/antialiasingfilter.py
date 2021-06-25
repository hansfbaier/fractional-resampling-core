#!/usr/bin/env python3
#
# Copyright (c) 2021 Hans Baier <hansfbaier@gmail.com>
# SPDX-License-Identifier: MIT

from scipy import signal
from nmigen import *
from pprint import pformat

class AntialiasingFilter(Elaboratable):
    def __init__(self, samplerate, bitwidth=16, cutoff_freq=20000) -> None:
        self.audio_in  = Signal(signed(bitwidth))
        self.audio_out = Signal(signed(bitwidth))
        self.bitwidth = bitwidth

        filter_order = 5
        num_coefficients = filter_order + 1
        nyquist_frequency = samplerate * 0.5
        cutoff = cutoff_freq / nyquist_frequency
        allowed_ripple = 1.0 # dB
        b, a = signal.cheby1(filter_order, allowed_ripple, cutoff, btype='lowpass', output='ba')

        # convert to fixed point representation
        self.fraction_bits = fraction_bits = 24
        assert bitwidth < fraction_bits, f"Bitwidth must not exceed {fraction_bits}"
        self.b = b_fp = [int(x * 2**fraction_bits) for x in b]
        self.a = a_fp = [int(x * 2**fraction_bits) for x in a]
        print(f"{filter_order}-order Chebyshev-Filter cutoff: {cutoff * nyquist_frequency} max ripple: {allowed_ripple}dB\n")
        print(f"b: {pformat(b)}")
        print(f"a: {pformat(a)}")
        print(f"b ({bitwidth}.{fraction_bits} fixed point): {b_fp}")
        print(f"a ({bitwidth}.{fraction_bits} fixed point): {a_fp}\n")
        assert len(b_fp) == len(a_fp)

        def conversion_error(coeff, fp_coeff):
            val = 2**(bitwidth - 1)
            fp_product = fp_coeff * val
            fp_result = fp_product >> fraction_bits
            fp_error = fp_result - (coeff * val)
            return fp_error

        conversion_errors_b = [abs(conversion_error(b[i], b_fp[i])) for i in range(num_coefficients)]
        conversion_errors_a = [abs(conversion_error(a[i], a_fp[i])) for i in range(num_coefficients)]
        print("b, fixed point conversion errors: {}".format(conversion_errors_a))
        print("a, fixed point conversion errors: {}".format(conversion_errors_b))
        for i in range(num_coefficients):
            assert (conversion_errors_b[i] < 1.0)
            assert (conversion_errors_a[i] < 1.0)

    def elaborate(self, platform):
        m = Module()

        # see https://en.wikipedia.org/wiki/Infinite_impulse_response
        # and https://en.wikipedia.org/wiki/Digital_filter
        # except that the negative signs in the recursive section seem
        # to be already baked into the coefficients
        # b are the input coefficients
        # a are the recursive (output) coefficients
        n = len(self.a)
        width = self.bitwidth + self.fraction_bits
        b = [Const(n, signed(width)) for n in self.b]
        # the filter design tool generates a '1.0' coefficient for a_n, which we don't need
        a = [Const(n, signed(width)) for n in self.a[1:]]

        # we use the array indices flipped, ascending from zero
        # so x[0] is x_n, x[1] is x_n-1, x[2] is x_n-2 ...
        # in other words: higher indices are past values, 0 is most recent
        x = Array(Signal(signed(width), name=f"x{i}") for i in range(n))
        # because y[0] would be the output value, the y array is shifted by one:
        # y[0] is y_n-1, y[1] is y_n-2, y[2] is y_n-3
        # but the signals are still named 'right' to be easy to understnad
        # in the waveform viewer
        y = Array(Signal(signed(width), name=f"y{i+1}") for i in range(n - 1))

        m.d.comb += self.audio_out.eq(
              sum([((x[i] * b[i]) >> self.fraction_bits) for i in range(n)])
            - sum([((y[i] * a[i]) >> self.fraction_bits) for i in range(n - 1)]))

        m.d.sync += [x[i + 1].eq(x[i]) for i in range(n - 1)]
        m.d.sync += [y[i + 1].eq(y[i]) for i in range(n - 2)]
        m.d.sync += x[0].eq(self.audio_in)
        m.d.sync += y[0].eq(self.audio_out)

        return m


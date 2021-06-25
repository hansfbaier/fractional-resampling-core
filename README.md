# fractional-resampling-core

This is a FPGA implementation of a fractional resampler for audio signals.
Resampling is achieved by:
1. Upsampling the signal by the multiplier
2. Anti-aliasing filtering (6-th order Chebyshev). IIR filter for minimal latency.
3. Downsampling the signal by the divider

# fractional-resampling-core

This is a FPGA implementation of a fractional resampler for audio signals.
Resampling is achieved by:
1. Upsampling the signal by the multiplier
2. Anti-aliasing filter (Choice of FIR, IIR)
3. Downsampling the signal by the divider

# status
The code has been tested working on the FPGA

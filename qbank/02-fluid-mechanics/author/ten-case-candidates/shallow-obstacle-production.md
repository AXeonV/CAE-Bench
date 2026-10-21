# Native closed shallow obstacle wave

A finite adapter targets only frozen 2.9.2 case06. The installed OpenCFD v2512 shallowWaterFoam advances inviscid shallow water momentum and depth with bed slope. This case has zero drag, flat bed, resting positive-depth initial data and closed impermeable slip walls, including the rectangular obstacle hole. Rotation is disabled. No source terms or PDE implementation are added.

The existing block mesh writer preserves the actual rectangular cutout. Its native quads are split into the public triangular mesh. Initial depth is evaluated at those public nodes, interpreted as P1, then integrated exactly to each native quad mean; initial momentum is zero. The finite native run uses dt=.0005 to end=.5 with 1000 steps; all requested times coincide with stored frames. Raw depth must remain finite and positive at requested frames.

This stage intentionally stops at native_complete_pending_conversion. A complete self-contained problem/input and real-node output recovery must be assembled before counting a candidate. No accuracy validation, HF upload or benchmark is performed. Per-attempt commands, source identity, script hashes, native logs and subsequent handoff are maintained on Titan.

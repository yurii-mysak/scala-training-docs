"""
harness — I/O + parsing scaffold for the 90-minute laptop round.

Modules:
    io_utils  -- read/write stdin & files; resolve_input() makes the channel a non-issue
    records   -- typed field coercion, tolerant CSV splitting, a fixed-schema record factory
    runner    -- the argparse CLI scaffold; main(solve) wires everything together

You should not need to edit this package during the round itself — see ../solution.py
and ../USAGE.md.
"""
__all__ = ["io_utils", "records", "runner"]
__version__ = "1.0.0"

"""Memory-map the members of an UNCOMPRESSED .npz (np.savez) without loading them into RAM.

research/bdi/stack1009/data/base.npz is 3.5 GB of float32 columns stored uncompressed; mapping them keeps this
workstream inside the shared machine's RAM budget (swarm1010/RULES.md). Educational only - not financial advice.
"""
from __future__ import annotations

import struct
import zipfile
from pathlib import Path

import numpy as np


def npz_memmap(path: str | Path) -> dict[str, np.memmap]:
    path = Path(path)
    out = {}
    with zipfile.ZipFile(path) as z, open(path, "rb") as fh:
        for info in z.infolist():
            if info.compress_type != zipfile.ZIP_STORED:
                raise ValueError(f"{info.filename} is compressed; cannot memory-map")
            fh.seek(info.header_offset)
            hdr = fh.read(30)
            n_name, n_extra = struct.unpack("<HH", hdr[26:30])
            data_off = info.header_offset + 30 + n_name + n_extra
            fh.seek(data_off)
            version = np.lib.format.read_magic(fh)
            if version == (1, 0):
                shape, fortran, dtype = np.lib.format.read_array_header_1_0(fh)
            else:
                shape, fortran, dtype = np.lib.format.read_array_header_2_0(fh)
            off = fh.tell()
            name = info.filename[:-4] if info.filename.endswith(".npy") else info.filename
            out[name] = np.memmap(path, dtype=dtype, mode="r", offset=off, shape=shape,
                                  order="F" if fortran else "C")
    return out

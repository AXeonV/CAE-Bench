"""Standard HDF5 array storage; semantics belong to problem.json."""
from pathlib import Path
import re

import h5py
import numpy as np

NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def read_arrays(path):
    """Read a self-contained, flat HDF5 payload into independent ndarrays.

    Use h5py.File directly for application-specific slicing or incremental writes.
    No casting, reshaping or sorting is performed here.
    """
    path = Path(path)
    if path.suffix != ".h5":
        raise ValueError("Array payload path must end in .h5.")
    with h5py.File(path, "r") as source:
        if source.attrs:
            raise ValueError("HDF5 attributes are not part of the data protocol; use problem.json.")
        arrays, objects = {}, set()
        for key in source:
            if not NAME.fullmatch(key) or not isinstance(source.get(key, getlink=True), h5py.HardLink):
                raise ValueError("Expected named root datasets, without soft or external links.")
            data = source[key]
            if not isinstance(data, h5py.Dataset) or data.shape is None:
                raise ValueError(f"{key}: expected a dataset with a non-null dataspace.")
            address = h5py.h5o.get_info(data.id).addr
            if address in objects:
                raise ValueError(f"{key}: dataset aliases are not allowed.")
            objects.add(address)
            if data.attrs or data.is_virtual or data.external:
                raise ValueError(f"{key}: attributes, virtual datasets and external storage are not allowed.")
            # These lossless filters ship with the HDF5 library itself.
            properties = data.id.get_create_plist()
            if any(properties.get_filter(i)[0] not in (1, 2, 3)
                   for i in range(properties.get_nfilters())):
                raise ValueError(f"{key}: only gzip, shuffle and Fletcher32 filters are allowed.")
            if data.dtype.fields or data.dtype.kind not in "biufc":
                raise ValueError(f"{key}: expected a numeric or boolean dataset.")
            if h5py.check_enum_dtype(data.dtype) is not None:
                raise ValueError(f"{key}: only the standard FALSE/TRUE boolean enum is allowed.")
            if data.dtype.kind == "b" and data.id.get_type().get_super().get_sign() != h5py.h5t.SGN_2:
                raise ValueError(f"{key}: boolean enum requires a signed 8-bit integer base.")
            value = np.asarray(data[()])
            if value.dtype.kind == "b" and np.any(value.view("u1") > 1):
                raise ValueError(f"{key}: boolean enum values must be 0 or 1.")
            arrays[key] = value
        return arrays


def write_hdf5(path, arrays, *, compression=None):
    """Write a mapping of dataset names to ndarrays using h5py, without casting.

    This storage helper does not replace validate-input/validate-output.
    """
    path = Path(path)
    if path.suffix != ".h5":
        raise ValueError("Array payload path must end in .h5.")
    if compression not in (None, "gzip"):
        raise ValueError("Use no compression or the standard HDF5 gzip filter.")
    for key, value in arrays.items():
        if not isinstance(key, str) or not NAME.fullmatch(key):
            raise ValueError(f"Invalid root dataset name: {key!r}")
        if not isinstance(value, np.ndarray):
            raise TypeError("Pass ndarrays; storage does not infer dtype or shape.")
        if value.dtype.fields or value.dtype.kind not in "biufc":
            raise TypeError("HDF5 protocol arrays must be numeric or boolean.")
        if value.dtype.kind == "b" and np.any(value.view("u1") > 1):
            raise ValueError("Boolean enum values must be encoded as 0 or 1.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w", libver="earliest") as target:
        for key, value in arrays.items():
            target.create_dataset(key, data=value,
                                  compression=compression if value.ndim else None)

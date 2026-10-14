"""HDF5 interoperability and the protocol's deliberately small storage subset."""
from pathlib import Path
import tempfile
import unittest

import h5py
import numpy as np

from caeoj.storage import write_hdf5
from caeoj.validation import ContractError, read_hdf5


class HDF5Tests(unittest.TestCase):
    def setUp(self):
        runs = Path(__file__).resolve().parents[1] / 'runs'
        runs.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=runs)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'payload.h5'

    def reject(self, create):
        with h5py.File(self.path, 'w') as data:
            create(data)
        with self.assertRaises(ContractError) as caught:
            read_hdf5(self.path)
        self.assertEqual(caught.exception.report['errors'][0]['code'], 'E_HDF5')

    def test_native_hdf5_datasets_preserve_types_axes_and_values(self):
        arrays = {'ids': np.array([10, 40], dtype='>i8'),
                  'times': np.array([0., .25]),
                  'velocity': np.asfortranarray(np.arange(8., dtype='>f8').reshape(2, 2, 2)),
                  'mask': np.array([[[True], [False]], [[False], [True]]])}
        write_hdf5(self.path, arrays)
        with h5py.File(self.path) as data:
            self.assertEqual(set(data), set(arrays))
            self.assertEqual(data['velocity'][1, 0, 1], 5.)
            self.assertEqual(data['velocity'].dtype, arrays['velocity'].dtype)
            self.assertEqual(data['mask'].id.get_type().get_member_name(0), b'FALSE')
            self.assertEqual(data['mask'].id.get_type().get_member_value(1), 1)
        actual = read_hdf5(self.path)
        self.path.unlink()  # Readers close all handles, including on Windows.
        for name, value in arrays.items():
            np.testing.assert_array_equal(actual[name], value)
            self.assertEqual(actual[name].dtype, value.dtype)

    def test_direct_hyperslab_write_and_lossless_filters(self):
        expected = np.arange(24., dtype='float64').reshape(3, 4, 2)
        with h5py.File(self.path, 'w') as data:
            field = data.create_dataset('velocity', shape=expected.shape, dtype='f8',
                                        chunks=(1, 4, 2), compression='gzip',
                                        shuffle=True, fletcher32=True)
            for t in range(3): field[t, :, :] = expected[t]
        np.testing.assert_array_equal(read_hdf5(self.path)['velocity'], expected)

    def test_lossy_and_nonstandard_filters_are_rejected(self):
        for options in ({'scaleoffset': 3}, {'compression': 'lzf'}):
            with self.subTest(options=options):
                self.reject(lambda data: data.create_dataset('values', data=np.arange(8.), **options))

    def test_external_storage_is_rejected_before_reading(self):
        self.reject(lambda data: data.create_dataset('values', shape=(3,), dtype='f8',
                                                     external=[('absent.raw', 0, 24)]))

    def test_virtual_dataset_is_rejected_before_reading(self):
        layout = h5py.VirtualLayout(shape=(3,), dtype='f8')
        layout[:] = h5py.VirtualSource('absent.h5', 'values', shape=(3,))
        self.reject(lambda data: data.create_virtual_dataset('values', layout))

    def test_null_compound_and_custom_enum_are_rejected(self):
        for dtype in (None, np.dtype([('x', 'f8'), ('y', 'f8')]),
                      h5py.enum_dtype({'COLD': 0, 'HOT': 1}, basetype='i4')):
            def create(data):
                if dtype is None: data.create_dataset('values', dtype='f8')
                else: data.create_dataset('values', shape=(2,), dtype=dtype)
            self.reject(create)

    def test_boolean_enum_cannot_contain_undeclared_values(self):
        self.reject(lambda data: data.create_dataset(
            'mask', data=np.array([0, 2], dtype='i1').view('?')))
        self.reject(lambda data: data.create_dataset(
            'mask', shape=(2,), dtype=h5py.enum_dtype({'FALSE': 0, 'TRUE': 1}, basetype='u1')))
        with self.assertRaises(ValueError):
            write_hdf5(self.path, {'mask': np.array([0, 2], dtype='i1').view('?')})

    def test_writer_does_not_cast_unsupported_data_or_create_partial_file(self):
        for value in (np.array([{}], dtype=object), np.array(['a']),
                      np.array([0], dtype='datetime64[s]'), [1., 2.]):
            with self.assertRaises(TypeError):
                write_hdf5(self.path, {'values': value})
            self.assertFalse(self.path.exists())

    def test_bad_names_and_extensions_have_no_format_fallback(self):
        for name in ('/values', 'group/values', '_values', 'two words'):
            with self.assertRaises(ValueError):
                write_hdf5(self.path, {name: np.zeros(1)})
        for extension in ('.bin', '.hdf5', '.H5'):
            with self.assertRaises(ValueError):
                write_hdf5(self.path.with_suffix(extension), {'values': np.zeros(1)})
        self.path.write_bytes(b'PK\x03\x04invalid')
        with self.assertRaises(ContractError): read_hdf5(self.path)


if __name__ == '__main__':
    unittest.main()

"""Small filesystem primitives shared by author-side writers."""
import os


def atomic_replace(source, destination):
    """Replace without unlinking the old file, including existing Windows ZIPs."""
    try:
        os.replace(source, destination)
    except PermissionError:
        if os.name != 'nt' or not os.path.isfile(destination):
            raise
        # MoveFileEx (used by os.replace) can reject an existing archive where
        # Windows' dedicated file-replacement operation succeeds. Keep both
        # paths intact on failure; do not use an unlink-and-rename fallback.
        import ctypes
        from pathlib import Path
        replace = ctypes.WinDLL('kernel32', use_last_error=True).ReplaceFileW
        replace.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
        replace.restype = ctypes.c_int
        if not replace(str(Path(destination).absolute()), str(Path(source).absolute()), None, 0, None, None):
            raise ctypes.WinError(ctypes.get_last_error())

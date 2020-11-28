from memory_tempfile import MemoryTempfile
from distutils.dir_util import copy_tree

copy_tree("./content", MemoryTempfile().gettempdir())

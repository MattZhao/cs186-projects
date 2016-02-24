from .tests import *
from .CleanRDD import *
from .URLTools import *

import pyspark.heapq3 as heapq
from pyspark.shuffle import get_used_memory,  _compressed_serializer as ser
from bisect import bisect_left

serializer = ser(None)
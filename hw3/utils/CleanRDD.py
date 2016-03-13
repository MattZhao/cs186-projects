from pyspark.rdd import portable_hash
from bisect import bisect_left


class CleanRDD(object):
    def __init__(self, rdd):
        self.__sparkrdd = rdd

    def getNumPartitions(self):
        return self.__sparkrdd.getNumPartitions()
    
    def partitionBy(self, numPartitions, func=portable_hash):
        """
        Return a copy of the RDD partitioned using the specified partitioner.

        >>> pairs = sc.parallelize([1, 2, 3, 4, 2, 4, 1]).map(lambda x: (x, x))
        >>> sets = pairs.partitionBy(2).glom().collect()
        >>> len(set(sets[0]).intersection(set(sets[1])))
        0
        """
        return self.__class__(self.__sparkrdd.partitionBy(numPartitions, partitionFunc=func))

    def coalesce(self, numPartitions, shuffle=False):
        """
        Return a new RDD that is reduced into `numPartitions` partitions.
        """
        return self.__class__(self.__sparkrdd.coalesce(numPartitions, shuffle))

    def sample(self, withReplacement, fraction, seed=None):
        """
        Return a sampled subset of this RDD.
        """
        return self.__class__(self.__sparkrdd.sample(withReplacement, fraction, seed))

    def count(self):
        """
        Return the number of elements in the RDD.
        """
        return self.__sparkrdd.count()
    
    def collect(self):
        """
        Return a list that contains all of the elements in this RDD.
        """
        return self.__sparkrdd.collect()
        
    def mapPartitionsWithIndex(self, f):
        """
        Return a new RDD by applying a function to each partition of this RDD,
        while tracking the index of the original partition.
        
        Takes in F[idx, partition iterator] => Iterator
        p = p.mapPartitionsWithIndex(lambda y, iterate: (len(_) for _ in iterate if len(_) > 10))
        
        """
        return self.__class__(self.__sparkrdd.mapPartitionsWithIndex(f))
    
    def saveAsTextFile(self, path, compressionCodecClass=None):
        """
        Save this RDD as a text file, using string representations of elements.
        """
        self.__sparkrdd.saveAsTextFile(path, compressionCodecClass)
    
    def zipPartitions(self, other, f, preservesPartitioning=False):
        """
        Return a new RDD by zipping the partitions of this and the other RDD,
        and then applying the user defined function.

        The user defined function f takes two iterators one for this and the
        other RDD respectively and returns a new iterator.

        Note both RDDs must have the same number of partitions.
        """
        if hasattr(other, "_CleanRDD__sparkrdd"):
            other = other._CleanRDD__sparkrdd
        return self.__class__(self.__sparkrdd.zipPartitions(other, f))

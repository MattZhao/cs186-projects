import commands
import csv
import os
import pyspark
import random
from tempfile import NamedTemporaryFile
from CleanRDD import *

try:
    SparkContext = pyspark.SparkContext()
except ValueError:
    print "Context already created..."

ref_output_dir = "ref_output_dir/"
your_output = "your_output/"

def _diff_helper(f, i, unordered=False, printing=True):
    """
    @param f (str) - filename to diff with reference output
    @param unordered (bool) - whether the ordering of the lines matters
    """
    yf = your_output + f
    rf = ref_output_dir + f
    if not os.path.isfile(your_output + f):
        if printing:
            print "Task " + str(i) + ": FAIL - {} does not exist.".format(f)
        return False
    
    if unordered:
        tmp1 = commands.getstatusoutput("mktemp")[1]
        _exit_code = commands.getstatusoutput("sort " + yf + " > " + tmp1)[0]
        _exit_code = commands.getstatusoutput("sort " + rf + " | diff " + tmp1 + " - > " + yf + ".diff")[0]
    else:
        _exit_code = commands.getstatusoutput("diff " + yf + " " + rf + " > " + yf + ".diff")[0]
    
    success = _exit_code == 0
    if success:
        commands.getstatusoutput("rm " + yf + ".diff")
        if printing:
            print "Task " + str(i) + ": PASS - {} matched reference output.".format(f)
        return True
    else:
        if printing:
            print "Task " + str(i) + ": FAIL - {} did not match reference output. See {}.diff.".format(f, yf)
        return False

def diff_against_reference(f, i, unordered=False, printing=True):
    """
    Compares the output files in the current directory with the reference output.
    If there is a difference, writes a ".diff" file, e.g. hits.csv.diff.
    """ 
    return _diff_helper(f, i, unordered, printing)


def check_dir():
    if not os.path.exists(your_output):
        os.makedirs(your_output)

def test1(countWords):
    check_dir()
    w = open(your_output + "task1.txt", "w")
    for tup in countWords("asyoulikeit.txt"):
        w.write(str(tup)+"\n")
    w.close()
    diff_against_reference("task1.txt", 1)

def test2TextFile(textFile):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    rdd = textFile("asyoulikeit.txt", ".")
    rdd.map(lambda x: x.replace("\n", "\\n")).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task2TextFile.txt")
    diff_against_reference("task2TextFile.txt", 2)

def test2Filter(CS186RDD):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    rdd = CS186RDD(SparkContext.textFile("asyoulikeit.txt"))
    rdd.filter(lambda x: "SCENE" in x).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task2Filter.txt")
    diff_against_reference("task2Filter.txt", 2)

def test2Reduce(CS186RDD):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    n = 15
    rdd = CS186RDD(SparkContext.parallelize([(x%n, x/n) for x in range(225)]))
    rdd.reduceByKey(lambda x, y: x + y, numPartitions=n-3).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task2Reduce.txt")
    diff_against_reference("task2Reduce.txt", 2, unordered=True)

def test2FlatMap(CS186RDD):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    rdd = CS186RDD(SparkContext.textFile("asyoulikeit.txt"))
    rdd.flatMap(lambda x: x.split()).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task2FlatMap.txt")
    diff_against_reference("task2FlatMap.txt", 2)

def test2Join(CS186RDD):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    rdd1 = CS186RDD(SparkContext.parallelize([(x, 1) for x in range(10)]))
    rdd2 = CS186RDD(SparkContext.parallelize([(x, 2) for x in range(10)]))
    rdd1.join(rdd2).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task2Join.txt")
    diff_against_reference("task2Join.txt", 2, unordered=True)

def test3ClockMap(ClockMap):
    check_dir()
    clock = ClockMap(4, lambda x: x ** 2)
    requests = [1, 2, 3, 4, 1, 6, 1, 4, 7, 4, 7, 5, 4, 6]
    with open(your_output + "task3ClockMap.txt", "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["Request", "Result", "Pointer", "Increments"])
        for r in requests:
            writer.writerow([r, clock[r], clock._p, clock._increments])
    diff_against_reference("task3ClockMap.txt", 3)

def test3CacheMap(cacheMap):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    rdd = CleanRDD(SparkContext.parallelize([x for x in range(30)]))
    cacheMap(rdd, 4, lambda x: x ** 2).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task3CacheMap.txt")
    diff_against_reference("task3CacheMap.txt", 3)

def test4(sortByKey):
    check_dir()
    t = NamedTemporaryFile(delete=True)
    t.close()
    rdd = CleanRDD(SparkContext.textFile("asyoulikeit.txt").map(lambda x: (x, None)))
    sortByKey(rdd).coalesce(1).saveAsTextFile(t.name)
    commands.getstatusoutput("mv " + t.name + "/part-00000 " + your_output + "task4.txt")
    diff_against_reference("task4.txt", 4)

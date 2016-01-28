# Homework 1: Web log data wrangling
### CS186, UC Berkeley, Spring 2016
### Points: [5% of your final grade](https://sites.google.com/site/cs186spring2016/home/basic-information)
### Due: Thursday Jan 28, 2016 11:59pm

*Note: This homework is to be done individually!*

##Description
This assignment will give you some experience with a typical task in modern data management:
using command-line tools to "wrangle" a bunch of publicly-available data into a more structured
format suitable for subsequent analysis.  In particular, we will
look at data from web access logs of an early viral video from 2002.

Along the way you will need to exercise your thinking about working with data that doesn't fit in memory.

###Your challenge
Given a large data file of web access logs, generate [csv](http://en.wikipedia.org/wiki/Comma-separated_values) files
that efficiently capture user sessions in a structured form suitable for analysis via a database
or statistical package.

###Your tools
For this assignment, you are limited to using [Python 2](https://www.python.org/) and the [standard Unix utilities](http://en.wikipedia.org/wiki/List_of_Unix_utilities) via the [Bourne shell](https://en.wikipedia.org/wiki/Bourne_shell). You will write your Python and shell scripts in a [Jupyter notebook](http://jupyter.org/), which makes it easy to interactively manipulate code and data. All of these are pre-installed on the instructional machines for you.

We assume that CS186 students can pick up languages like Python and shell scripting on their own; there will be no training as part of the class.

###Your constraints
You need to be able to handle an input file that is far larger than the memory of the computer that runs the script.  To do so, you should:

1. write streaming Python and bash code that only requires a fraction of the data to be in memory at a time, and
2. utilize UNIX utilities like `sort` that provide out-of-core divide-and-conquer algorithms.

You should not need to write very complicated code in either Python or bash.  Take advantage of UNIX utilities as much as you can.  In particular, note that there is no need for you to write an out-of-core algorithm to complete this homework: UNIX utilities can do the heavy lifting if you orchestrate them properly.

##Getting started
To follow these instructions, use your CS186 inst account on one of the *Linux* servers:

* `hive{1..28}.cs`
* `s349-{1..14}.cs`

Login into your class account using ssh. If you haven't already, in your instructional account, follow the [hw0 instructions](https://github.com/berkeley-cs186/course/tree/master/hw0) and clone a copy of your CS186 student repo.

After you [pull the latest changes](https://github.com/berkeley-cs186/course/tree/master/hw0#receiving-new-assignments-and-assignment-updates) from the `course` remote, you should see the new hw1 files.

###Running Jupyter notebook

Jupyter notebook is a web-based platform. In order for you to view the dashboard from your local computer, we need to enable *port forwarding* when making an ssh connection.

If you are using a Mac OS X or Linux system, you should have ssh installed. Windows users can install [Git Bash](https://git-for-windows.github.io/), which includes a terminal emulator and handy utilities like `ssh` and `scp`, so you can use the ssh command below. It is also possible to do port forwarding using PuTTY with [these instructions](http://howto.ccs.neu.edu/howto/windows/ssh-port-tunneling-with-putty/).

We assign you a unique port based on your login, so that it doesn't conflict with anyone else. To find out which one it is, login to your instructional account and run

    INST:~$ echo $JUPYTERPORT
    55555

You will also need your Jupyter password:

    INST:~$ cat ~/.jupyter/password
    <YOUR PASSWORD HERE>

In the following instructions, replace 55555 with the actual port number you see when running `echo $JUPYTERPORT`.

Now, we can start an SSH connection with port forwarding. Log out of your instructional account. On your _local_ machine, run

    LOCAL:~$ ssh -L 55555:localhost:55555 cs186-xx@hiveXX.cs.berkeley.edu

Once this command logs you back into your instructional account, start the Jupyter notebook by running from the hw1 directory:

    INST:hw1$ jupyter notebook

Then, on your local computer, you can point your web browser to http://localhost:55555, and you should see the Jupyter notebook dashboard. When prompted for your password, paste in the password from above.

Click on `hw1.ipynb` to begin this assignment.

**Note**: if, when starting Jupyter, you see `ERROR: the notebook server could not be started because no available port could be found.` then you may already have a Jupyter server running. You can kill it (which may lose unsaved work) using:

    pkill -f jupyter -u $USER

Then try running `jupyter notebook` again.

##Specification
Your solution should be driven by the `process_logs()` function in hw1.ipynb. It is passed one argument: an iterator (or stream) of log lines to be parsed. This input stream can only be iterated over *once*.

These web logs were produced by an Apache web server. Each line represents a request to the server that hosts the viral video. Each log looks something like this:

    24.71.223.142 - - [28/Apr/2003:16:24:59 -0700] "GET /random/video/puppy.mov HTTP/1.1" 200 567581 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"

This format is called "Combined Log Format", and you can find a description of each of the fields [here](https://httpd.apache.org/docs/1.3/logs.html#common).

The problem we are interested in is **[session reconstruction](https://en.wikipedia.org/wiki/Session_(web_analytics)#Session_reconstruction)**. A web session represents a user's actions on a website in a consecutive chunk of time. Session information is useful for tracking the path a user took through your site, and for metrics such as user engagement. These days, if you set up Google Analytics on your site, it is easy to track session information. However, in our case, we only have the logs, and would like to compute the sessions after the fact.

We'll use a time-oriented approach to reconstruct the sessions: requests made by the same IP address are considered part of the same session. If the IP address does not make a request for 30 minutes (*inactivity threshold*), we consider that IP address's next request the start of a new session. Overall, we are interested in computing session length, and the number of requests made in each session.

So, `process_logs()` should produce 3 csv output files, as follows:

* `hits.csv` should be a csv file with the header `ip,timestamp`.
    * Each row is a request made to the web server.
    * `timestamp` is a [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time), which counts the number of seconds since Jan. 1, 1970.
    * Notice how each row in the input logfile corresponds to one row in hits.csv. The order of rows in hits.csv should match the order of the log entries.
* `sessions.csv` should be a csv file with the header `ip,session_length,num_hits`
    * `session_length` is measured in seconds.
    * As described above, our inactivity threshold is > 30 minutes. i.e. if a request comes exactly 30 minutes after the last request, it is part of the same session.
    * The order of this file's rows does not matter.
* `session_length_plot.csv` is a csv file with the header `left,right,count`
    * This file describes a histogram-style plot, where the size of each bin increases exponentially.
    * In each row, the first two columns describe a range: [`left`, `right`). `count` is the number of sessions having a `session_length` in that range.
    * The left and right boundaries of each bin should be a power of 2. However, as an exception, the left boundary of the first range should be 0.
        * e.g. [0, 2), [2, 4), [4, 8), [8, 16), ...
    * Any rows which have a `count` of 0 should be omitted.
    * The rows should appear in order of increasing `left` value.

We provide you with reference versions of each of these files, as described in the Testing section below.

###Testing

On the instructional machines, you can find reference output in `~cs186/sp16/hw1/ref_output_small`.

We also provide some code that performs a [diff](https://en.wikipedia.org/wiki/Diff_utility) between your output and the reference output, which tells you which lines differ.

You need to ensure that your code will scale to datasets that are bigger than memory -- no matter how large/skewed the dataset or how much memory is on your test machine.  To help you assess your implementation, we've included a test script `test_memory_usage.sh`, which uses the [`ulimit -v`](http://ss64.com/bash/ulimit.html) command to cap the amount of virtual memory your notebook can use.  If you get a memory error, then your code is not doing appropriate streaming and/or divide-and-conquer!

##Notes
* Python has a handy [CSV library](https://docs.python.org/2/library/csv.html) for csv manipulation.  It may make your life simpler.
* As in the example csvs, the line endings for your output csvs should have UNIX line-endings (\\n). Be careful as this is not the default line ending for Python's `csvwriter`.
* The UNIX utilities are written in C, and thus must faster than anything you can write in Python. If a sub-problem can be easily solved by one of the UNIX utilities, we strongly recommend you use it.
* When using shell commands, instead of writing out intermediate results to temporary files, consider using [UNIX pipes](http://en.wikipedia.org/wiki/Pipeline_(Unix)) to chain the output of one command to the input of the next.
* The reference implementation finishes `process_logs_small()` in < 1 minute, and `process_logs_large()` in < 3 minutes on a `hive` machine. Our autograder will run your code with reasonable, but generous timeouts -- at least 2x our reference times.
* Grading for this assignment will run your code against several datasets (in the same format), and test for correct output and efficient memory usage.

## Submission instructions
Follow the submission instructions in [HW0](https://github.com/berkeley-cs186/course/tree/master/hw0).

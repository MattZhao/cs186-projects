#!/bin/bash

rm -rf your_output 2> /dev/null
mkdir your_output 2>/dev/null

rm -rf diffs 2> /dev/null
mkdir diffs 2> /dev/null

pass=true

function test_query() {
	query=$1
	test_name=$2

	# First test if the view exists
  if ! (sqlite3 -csv part2test.db "$query" > your_output/$test_name.csv); then
	  pass=false
		echo -e "ERROR $test_name! See your_output/$test_name.csv"
	else
	    diff your_output/$test_name.csv ~cs186/sp16/hw2/part2/expected_output/$test_name.csv > diffs/$test_name.csv
	    if [ $? -ne 0 ]
	    then
		pass=false
		echo -e "ERROR $test_name output differed! See diffs/$test_name.csv"
	    else
		echo -e "PASS $test_name"
	    fi
	fi
}

test_query "SELECT * FROM paths ORDER BY src, dst;" q1
test_query "SELECT * FROM topPR;" q2

if $pass; then
echo -e "SUCCESS: Your queries worked on this dataset!"
fi

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
  if ! (sqlite3 -csv part1test.db "$query" > your_output/$test_name.csv); then
    pass=false
    echo -e "ERROR $test_name! See your_output/$test_name.csv"
  else
      diff your_output/$test_name.csv ~cs186/sp16/hw2/part1/expected_output/$test_name.csv > diffs/$test_name.csv
      if [ $? -ne 0 ]
      then
    pass=false
    echo -e "ERROR $test_name output differed! See diffs/$test_name.csv"
      else
    echo -e "PASS $test_name"
      fi
  fi
}
test_query "SELECT * FROM q1 ORDER BY company_name, price_amount;" q1
test_query "SELECT * FROM q2;" q2
test_query "SELECT * FROM q3 ORDER BY state, total;" q3
test_query "SELECT * FROM q4 ORDER BY acquirer_city;" q4

if $pass; then
echo -e "SUCCESS: Your queries worked on this dataset!"
fi

# gradingscript
a simple python script to automate testing for introduction to computer science submissions

By Ethan Shenassa (created with Gemini 3.1 pro)

Place this script in a folder of c files named in the following format: `<student name>_<...>.c` and run with `python3 grader.py`. This script compiles every c file into executables based on the student's name (i. e., the characters in the filename that appear before the first underscore) into one folder called "submissions," runs each of the executables with each test case in `tests.csv`, and generates a report for each student in a .txt file (as well as a summary report markdown). 

`tests.csv` should be formatted as follows:
- the first row is simply the column headers
- column one is the test name
- column two is the input (`\n` for newline)
- column three is the expected output
- column four is a flag for how to search for the expected output in the given output (`TRUE` checks to see if the given output contains the expected output, `FALSE` requires an exact match for the test to pass)

Input and expected output ignore case, whitespace, and punctuation

TODO:
- Parallelize grading
- Add ability to take in command line arguments
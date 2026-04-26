import os
import subprocess
import re
import csv

# =====================================================================
# TEACHER CONFIGURATION SECTION
# =====================================================================

TEST_CSV_FILE = "tests.csv"
TIMEOUT_SECONDS = 5 

# =====================================================================

def load_tests_from_csv(filename):
    test_cases = []
    
    if not os.path.exists(filename):
        print(f"Error: Could not find the file '{filename}'. Please ensure it is in the same folder.")
        return None

    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None) 
        
        for row in reader:
            if len(row) < 4:
                continue
                
            name = row[0].strip()
            test_input = row[1].replace('\\n', '\n')
            expected = row[2].strip()
            contains_flag = row[3].strip().lower() in ['true', 'yes', '1', 't']
            
            test_cases.append({
                "name": name,
                "input": test_input,
                "expected_output": expected,
                "contains": contains_flag
            })
            
    return test_cases

def grade_submissions():
    test_cases = load_tests_from_csv(TEST_CSV_FILE)
    if not test_cases:
        return 
        
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    class_summary_data = []
    
    for filename in os.listdir('.'):
        if not filename.endswith('.c'):
            continue
        
        student_name = filename.split('_')[0]
        report_filename = f"{student_name}.txt"
        executable_name = f"{student_name}.out"
        
        report_filepath = os.path.join(reports_dir, report_filename)
        
        with open(report_filepath, 'w') as report:
            report.write(f"Grading Report for: {student_name}\n")
            report.write("=" * 40 + "\n\n")
            
            compile_cmd = ['gcc', '-Wall', '-o', executable_name, filename]
            compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True)
            
            warnings_count = compile_proc.stderr.count("warning:")
            notes_count = compile_proc.stderr.count("note:")
            
            if compile_proc.returncode != 0:
                report.write("--- Compiler Output ---\n")
                report.write("Compile error.\n\n")
                
                class_summary_data.append([student_name, "Failed", "N/A (Did not compile)"])
                continue 
            elif warnings_count > 0 or notes_count > 0:
                report.write("--- Compiler Output ---\n")
                report.write(f"Warnings: {warnings_count}\n")
                report.write(f"Notes: {notes_count}\n\n")
            
            report.write("--- Test Results ---\n\n")
            
            results_summary = []
            detailed_failures = []
            all_passed = True
            
            for test in test_cases:
                try:
                    run_proc = subprocess.run(
                        [f"./{executable_name}"],
                        input=test["input"],
                        capture_output=True,
                        text=True,
                        timeout=TIMEOUT_SECONDS
                    )
                    
                    given_output = run_proc.stdout.strip()
                    
                    clean_expected = [c for c in test["expected_output"] if c.isalnum()]
                    regex_body = r"[\W_]*".join(clean_expected)
                    
                    if test.get("contains", False):
                        regex_pattern = regex_body
                    else:
                        regex_pattern = r"^[\W_]*" + regex_body + r"[\W_]*$"
                    
                    if not re.search(regex_pattern, given_output, re.IGNORECASE):
                        all_passed = False
                        results_summary.append((test['name'], "FAILED"))
                        
                        fail_msg = f"FAILED: {test['name']}\n"
                        if test.get("contains", False):
                            fail_msg += f"EXPECTED OUTPUT (to contain):\n{test['expected_output']}\n"
                        else:
                            fail_msg += f"EXPECTED OUTPUT (exact match):\n{test['expected_output']}\n"
                        fail_msg += f"GIVEN OUTPUT:\n{given_output}\n"
                        fail_msg += "-" * 25 + "\n\n"
                        
                        detailed_failures.append(fail_msg)
                    else:
                        results_summary.append((test['name'], "PASSED"))
                        
                except subprocess.TimeoutExpired:
                    all_passed = False
                    results_summary.append((test['name'], "FAILED (Timeout)"))
                    
                    fail_msg = f"Failed {test['name']}\n"
                    fail_msg += f"Expected Output:\n{test['expected_output']}\n"
                    fail_msg += "Given Output:\nProgram timed out. (Infinite loop?)\n"
                    fail_msg += "-" * 25 + "\n\n"
                    
                    detailed_failures.append(fail_msg)
            
            report.write("Summary:\n")
            for name, status in results_summary:
                report.write(f"- {name}: {status}\n")
            report.write("\n")
            
            if all_passed:
                report.write("All tests passed successfully!\n\n")
                class_summary_data.append([student_name, "Success", "None"])
            else:
                report.write("--- Detailed Failures ---\n\n")
                for fail_msg in detailed_failures:
                    report.write(fail_msg)
                
                failed_tests = [name for name, status in results_summary if "FAILED" in status]
                failed_tests_str = ", ".join(failed_tests)
                class_summary_data.append([student_name, "Success", failed_tests_str])
        
        if os.path.exists(executable_name):
            os.remove(executable_name)

    if class_summary_data:
        class_summary_data.sort(key=lambda x: x[0].lower())

        # --- NEW: Calculate the maximum width needed for each column ---
        # We check the length of every item in that column, plus the header string itself
        header = ["Student Name", "Compilation", "Failed Tests"]
        max_col0 = max([len(row[0]) for row in class_summary_data] + [len(header[0])])
        max_col1 = max([len(row[1]) for row in class_summary_data] + [len(header[1])])
        max_col2 = max([len(row[2]) for row in class_summary_data] + [len(header[2])])

        master_md_path = os.path.join(reports_dir, "master_summary.md")
        with open(master_md_path, 'w', encoding='utf-8') as md_file:
            md_file.write("# Master Grading Summary\n\n")
            md_file.write(f"| {header[0]:<{max_col0}} | {header[1]:<{max_col1}} | {header[2]:<{max_col2}} |\n")
            
            # Write the divider row using repeating hyphens based on the column width
            md_file.write(f"|-{'-'*max_col0}-|-{'-'*max_col1}-|-{'-'*max_col2}-|\n")
            
            # Write the student rows padded to the exact same lengths
            for row in class_summary_data:
                md_file.write(f"| {row[0]:<{max_col0}} | {row[1]:<{max_col1}} | {row[2]:<{max_col2}} |\n")

if __name__ == "__main__":
    grade_submissions()
    print("Grading complete. Check the generated .txt files and 'master_summary.md' in the 'reports' folder.")
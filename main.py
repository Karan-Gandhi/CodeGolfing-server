import sys	
from flask import Flask, request, jsonify
import subprocess
import os
import tempfile
import uuid
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TEST_CASES_DIR = "test_cases"
LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)

leaderboard = load_leaderboard()

def read_test_cases(problem_id):
    problem_dir = os.path.join(TEST_CASES_DIR, problem_id)
    if not os.path.exists(problem_dir):
        return None

    test_cases = []
    input_files = sorted([f for f in os.listdir(problem_dir) if f.startswith("input")])
    
    for input_file in input_files:
        input_path = os.path.join(problem_dir, input_file)
        output_file = input_file.replace("input", "output")
        output_path = os.path.join(problem_dir, output_file)
        
        if os.path.exists(output_path):
            with open(input_path, 'r') as inf, open(output_path, 'r') as outf:
                test_cases.append({
                    "input": inf.read(),
                    "expected_output": outf.read()
                })

    return test_cases

def compile_and_run(source_code, language, input_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_name = str(uuid.uuid4())
        source_file = os.path.join(temp_dir, f"{file_name}.{language}")
        compiled_file = os.path.join(temp_dir, file_name)

        with open(source_file, 'w') as f:
            f.write(source_code)

        if language == 'cpp':
            compile_command = f"g++ {source_file} -o {compiled_file}"
            try:
                subprocess.run(compile_command, check=True, shell=True, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                return None, f"Compilation error: {e.stderr.decode()}"

        try:
            if language == 'cpp':
                run_command = compiled_file
            elif language == 'python':
                run_command = [sys.executable, source_file]  # Use sys.executable for the correct Python interpreter
            else:
                return None, "Unsupported language"

            result = subprocess.run(
                run_command, 
                input=input_data, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.stdout.strip(), None
        except subprocess.TimeoutExpired:
            return None, "Time Limit Exceeded (5 seconds)"
        except Exception as e:
            return None, f"Runtime Error: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit_code():
    data = request.json
    source_code = data.get('source_code')
    language = data.get('language')
    problem_id = data.get('problem_id')
    user_id = data.get('user_id', 'anonymous')

    if not all([source_code, language, problem_id]):
        return jsonify({"error": "Missing required fields"}), 400

    test_cases = read_test_cases(problem_id)
    if test_cases is None:
        return jsonify({"error": "Invalid problem ID"}), 400

    results = []
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        output, error = compile_and_run(source_code, language, test_case['input'])
        if error:
            results.append({
                "test_case": i,
                "status": "Error",
                "message": error
            })
            all_passed = False
        elif output == test_case['expected_output'].strip():
            results.append({
                "test_case": i,
                "status": "Passed"
            })
        else:
            results.append({
                "test_case": i,
                "status": "Failed",
                "expected": test_case['expected_output'].strip(),
                "actual": output
            })
            all_passed = False

    code_length = len(source_code)

    if all_passed:
        if problem_id not in leaderboard:
            leaderboard[problem_id] = {}
        if language not in leaderboard[problem_id]:
            leaderboard[problem_id][language] = []

        leaderboard[problem_id][language].append({
            "user_id": user_id,
            "length": code_length
        })
        leaderboard[problem_id][language].sort(key=lambda x: x["length"])
        save_leaderboard(leaderboard)

    return jsonify({
        "results": results,
        "code_length": code_length,
        "all_passed": all_passed
    })

@app.route('/leaderboard/<problem_id>/<language>', methods=['GET'])
def get_leaderboard(problem_id, language):
    if problem_id not in leaderboard or language not in leaderboard[problem_id]:
        return jsonify({"error": "No leaderboard data available"}), 404

    return jsonify(leaderboard[problem_id][language][:10])  # Return top 10

if __name__ == '__main__':
    app.run(debug=True)
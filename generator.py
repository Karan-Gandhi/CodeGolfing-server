import random
import os

def generate_testcase(min_size=1, max_size=100, min_val=1, max_val=1000, num_testcases=10):
    testcases = []
    
    for _ in range(num_testcases):
        size = random.randint(min_size, max_size)
        if size % 2 == 0:
            size += 1
        
        arr = []
        odd_element = random.randint(min_val, max_val)
        odd_count = random.randrange(1, size, 2)
        
        arr.extend([odd_element] * odd_count)
        
        while len(arr) < size:
            element = random.randint(min_val, max_val)
            if element != odd_element:
                arr.extend([element, element])
        
        random.shuffle(arr)
        testcases.append(arr)
    
    return testcases

def write_testcases(testcases, input_file, output_file):
    with open(input_file, 'w') as fin, open(output_file, 'w') as fout:
        fin.write(f"{len(testcases)}\n")
        for case in testcases:
            fin.write(f"{len(case)}\n")
            fin.write(' '.join(map(str, case)) + '\n')
            
            odd_element = [x for x in set(case) if case.count(x) % 2 != 0][0]
            fout.write(f"{odd_element}\n")

# Generate test cases
testcases = generate_testcase()

# Write test cases to files
write_testcases(testcases, 'test_cases/problem1/input1.txt', 'test_cases/problem1/output1.txt')
write_testcases(generate_testcase(num_testcases=100, min_size=int(1e4 - 1), max_size=int(1e4), min_val=int(1e8), max_val=int(1e9)), 'test_cases/problem1/input2.txt', 'test_cases/problem1/output2.txt')
write_testcases(generate_testcase(num_testcases=100, min_size=int(100), max_size=int(1e4), min_val=int(1e8), max_val=int(1e9)), 'test_cases/problem1/input3.txt', 'test_cases/problem1/output3.txt')

print("Test cases have been written to 'testcases/input.txt' and 'testcases/output.txt'")
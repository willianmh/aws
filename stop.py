import src.awsFunctions as aws
import time
import sys


def main():
    if len(sys.argv) <= 1:
        path_to_file = 'instances_ids'
    else:
        path_to_file = sys.argv[1]

    # if len(path_to_file) < 1:
    ids = []
    with open(path_to_file, 'r') as file:
        for line in file:
            ids.append(line.rstrip())

    aws.stop_instances(ids)
    time.sleep(1)

    
main()

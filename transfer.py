import src.awsFunctions as aws
import time
import sys


def main():
    ids = sys.argv[1]
    file = sys.argv[2]
    key = sys.argv[3]
    # if len(path_to_file) < 1:
    ids = []
    with open(ids, 'r') as file:
        for line in file:
            ids.append(line.rstrip())

    aws.transferParallel(ids, key, file)
    time.sleep(1)


main()

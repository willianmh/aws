import src.awsFunctions as aws
import time
import sys


def main():
    id_file = sys.argv[1]
    key = sys.argv[2]
    paths_to_files = []
    for i in range(3, len(sys.argv)):
        paths_to_files.append(sys.argv[i])
    ids = []
    with open(id_file, 'r') as file:
        for line in file:
            ids.append(line.rstrip())

    aws.transferParallel(ids, key, paths_to_files)
    time.sleep(1)


main()

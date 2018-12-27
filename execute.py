import src.awsFunctions as aws
import time
import sys


def main():
    id_file = sys.argv[1]
    key = sys.argv[2]
    commands = []

    for i in range(3, len(sys.argv)):
        commands.append(sys.argv[i])

    ids = []
    with open(id_file, 'r') as file:
        for line in file:
            ids.append(line.rstrip())

    if len(ids) > 0:
        aws.execute_parallel(ids, key, commands)
        time.sleep(1)


main()

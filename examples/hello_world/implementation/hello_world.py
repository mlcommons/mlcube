
import argparse
import time

parser = argparse.ArgumentParser(description='Hello and goodbye.')
parser.add_argument('--mlbox_task', metavar='TASK', type=str,
                    help='the name of the task.')
parser.add_argument('--name', metavar='NAME', type=str,
                    help='the path to the name.')
parser.add_argument('--greeting', metavar='FILE', type=str,
                    help='the path to write the greeting to.')
parser.add_argument('--farewell', metavar='FILE', type=str,
                    help='the path to write the farewell to.')

args = parser.parse_args()

with open(args.name) as f:
    name = f.read().strip()

if args.mlbox_task == 'hello':
    with open(args.greeting, 'w') as f:
        f.write('Hello {}, right now is {} seconds.\n'.format(name, int(time.time())))
elif args.mlbox_task == 'goodbye':
    with open(args.greeting) as f:
        previous_greeting = f.read().strip()
    with open(args.farewell, 'w') as f:
        f.write('Previously I said: {}\n'.format(previous_greeting))
        f.write('Now I say goodbye {} at {} seconds.\n'.format(name, int(time.time())))

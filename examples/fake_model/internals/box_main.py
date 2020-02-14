import argparse
import os

parser = argparse.ArgumentParser(description='Say Hello World to you!')

parser.add_argument('--mlbox_params', metavar='PARAMS', type=str, help='the parameters to train the model.')
parser.add_argument('--mlbox_dataset', metavar='DATASET', type=str, help='The dataset input.')
parser.add_argument('--mlbox_model_dir', metavar='MODEL_DIR', type=str, help='the directory to output the tarined model to.')
parser.add_argument('--mlbox_log_file', metavar='LOG_FILE', type=str, help='where to log the output to.')
parser.add_argument('--step_size', metavar='STEPSIZE', type=str, help='the batch size to use.')
parser.add_argument('--batch_size', metavar='BATCHSIZE', type=str, help='the step size to use.')
# The subsitution rules gives us direct access to the dataset without using the --mlbox_* param.
parser.add_argument('--dataset_direct', metavar='DATASETDIRECT', type=str, help='To demo subsitution.')

args = parser.parse_args()

with open(args.mlbox_params) as f:
    params = f.read()

with open(args.dataset_direct) as f:
    data = f.read()

with open(os.path.join(args.mlbox_model_dir, 'train_model.txt'), 'w') as f:
    f.write('THIS IS A TRAINED MODEL!'.format(data))
    f.write('trained on {}'.format(data))
    f.write('Training with params:')
    f.write(params)

with open(os.path.join(args.mlbox_log_file), 'w') as f:
    f.write('training with step_size = {}'.format(args.step_size))
    f.write('training with batch_size = {}'.format(args.batch_size))

print('Done training a fake model!')

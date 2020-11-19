import  os
import sys
import argparse


def run(cmd, **kwargs):
    for k, v  in kwargs.items():
        if v is None:
            raise Exception('Argument {} must be a file path.'.format(k))
    cmd_filled = cmd.format(**kwargs)
    print(cmd_filled)
    return os.system(cmd_filled)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
          "--mlcube_task", type=str,
          help="The MLCube task to preform.",
          metavar="<TASK>")
    parser.add_argument(
          "--raw_dir", type=str, default=None,
          help="[default: %(default)s] Path where the raw data will be downloaded "
          "and extracted.",
          metavar="<RD>")
    parser.add_argument(
          "--data_dir", type=str, default=None,
          help="[default: %(default)s] Path where the training and evaluation "
          "data are saved.",
          metavar="<DD>")
    parser.add_argument(
          "--parameter_file", type=str, default=None,
          help="Parameter file to use. The parameter file should be a yaml file "
          "that serves as command line arguments.",
          metavar="<PF>")
    parser.add_argument(
          "--vocab_file", type=str, default=None,
          help="[default: %(default)s] Name of vocabulary file.",
          metavar="<VF>")
    parser.add_argument(
          "--model_dir", type=str, default=None,
          help="[default: %(default)s] Directory to save Transformer model "
          "training checkpoints",
          metavar="<MD>")
    parser.add_argument(
          "--bleu_dir", type=str, default=None,
          help="[default: %(default)s] Directory to save BLEU scores."
          )
    parser.add_argument(
          "--mlperf_log_dir", type=str, default=None,
          help="[default: %(default)s] Directory for mlperf log files.", metavar="<LD>"
          )

    FLAGS, unparsed = parser.parse_known_args()
    if FLAGS.mlcube_task is None:
        raise Exception('needs --mlcube_task')

    if FLAGS.mlcube_task  == 'downloaddata':
        return run('python3 -m mlcube_download_main --raw_dir={raw_dir}', raw_dir=FLAGS.raw_dir)
    if FLAGS.mlcube_task  == 'preprocess':
        return run('python3 -m mlcube_preprocess_main --raw_dir={raw_dir} --data_dir={data_dir}',
                raw_dir=FLAGS.raw_dir, data_dir=FLAGS.data_dir)
    if FLAGS.mlcube_task  == 'train':
        return run('python3 -m mlcube_train_main --data_dir={data_dir}'
            '--parameter_file={parameter_file} --vocab_file={vocab_file}'
            '--model_dir={model_dir} --bleu_dir={bleu_dir} --mlperf_log_dir={mlperf_log_dir}',
            data_dir=FLAGS.data_dir, parameter_file=FLAGS.parameter_file,
            vocab_file=FLAGS.vocab_file,
            model_dir=FLAGS.model_dir, bleu_dir=FLAGS.bleu_dir,
            mlperf_log_dir=FLAGS.mlperf_log_dir)
    raise Exception('No known task: {}'.format(FLAGS.mlcube_task))


if __name__  == '__main__':
    sys.exit(main())

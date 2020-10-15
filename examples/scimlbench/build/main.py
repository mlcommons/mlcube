# Height and Width of a single EM Graphene Image
IMG_SIZE = 256

from abc import abstractmethod, ABCMeta
import time
import h5py
import tensorflow as tf
import numpy as np
from pathlib import Path
import horovod.tensorflow.keras as hvd
from tinydb import TinyDB, Query


class DataLoader():
    """Base class for data loaders

    This defines the interface that new data loaders must adhere to
    """
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def input_shape(self):
        pass

    @property
    @abstractmethod
    def output_shape(self):
        pass

    @abstractmethod
    def to_dataset(self):
        pass


def autoencoder(input_shape, learning_rate=0.001, **params):
    skip_layers = []

    input_layer = tf.keras.layers.Input(input_shape)
    x = input_layer
    x = tf.keras.layers.Conv2D(filters=8, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=8, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    skip_layers.append(x)
    x = tf.keras.layers.MaxPooling2D()(x)

    x = tf.keras.layers.Conv2D(filters=16, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=16, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    skip_layers.append(x)
    x = tf.keras.layers.MaxPooling2D()(x)

    x = tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    skip_layers.append(x)
    x = tf.keras.layers.MaxPooling2D()(x)

    x = tf.keras.layers.Conv2D(filters=64, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=64, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)

    x = tf.keras.layers.UpSampling2D()(x)
    x = tf.keras.layers.Concatenate()([x, skip_layers.pop(-1)])
    x = tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)

    x = tf.keras.layers.UpSampling2D()(x)
    x = tf.keras.layers.Concatenate()([x, skip_layers.pop(-1)])
    x = tf.keras.layers.Conv2D(filters=16, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=16, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)

    x = tf.keras.layers.UpSampling2D()(x)
    x = tf.keras.layers.Concatenate()([x, skip_layers.pop(-1)])
    x = tf.keras.layers.Conv2D(filters=8, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv2D(filters=8, kernel_size=3, activation='relu', padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x)

    x = tf.keras.layers.Conv2D(filters=1, kernel_size=3, activation='linear', padding='same')(x)

    model = tf.keras.models.Model(input_layer, x)
    return model


class EMGrapheneDataset(DataLoader):

    def __init__(self, data_dir, seed=None, batch_size=10, **kwargs):
        self._seed = seed
        self._data_dir = Path(data_dir)
        self._batch_size = 10

    def _load_data(self, path):
        path = path.decode()
        with h5py.File(path, "r") as hdf5_file:
            for i in range(len(hdf5_file['images'])):
                images = np.array(hdf5_file["images"][i])
                yield images

    @property
    def input_shape(self):
        return (IMG_SIZE, IMG_SIZE, 1)

    @property
    def output_shape(self):
        return (IMG_SIZE, IMG_SIZE, 1)

    def to_dataset(self):
        types = tf.float32
        shapes = tf.TensorShape([IMG_SIZE, IMG_SIZE, 1])

        path = str(self._data_dir / 'graphene_img_noise.h5')
        noise_dataset = tf.data.Dataset.from_generator(self._load_data,
                                                       output_types=types,
                                                       output_shapes=shapes,
                                                       args=(path,))

        path = str(self._data_dir / 'graphene_img_clean.h5')
        clean_dataset = tf.data.Dataset.from_generator(self._load_data,
                                                       output_types=types,
                                                       output_shapes=shapes,
                                                       args=(path,))

        dataset = tf.data.Dataset.zip((noise_dataset, clean_dataset))
        dataset = dataset.shard(hvd.size(), hvd.rank())
        dataset = dataset.shuffle(1000)
        dataset = dataset.batch(self._batch_size)
        return dataset


class AverageMeter(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.value = 0
        self.last = 0

    def record(self, value, n=1):
        self.last = value
        self.count += n
        self.value += value * n

    def get_value(self):
        if self.count == 0:
            return 0

        return self.value / self.count

    def get_last(self):
        return self.last


def sanitize_dict(d):
    d = d.copy()
    for k, v in d.items():
        if type(v) is dict:
            v = sanitize_dict(v)
        elif isinstance(v, np.floating) or isinstance(v, float):
            v = float(v)
        elif isinstance(v, set):
            v = list(v)
        elif hasattr(v, '__name__'):
            v = v.__name__
        else:
            v = str(v)
        d[k] = v
    return d


class TrackingClient:

    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(str(path))

    def log_metric(self, key, value, step=0):
        value = sanitize_dict(value)
        metric = {'name': key, 'data': value, 'step': step,
                  'timestamp': time.time(), 'type': 'metric'}

        self._db.insert(metric)

    def log_tag(self, key, value):
        value = sanitize_dict(value)
        tag = {'name': key, 'data': value, 'type': 'tag'}
        self._db.insert(tag)

    def log_param(self, key, value):
        value = sanitize_dict(value)
        param = {'name': key, 'data': value, 'type': 'param'}
        self._db.insert(param)

    def get_metric(self, name):
        query = Query()
        return self._db.search((query.name == name) & (query.type == 'metric'))

    def get_metrics(self):
        query = Query()
        return self._db.search(query.type == 'metric')

    def get_param(self, name):
        query = Query()
        return self._db.search((query.name == name) & (query.type == 'param'))

    def get_params(self):
        query = Query()
        return self._db.search(query.type == 'param')

    def get_tag(self, name):
        query = Query()
        return self._db.search((query.name == name) & (query.type == 'tag'))

    def get_tags(self):
        query = Query()
        return self._db.search(query.type == 'tag')


class TrackingCallback(tf.keras.callbacks.Callback):

    def __init__(self, output_dir, batch_size, warmup_steps=1, log_batch=False):
        self._db = TrackingClient(Path(output_dir) / 'logs.json')
        self._current_step = 0
        self._warmup_steps = warmup_steps
        self._batch_size = batch_size

        self._train_meter = AverageMeter()
        self._predict_meter = AverageMeter()
        self._test_meter = AverageMeter()
        self._log_batch = log_batch

    def on_train_batch_begin(self, batch, logs=None):
        self._t0 = time.time()

    def on_train_batch_end(self, batch, logs=None):
        if self._current_step < self._warmup_steps:
            return

        t1 = time.time()
        batch_time = self._batch_size / (t1 - self._t0)

        self._train_meter.record(batch_time)

        if self._log_batch:
            self._db.log_metric('train_batch_log', logs, step=batch)

    def on_predict_batch_begin(self, batch, logs=None):
        self._t0 = time.time()

    def on_predict_batch_end(self, batch, logs=None):
        t1 = time.time()
        batch_time = self._batch_size / (t1 - self._t0)

        self._predict_meter.record(batch_time)

        if self._log_batch:
            self._db.log_metric('predict_batch_log', logs, step=batch)

    def on_test_batch_begin(self, batch, logs=None):
        self._t0 = time.time()

    def on_test_batch_end(self, batch, logs=None):
        t1 = time.time()
        batch_time = self._batch_size / (t1 - self._t0)

        self._test_meter.record(batch_time)

        if self._log_batch:
            self._db.log_metric('test_batch_log', logs, step=batch)

    def on_epoch_begin(self, epoch, logs=None):
        self._epoch_begin_time = time.time()

    def on_epoch_end(self, epoch, logs=None):
        self._current_step = epoch
        if epoch < self._warmup_steps:
            return

        metrics = {
            'duration': time.time() - self._epoch_begin_time,
            'samples_per_sec': self._train_meter.get_value()
        }
        if logs is not None:
            metrics.update(logs)
        self._db.log_metric('epoch_log', metrics, step=epoch)

    def on_train_begin(self, logs=None):
        self._train_begin_time = time.time()

    def on_train_end(self, logs=None):
        metrics = {
            'duration': time.time() - self._train_begin_time,
            'samples_per_sec': self._train_meter.get_value()
        }
        if logs is not None:
            metrics.update(logs)
        self._db.log_metric('train_log', metrics)

    def on_test_begin(self, logs=None):
        self._test_begin_time = time.time()

    def on_test_end(self, logs=None):
        metrics = {
            'duration': time.time() - self._test_begin_time,
            'samples_per_sec': self._test_meter.get_value()
        }
        if logs is not None:
            metrics.update(logs)
        self._db.log_metric('test_log', metrics)

    def on_predict_begin(self, logs=None):
        self._predict_begin_time = time.time()

    def on_predict_end(self, logs=None):
        metrics = {
            'duration': time.time() - self._predict_begin_time,
            'samples_per_sec': self._predict_meter.get_value()
        }
        if logs is not None:
            metrics.update(logs)
        self._db.log_metric('predict_log', metrics)


hvd.init()

train_data_dir = '/N/u2/v/vlabeyko/sandbox/sciml/em_denoise/em_denoise/train'
test_data_dir = '/N/u2/v/vlabeyko/sandbox/sciml/em_denoise/em_denoise/test'
output_dir = '/tmp/sciml'
epochs = 1
learning_rate = 0.01
beta_1 = 0.9
beta_2 = 0.999
epsilon = 1e-07


def train(data_dir=None, output_dir=None, epochs=1, learning_rate=0.01, beta_1=0.9, beta_2=0.99,
          epsilon=1e-07):
    dataset = EMGrapheneDataset(data_dir=data_dir)

    opt = tf.keras.optimizers.Adam(learning_rate=learning_rate, beta_1=beta_1, beta_2=beta_2,
                                   epsilon=epsilon, amsgrad=False, name='Adam')

    opt = hvd.DistributedOptimizer(opt)

    loss = tf.keras.losses.MeanSquaredError()

    model = autoencoder(dataset.input_shape)

    model.compile(loss=loss,
                  optimizer=opt,
                  experimental_run_tf_function=False)

    hooks = [
        hvd.callbacks.BroadcastGlobalVariablesCallback(0),
        hvd.callbacks.MetricAverageCallback(),
    ]

    if hvd.rank() == 0:
        # These hooks only need to be called by one instance.
        # Therefore we need to only add them on rank == 0
        tracker_hook = TrackingCallback(output_dir, 256, False)
        hooks.append(tracker_hook)

    model_dir = Path(output_dir)
    weights_file = model_dir / 'final_weights.h5'

    model.fit(dataset.to_dataset(), epochs=epochs, callbacks=hooks)

    if hvd.rank() == 0:
        model_dir = Path(output_dir)
        weights_file = str(model_dir / 'final_weights.h5')
        model.save_weights(weights_file)


def predict(model=None, data_dir=None, output_dir=None, global_batch_size=256, log_batch=False):
    hooks = [
        hvd.callbacks.BroadcastGlobalVariablesCallback(0),
        hvd.callbacks.MetricAverageCallback(),
    ]

    if hvd.rank() == 0:
        # These hooks only need to be called by one instance.
        # Therefore we need to only add them on rank == 0
        tracker_hook = TrackingCallback(output_dir, global_batch_size, log_batch)
        hooks.append(tracker_hook)

    print('Begin Predict...')

    model_dir = Path(output_dir)
    weights_file = model_dir / 'final_weights.h5'

    # Edge case: user is trying to run inference but not training
    # See if we can find a pre-trained model from another run
    # If not then throw and error as we're in an inconsistent state.
    if not weights_file.exists():
        print('Searching for pre-trained models')

        weight_files = model_dir.parent.glob('**/*final_weights.h5')
        weight_files = list(sorted(weight_files))
        if len(weight_files) == 0:
            raise RuntimeError(
                "No pre-trained model exists! Please train a model before running inference!")
        weights_file = weight_files[-1]

    print(f'Using weights file: {str(weights_file)}')
    model.load_weights(str(weights_file))

    dataset = EMGrapheneDataset(data_dir=data_dir).to_dataset()

    model.evaluate(dataset, callbacks=hooks)
    return model


model = train(data_dir=train_data_dir, output_dir=output_dir)

predict(data_dir=test_data_dir, output_dir=output_dir, model=model)

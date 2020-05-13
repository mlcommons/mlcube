import os


class BaseValidator(object):
  @staticmethod
  def validate():
    raise NotImplementedError


class FileValidator(BaseValidator):
  @staticmethod
  def validate(path):
    passed = True
    msg = None
    if not os.path.isfile(path):
      passed = False
      msg = "File does not exist: {}".format(path)
    return passed, msg


class DirectoryValidator(BaseValidator):
  @staticmethod
  def validate(path):
    passed = True
    msg = None
    if not os.path.isdir(path):
      passed = False
      msg = "Directory does not exist: {}".format(path)
    return passed, msg


# TODO
class SchemaValidator(BaseValidator):
  @staticmethod
  def validate(path):
    passed = True
    msg = None
    return passed, msg

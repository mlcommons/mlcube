from unittest import TestCase
from omegaconf import (DictConfig, OmegaConf)
from mlcube_ssh.ssh_metadata import (PythonInterpreter, SystemInterpreter, VirtualEnvInterpreter)


class TestPythonInterpreters(TestCase):
    def test_all_interpreters_present(self) -> None:
        self.assertIsInstance(PythonInterpreter._interpreters, dict)
        self.assertTrue(len(PythonInterpreter._interpreters) == 2)

        self.assertIn('system', PythonInterpreter._interpreters)
        self.assertIs(PythonInterpreter._interpreters['system'], SystemInterpreter)

        self.assertIn('virtualenv', PythonInterpreter._interpreters)
        self.assertIs(PythonInterpreter._interpreters['virtualenv'], VirtualEnvInterpreter)


class TestSystemInterpreter(TestCase):
    def check_state(self, state: DictConfig, interpreter: SystemInterpreter) -> None:
        self.assertIsInstance(interpreter, SystemInterpreter)
        self.assertEqual(state.type, interpreter.type)
        self.assertEqual(state.python, interpreter.python)
        self.assertEqual(state.requirements, interpreter.requirements)

    def test_system_interpreter_default_config(self) -> None:
        self.check_state(
            OmegaConf.create({'type': 'system', 'python': 'python', 'requirements': ''}),
            PythonInterpreter.create(OmegaConf.create({'type': 'system'}))
        )

    def test_system_interpreter_user_config(self) -> None:
        config = OmegaConf.create({'type': 'system', 'python': 'python3.8',
                                   'requirements': 'click==7.1.2 mlcube==0.2.2'})
        self.check_state(config, PythonInterpreter.create(config))


class TestVirtualEnvInterpreter(TestCase):
    def check_state(self, state: DictConfig, interpreter: VirtualEnvInterpreter) -> None:
        self.assertIsInstance(interpreter, VirtualEnvInterpreter)
        self.assertEqual(state.type, interpreter.type)
        self.assertEqual(state.python, interpreter.python)
        self.assertEqual(state.requirements, interpreter.requirements)
        self.assertEqual(state.location, interpreter.location)
        self.assertEqual(state.name, interpreter.name)

    def test_virtualenv_interpreter_user_config(self):
        config = OmegaConf.create({
            'type': 'virtualenv', 'python': 'python3.8', 'requirements': 'click==7.1.2 mlcube==0.2.2',
            'location': '/opt/mlcube_resources/environments', 'name': 'docker_runner-0.2.2'
        })
        self.check_state(config, PythonInterpreter.create(config))

import abc
import contextlib
import typing


class ValidatableData(abc.ABC):
    @abc.abstractmethod
    def validate(self):
        pass


ValidatorType = typing.Callable[[], None]


class Validator:
    _validators: typing.Dict[typing.Type, typing.List[ValidatorType]]

    def __init__(self, use_method=True, use_class=True):
        super(Validator, self).__init__()

        self._use_method = use_method
        self._use_class = use_class
        self._validators = {}

    @contextlib.contextmanager
    def _run_validation(self):
        try:
            yield
        except AssertionError as e:
            msg = str(e) if e.args else "Validation failed"
            raise ValueError(msg)

    def validate(self, model):
        if (self._use_class and isinstance(model, ValidatableData)) or (
                self._use_method and hasattr(model, "validate")):
            with self._run_validation():
                model.validate()

        for (cls, validators) in self._validators:
            if isinstance(model, cls):
                with self._run_validation():
                    for v in validators:
                        v(model)

    def register_validator(self, cls: typing.Type, f: ValidatorType):
        self._validators.setdefault(cls, []).append(f)

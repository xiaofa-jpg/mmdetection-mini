from cvcore import Hook, HOOKS, build_from_cfg, get_event_storage
from ..utils import EventWriter
from .builder import WRITERS

__all__ = ['PeriodicWriterHook']


@HOOKS.register_module()
class PeriodicWriterHook(Hook):
    """
    Write events to EventStorage (by calling ``writer.write()``) periodically.

    It is executed every ``period`` iterations and after the last iteration.
    Note that ``period`` does not affect how data is smoothed by each writer.
    """

    def __init__(self, writers, interval=20):
        """
        Args:
            writers (list[EventWriter]): a list of EventWriter objects
            interval (int):
        """
        if not isinstance(writers, list):
            writers = [writers]

        writers_obj = []
        for w in writers:
            if isinstance(w, dict):
                w = build_from_cfg(w, WRITERS)
            else:
                assert isinstance(w, EventWriter), w
            writers_obj.append(w)

        self._writers = writers_obj
        self._interval = interval

    def before_run(self, runner):
        if self._interval <= 0:
            return
        for writer in self._writers:
            writer.init(runner)

    def before_iter(self, runner):
        storage = get_event_storage()
        storage.iter = runner.iter

    def after_train_iter(self, runner):
        if self._interval <= 0:
            return
        if (runner.iter + 1) % self._interval == 0 or (
                runner.iter == runner.max_iters - 1
        ):
            for writer in self._writers:
                writer.write()

    def after_run(self, runner):
        if self._interval <= 0:
            return
        for writer in self._writers:
            # If any new data is found (e.g. produced by other after_train),
            # write them before closing
            writer.write()
            writer.close()

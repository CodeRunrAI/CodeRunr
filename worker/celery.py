from celery import Celery
from celery.signals import setup_logging, worker_process_init

from config import configure_logger, settings

app = Celery(
    "worker",
    include=["worker.tasks"],
    **settings.CELERY_CONFIG.celery_kwargs,
)

app.conf.update(
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
)


@setup_logging.connect
def setup_celery_logging(**_: object) -> None:
    configure_logger()


@worker_process_init.connect
def setup_worker_logging(**_: object) -> None:
    configure_logger()


if __name__ == "__main__":
    app.start()

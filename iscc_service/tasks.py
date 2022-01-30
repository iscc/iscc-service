# -*- coding: utf-8 -*-
"""Background Tasks"""
import json
from os.path import join, basename
from typing import Optional
from codetiming import Timer
from iscc_service.models import URLRequest
import iscc
from iscc.utils import download_file
from blake3 import blake3
import tempfile
from iscc.schema import ISCC


class TaskResult(URLRequest):
    task_id: Optional[str]
    filename: Optional[str]
    status: Optional[str]
    message: Optional[str]
    result: Optional[dict]

    def set_task_id(self):
        self.task_id = blake3(self.url.encode("utf-8")).hexdigest()
        self.status = "pending"

    def save(self):
        task_file_path = task_id_to_task_path(self.task_id)
        with open(task_file_path, "wt", encoding="utf-8") as outf:
            outf.write(self.json(exclude_unset=True))


def url_to_task_id(url: str) -> str:
    return blake3(url.encode("utf-8")).hexdigest()


def load_task(task_id: str) -> TaskResult:
    tp = task_id_to_task_path(task_id)
    with open(tp, "rt", encoding="utf-8") as infile:
        return TaskResult(**json.load(infile))


def task_id_to_task_path(task_id) -> str:
    return join(tempfile.gettempdir(), f"task-{task_id}.json")


def process_url(status: TaskResult):

    timer = Timer("message")
    timer.start()

    # task file
    status.status = "downloading"
    status.save()

    try:
        local_path = download_file(
            status.url, folder=tempfile.gettempdir(), sanitize=True
        )
    except Exception as e:
        status.status = "failed"
        status.message = f"download failed with {type(e)}"
        status.save()
        return

    status.status = "processing"
    status.filename = basename(local_path)
    status.save()

    title = status.title or ""
    extra = status.extra or ""
    try:
        result = iscc.code_iscc(local_path, title=title, extra=extra)
    except Exception as e:
        status.status = f"failed"
        status.message = f"processing failed with {type(e)}"
        return

    status.status = "success"
    status.result = ISCC(**result).dict(exclude_unset=True)
    timer.stop()
    status.message = f"Processing Time: {timer.timers['message']:.2f}"
    status.save()

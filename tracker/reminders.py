from datetime import datetime, timedelta, timezone
from emoji import emojize
from telegram.ext import Application


from .context import Context
from .task import Task
from .tz import ntp_time_offset


async def reminder_job(context: Context):
    job = context.job
    task: Task = job.data

    is_late = (
        datetime.now(task.at.tzinfo) - task.at - timedelta(seconds=ntp_time_offset())
    ) > timedelta(minutes=1)

    if is_late:
        await context.bot.send_message(
            job.chat_id,
            emojize(":fire: Due to server downtime the reminder is sent late!"),
        )

    await context.bot.forward_message(
        job.chat_id, job.chat_id, message_id=task.message_id
    )

    chat_data = context.application.chat_data.get(job.chat_id)
    assert chat_data != None
    assert chat_data.delete_task_if_exists(task)


def enqueue_reminder(task: Task, application: Application, chat_id: int):
    adjusted_time = task.at - timedelta(seconds=ntp_time_offset())
    application.job_queue.run_once(
        reminder_job,
        adjusted_time,
        name=str(id(task)),
        chat_id=chat_id,
        data=task,
        job_kwargs={"misfire_grace_time": None},
    )


def dequeue_reminder(application: Application, task: Task) -> bool:
    name = str(id(task))
    jobs = application.job_queue.get_jobs_by_name(name)
    if not jobs:
        return False
    for job in jobs:
        job.schedule_removal()
    return True

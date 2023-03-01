from google.cloud import tasks_v2
import logging
import os

project_id = os.environ.get("_PROJECT_ID")
cloudtask_region = os.environ.get("_EXPORT_QUEUE_REGION")
cloudtask_name = os.environ.get("_EXPORT_QUEUE_NAME")


def enqueue(task):
    """Enqueue a task."""
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project_id, cloudtask_region, cloudtask_name)
    response = client.create_task(request={"parent": parent, "task": task})
    logging.info(f"Response from cloud tasks: {response}.")
    return response


def get_queue_path():
    """Return the queue path."""
    client = tasks_v2.CloudTasksClient()
    return client.queue_path(project_id, cloudtask_region, cloudtask_name)

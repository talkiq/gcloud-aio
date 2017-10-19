## taskmanager/

> smoke test: `python -m gcloud.aio.taskmanager smoke`

This implements a pull task queue manager, which:

 * leases tasks from a single pull task queue
 * renews tasks as necessary
 * releases tasks on failure
 * deletes tasks when they are completed successfully
 * dead-letters and deletes tasks when they have failed too many times

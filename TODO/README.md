# gcloud/aio

## smoke tests

Each component has a smoke test, which you can run via `python -m gcloud.aio.<component> smoke`. You will need to have a service file for our `talkiq-integration` project, located in the root repo directory and called `service-integration.json`. The smoke tests also serve as examples. :)

## components

### auth/

> smoke test: `python -m gcloud.aio.auth smoke`

Implements a Token class for authorizing against GCloud. All of the other components accept a token instance argument. You can define a single token for all of the required components in the project, or define one token for each component. Each component corresponds to one GCloud service, and each GCloud service [requires "scopes"](https://developers.google.com/identity/protocols/googlescopes).

### datastore/

> smoke test: `python -m gcloud.aio.datastore smoke`

> scopes: `https://developers.google.com/identity/protocols/googlescopes#datastorev1`

### storage/

> smoke test: `python -m gcloud.aio.storage smoke`

> scopes: `https://developers.google.com/identity/protocols/googlescopes#storagev1`

### bigquery/

> smoke test: `python -m gcloud.aio.bigquery smoke`

> scopes: `https://developers.google.com/identity/protocols/googlescopes#bigqueryv2`

### taskqueue/

> smoke test: `python -m gcloud.aio.taskqueue smoke`

> scopes: `https://developers.google.com/identity/protocols/googlescopes#taskqueuev1beta2`

## taskmanager/

> smoke test: `python -m gcloud.aio.taskmanager smoke`

This implements a pull task queue manager, which:

 * leases tasks from a single pull task queue
 * renews tasks as necessary
 * releases tasks on failure
 * deletes tasks when they are completed successfully
 * dead-letters and deletes tasks when they have failed too many times

These docs cover two projects: `gcloud-aio-*` and `gcloud-rest-*`. Both of them are HTTP implementations of the Google Cloud client libraries. The former has been built to work with Python 3's asyncio. The later is a threadsafe `requests`-based implementation which should be compatible all the way back to Python 2.7.

For supported clients, see the modules in the sidebar.

## Installation

```console
$ pip install --upgrade gcloud-{aio,rest}-{client_name}
```

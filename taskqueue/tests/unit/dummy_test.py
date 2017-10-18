import gcloud.aio.taskqueue as taskqueue


def test_aardvark():
    assert taskqueue.Something.animal == 'aardvark'

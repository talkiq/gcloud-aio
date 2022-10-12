from gcloud.aio.auth import BUILD_GCLOUD_REST

if BUILD_GCLOUD_REST:
    pass
else:
    import prometheus_client

    _NAMESPACE = 'gcloud_aio'
    _SUBSYSTEM = 'pubsub'

    CONSUME = prometheus_client.Counter(
        'subscriber_consume',
        'Counter of the outcomes of PubSub message consume attempts',
        ['outcome'],
        namespace=_NAMESPACE,
        subsystem=_SUBSYSTEM,
        unit='total')

    CONSUME_LATENCY = prometheus_client.Histogram(
        'subscriber_consume_latency',
        'Histogram of PubSub message consume latencies',
        ['phase'],
        namespace=_NAMESPACE,
        subsystem=_SUBSYSTEM,
        unit='seconds')

    BATCH_STATUS = prometheus_client.Counter(
        'subscriber_batch_status',
        'Counter for success/failure to process PubSub message batches',
        ['component', 'outcome'],
        namespace=_NAMESPACE,
        subsystem=_SUBSYSTEM,
        unit='total')

    MESSAGES_PROCESSED = prometheus_client.Counter(
        'subscriber_messages_processed',
        'Counter of successfully acked/nacked messages',
        ['component'],
        namespace=_NAMESPACE,
        subsystem=_SUBSYSTEM,
        unit='total')

    MESSAGES_RECEIVED = prometheus_client.Counter(
        'subscriber_messages_received',
        'Counter of messages pulled from subscription',
        namespace=_NAMESPACE,
        subsystem=_SUBSYSTEM,
        unit='total')

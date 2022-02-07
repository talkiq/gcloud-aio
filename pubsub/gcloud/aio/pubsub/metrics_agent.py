import prometheus_client


class MetricsAgent:
    """
    Any metric client should implement this interface
    to be compatible with subscriber.subscribe
    """
    def histogram(self,
                  metric: str,
                  value: float) -> None:
        pass

    def increment(self,
                  metric: str,
                  value: float = 1) -> None:
        pass


class PrometheusMetrics:
    def __init__(self, *, namespace: str = '',
                 subsystem: str = '') -> None:
        self.consume = prometheus_client.Counter(
            'pubsub_consume',
            'Counter of the outcomes of PubSub message consume attempts',
            ['outcome'], namespace=namespace, subsystem=subsystem)

        self.consume_latency = prometheus_client.Histogram(
            'pubsub_consume_latency',
            'Histogram of PubSub message consume latencies', ['aspect'],
            namespace=namespace, subsystem=subsystem)

        self.batch_fail = prometheus_client.Counter(
            'pubsub_batch_failed',
            'Counter for failures to process PubSub message batches',
            ['component'], namespace=namespace, subsystem=subsystem)

        self.messages_processed = prometheus_client.Counter(
            'pubsub_messages_processed',
            'Counter of successfully processed messages',
            ['component'], namespace=namespace, subsystem=subsystem)


PROMETHEUS = PrometheusMetrics(namespace='gcloud', subsystem='aio')

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

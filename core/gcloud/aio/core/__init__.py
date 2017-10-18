from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-core').version


__all__ = ['__version__']

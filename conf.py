project = 'gcloud-aio'
author = 'TalkIQ'
project_copyright = '2017, TalkIQ'

autoapi_add_toctree_entry = False
autoapi_dirs = [
    'auth',
    'bigquery',
    'datastore',
    'kms',
    'pubsub',
    'storage',
    'taskqueue',
]
autoapi_ignore = [
    '*/tests/*',
]

autodoc_typehints = 'description'

exclude_patterns = ['README.rst', '*/README.rst']

extensions = [
    'autoapi.extension',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

html_theme = 'sizzle'

# Internal build variable to help choose the correct target code for
# syntactically differing code in AIO and REST builds
BUILD_GCLOUD_REST = not __package__ or 'rest' in __package__

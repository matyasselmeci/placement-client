placement-client
================

A Python client library for interacting with the Placement Webapp (pdwebapp).
It enables users to authenticate with the Placement Webapp and submit/manage
jobs on an HTCondor Access Point (AP) via the HTCondor job scheduling system.


Typical workflow
----------------
1. Authenticate with the Placement Webapp using the OAuth2 Device Flow to
   obtain an access token.
2. The token is installed into the local HTCondor tokens directory
   (~/.condor/tokens.d/ or SEC_TOKEN_DIRECTORY if configured).
3. Submit HTCondor jobs to a remote Access Point using the token.


Install requirements
--------------------

For command line client:
- HTCondor Python bindings >= 25.5

For Jupyter notebook:
- IPyWidgets and IPython


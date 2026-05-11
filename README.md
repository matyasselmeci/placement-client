placement-client
================

A Python client for obtaining Placement Tokens for use with HTCondor remote
submission.

Installation
------------

### Requirements

- Python >= 3.6.8
- HTCondor Python bindings >= 25.8

For Jupyter notebook:
- ipywidgets and IPython


### Installation

Enterprise Linux 8 users (RHEL 8, AlmaLinux 8, Rocky 8, etc.) must first
install HTCondor via RPM from the [HTCondor repositories][1].  After setting up
the repositories run:

      yum install python3-htcondor

If you have Python 3.8 or later, you can skip installing the
`python3-htcondor` RPM.

Then, install the placement client via pip:

      pip install git+https://github.com/matyasselmeci/placement-client.git


You will have one new command line tool, `placement-request`,
and one new Python package, `placement_client`, which contains a text-based
user interface.

To install the Jupyter notebook interface, specify the `jupyter` extra as follows:

      pip install "placement-client[jupyter]@git+https://github.com/matyasselmeci/placement-client.git"

^^ TODO test to make sure these work on old and new versions

Usage
-----

### Command-line usage

To request a token from the command line, run:

      placement-request <PLACEMENT_SERVER>

Where `<PLACEMENT_SERVER>` is the hostname of the Placement Server you wish to
request a token from.  For example:

      placement-request demo-ap.chtc.wisc.edu

A URL will be displayed for you to visit in your web browser, as well as a
code to enter on the web page.

      Token requested; please go to

            https://demo-ap.chtc.wisc.edu/auth/code?user_code=ABCD-EFGH

      and use the code "ABCD-EFGH".
      The code will expire at <date/time>.

Visit the web page and log in via your institutional credentials if necessary.
Then, verify the code on the web page matches the code displayed in your
terminal and click "OK".

Then, you will be taken to a screen where you can select the permissions and
project for your token.  Make your selections and click "Make Request".
If the token request is successful, you can return to your terminal,
where you will see a message indicating the token has been saved to disk,
and is ready for use with HTCondor remote submission.

The token is written to your HTCondor user tokens directory
(e.g. `~/.condor/tokens.d/` on Linux) with the filename `Placement.token`.


### Library usage (interactive)

To use the library, import the `placement_client` package and call the
`request_token` function as follows:

```python
from placement_client import request_token

token_path = request_token("placement-server.example.com")
```

The URL to visit will be printed to the terminal, like with the
command-line tool.  Follow the instructions above to obtain the token,
and the path to the installed token file will be returned on success, or
`None` on failure.
The token is written to your HTCondor user tokens directory
(e.g. `~/.condor/tokens.d/` on Linux) with the filename `Placement.token`.

Alternatively, you can use the `request_token_and_return` function to obtain the
token contents as `bytes`, without installing it to disk:

```python
from placement_client import request_token_and_return
token_contents = request_token_and_return("placement-server.example.com")
```


### Library usage (non-interactive, advanced)

To use the library non-interactively, use the `DeviceClient` class to
manually handle the token request workflow, as follows:

```python
from placement_client import DeviceClient
client = DeviceClient("placement-server.example.com")
client.make_request()
```

The URL to visit (with the code already filled in) will be in
`client.verification_uri_complete`.  The code to check against the web page
will be in `client.user_code`.

Afterwards, get the token contents (as `bytes`) as follows:

```python
token_contents = client.poll_for_token()  # poll once
# or
token_contents = client.wait_for_token()  # poll in a loop until token is obtained
```

On failure, these functions will raise a `DeviceClientError` or a subclass of it.

Once the token is obtained, you can write it to disk using the `write_token`
function as follows:

```python
from placement_client import write_token
token_path = write_token(token_filename, token_contents)
```

where `token_filename` is the name of a file to write the token to.
It must not contain any path components, and the token will be written to the user tokens
directory (e.g. `~/.condor/tokens.d/` on Linux).
The path to the installed token file will be returned on success,
or an `OSError` will be raised on failure.


### Jupyter usage

To use the Jupyter widget interface, you must have the ipywidgets package
installed and be running in a Jupyter notebook environment.
Then, import the `placement_client.jupyter` module:

```python
from placement_client import jupyter
```

The module has two sets of widgets:

- `TokenFileUploadWidgets`: for uploading an existing token file to the
   notebook.  Once the file is uploaded, the token will be installed
   to the user tokens directory.

- `DeviceWidgets`: for requesting a new token via the device authorization
   flow.  This is the same workflow as the command-line tool, but in a
   Jupyter widget form.

Use the `TokenFileUploadWidgets` as follows:

```python
widgets = jupyter.TokenFileUploadWidgets()
widgets.display_widgets()
```

Use the `DeviceWidgets` as follows:

```python
widgets = jupyter.DeviceWidgets("placement-server.example.com")
widgets.display_widgets()
```

Click on the "Request Token" button to get started.
Follow the instructions displayed in the widgets to obtain the token.
The token will be saved to the user tokens directory.

[1]: <https://htcondor.readthedocs.io/en/latest/getting-htcondor/from-our-repositories.html>

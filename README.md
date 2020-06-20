# pibells

## Mac Development Environment

### System dependencies

The following packages are required by [pygame](https://www.pygame.org/) which is used to play the sounds.

```shell
brew install sdl sdl_mixer
```

### Python dependencies

Setup a Python virtual environment and install the required Python dependencies:

```shell
pipenv install
```

**Note** - [pygame](https://www.pygame.org/) currently requires a `dev` build to support latest macOS ([see details](https://www.pygame.org/wiki/GettingStarted#Recent%20versions%20of%20Mac%20OS%20X%20require%20pygame%202)).

### Configuration

Run the following command to get the name of the serial input device:

```shell
 ls /dev/tty.*
 ```

Update `device_name` in `pibells.py` accordingly.

### Running

The `keyboard` package must be run as administrator, so you need to run the Python interpretter as `sudo`.

First run the following to get the path to your environment's interpretter:

```shell
which python
```

Then use it as follows:

```shell
sudo /path/to/virtualenvs/for/pibells/bin/python /path/to/pibells/pibells.py
```
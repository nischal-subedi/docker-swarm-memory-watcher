# docker-swarm-memory-watcher
This application polls the docker api in between set intervals to fetch the swarm service memory usage. If memory usage is found to have exceeded a certain threshold the service is reset.

## why?
Obvious question and to answer, because a application is misbehaving and the issue has not been identified so in the meantime this is is the solution help keep things running smoothly.

# how to run?
**First create a virtual environment**
```
python3 -m venv venv
```
*Note: Python is pre-installed in most non-windows distros, but the package required for python virtual environment is not installed by default with the python installation. If found missing an error will be logged when the virtual environment is created. Install it using the command: ```apt install python3.10-venv```*

*Change python version to whatever you have in your system, can be checked with ```python --version```*

**Activate virtual environment**
```
source venv/bin/activate
```
*Note: if you wish to disable venv then run ```deactivate``` within the venv shell.*

**Start the application**
```
python app.py --service service_name --threshold 4098 --interval 10 --log-dir ./swarm-memorywatcher-logs

```

# TODO
- [x] Add automated log rotation and handling
- [] Add option to run service as daemon
- [] Send notification to webhook when threshold is exceeded
- [] Write tests
- [] Fetch service names, threshold values and other input's via .env (using dotenv)

# Thoughts
Was thinking that maybe i'd directly call the ```docker``` command via ```os``` package to perform updates and fetch container stats, but using the ```docker``` package was definitely faster, optimal and the better call for this project. It was easier in getting the stats in the correct form which would otherwise have been a pain to parse from ```docker``` command outputs.
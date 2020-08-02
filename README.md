# mbztool

 moodle backup files extractor (mbz) - usable as command-line-tool or with a webserver

##### Anaconda

Install environment:

```bash
./install.sh -i
```

Convert files of mbz-moodle-backup, e.g. `moodlebackup.mbz` into zip file:

```
conda activate mbz
./mbzbot.py -f moodlebackup.mbz
```

##### System python

Install packages:

```
pip install -r requirements.txt
```

Convert:

```bash
./mbzbot.py -f moodlebackup.mbz
```

##### Deploy as system script

```bash
./install.sh -s
```

##### Deploy as docker image

Set up the environment and the docker-compose file. If you do not use a public accessible server, just ignore the domain input question.

```bash
./deploy.sh
```

Optional: Build the docker image, otherwise it will be pulled from docker hub

```
./install.sh -b
```

Start the docker image:

```bash
docker-compose up -d
```

##### Syntax

```bash
$ ./mbzbot.py -h
usage: mbzbot.py [-h] [-f F] [-a]

optional arguments:
  -h, --help  show this help message and exit
  -f F        mbz file to extract
  -a          convert all mbz files in current directory
```

```bash
$ ./install.sh -h

install.sh [-h|-i|-p|-u|-s|-b|-e]  -- simple environment installer for mbz environment and docker image builder

where:
    -h  show this help text
    -i	install conda environment and packages from environment.yml
    -p	install pip packages from requirement.txt
    -u  remove conda environment
    -s  copy script to /usr/local/bin
    -b  build docker image
    -e	create environment.xml from anaconda environment
```

##### Credits

Thanks to  https://github.com/Swarthmore/extract-mbz for the inspiration with extracting the mbz files.
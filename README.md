# mbztool

moodle backup files extractor (mbz) - usable as command-line-tool or with a webserver

<img src="web/static/logo.svg" style="zoom:500%;" /> 

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
./install.sh -c
```

##### Deploy as docker image

If you want to run mbztool via a docker webserver, you need docker and docker-compose installed. By running the install script, both will be installed. Also the environment and the docker-compose file gets initialized.

```bash
./install.sh
```

Start the docker image:

```bash
docker-compose up -d
```

##### Syntax

```bash
Usage: ./install.sh -[p|s|b|a|c|h]

   -p,      Install prerequisites (docker, docker-compose)
   -s,      Setup environment
   -b,      Build docker image
   -a,      Create anaconda environment
   -c,      Deploy mbzbot.py as system script
   -h,      Print this help text

If the script will be called without parameters, it will run:
    ./install.sh -p -s -b
```

##### Credits

Thanks to  https://github.com/Swarthmore/extract-mbz for the inspiration with extracting the mbz files.
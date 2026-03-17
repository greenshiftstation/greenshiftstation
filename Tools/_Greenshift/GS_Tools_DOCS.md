# GreenShift Tools
## buildManifest.py
buildManifest runs the packaging and formats into the release folder with metadata that makes it ready to be pushed to our packages server. This is a tool we used for releasing new server and client packages in the release cycle, and is saved here so people can explore how it works, and any downstreams (if we ever have any) can have the tool available if they want to use it with our simplified package server code.

## portContentFiles.py
portContentFiles takes a file argument containing a list of files to port from a different fork, it performs a special python assisted git command called `filter-repo`, which is a "built in" (python assisted, so you have to install a python package) git command that takes a list of files as its argument, and removes everything in the repository that isn't those files and their git history. This is useful for porting content WITH its git history, which is otherwise tedious as fuck for commits that touch files we don't care about. The reason we want the git history is because it makes patching that content with fixes or improvements from its parent fork much easier, nearly as easy as just running the same command again on the file.

With this script, the REQUIRED workflow for porting content is as follows:
- Install python if you don't have it
- Install python virtual environment support if you don't have it
- Install pip if you don't have it (pip is a python package manager)
- Set up a virtual environment for this repository
    `python3 -m venv venv` 
- Activate the virtual environment
    linux or wsl: `source ./venv/bin/activate`
    windows: `.\venv\Scripts\Activate.ps1` or `venv\Scripts\activate.bat`
- Install the python requirements
    `pip install -r /Tools/_Greenshift/requirements.txt`
- Create a file containing the list of content files you want to pull (follow the format used by the RMC14_UniqueActionSystem.txt file)
- Make sure the repository is locally available with git remote add <arbitrary remote tag> <repository url or ssh>
    for rmc as an example `git remote add rmc git@github.com:RMC-14/RMC-14.git`
- Make sure you have the latest master (or specific branch) to port the content from fetched and locally available
    git fetch <arbitrary remote tag>
    following what we did above for rmc, it would be `git fetch rmc`
- run the script
    linux: `python3 ./Tools/_Greenshift/portContentFiles.py <remote>/<branch> --paths-from-file ./Tools/_Greenshift/ported_file_lists/<file.txt>`
    windows: fuck if I know. but probably something similar.

    so the specific command for the RMC port we have been using as a reference would be
    `python3 ./Tools/_Greenshift/portContentFiles.py rmc/master --paths-from-file ./Tools/_Greenshift/ported_file_lists/RMC14_UniqueActionSystem.txt`

### Things to note
AGPL licensed content will be automatically rejected. I have no desire to be legally required to distribute code to people that ask for it.
This script does not handle EVERYTHING that a port requires
- You should only be using this script to pull the fork specific content files, **NEVER** the fork specific modifications to wizden files. IE: only files within a _ForkName content folder. You will need to manually grab any changes to wizden files that are necessary to make the port work, and those changes to wizden files should be commented correctly
- You should modify any content files that get pulled if they have prototypes, FTL strings, or other values that are not necessary for your specific port to function correctly.
- This script automatically merges all of the fork specific files with their history to the local branch you are currently on, or to the local branch you specify in the args. You should make an additional commit on top of this with your additional changes that are required to make the port work. When you make a PR, **your PR should NOT be to master** - it should be to the port branch that is specific to the sister fork. If such a branch does not exist, request one. But in general, you should already have permission to be doing a port before you start this whole process. 

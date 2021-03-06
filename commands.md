# Common commands

### Command line

| Task   | Command  |
| :----- | :------  |
| Remove directory | `rm -r -f` |
|                  | `-r` recursive (do all directories underneath) |
|                  | `-f` supresses prompt for write protected files (useful for deleting a git repo) |
| Git    | `git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch file.py' --prune-empty --tag-name-filter cat -- --all` then `git push origin --force --all` to remove history of sensitive files |
| Checking jobs | `top` |
|               | `-u STUDENT\\dbirving` (shows just my jobs) |
|               | `-r` (renice the job) |
|               | `-k` (kill the job) |
| Run in background | `nohup nice myscript.py &` |
| Check data size | `du -B GB -c -s` |
|                 | `-B` (units: GB, MB, etc) |
|                 | `-c` (display grand total) |
|                 | `-s` (don't display sub directory totals) |
|                 | `ls -lah` |
| Search for patterns in file | `grep -r 'word' *` |
|                             | `-r` (look through all directories under the current |
| Search for file names | `find . -name *.txt` |
| Cygwin          | `startx` |
|                 | `ssh -Y STUDENT\\dbirving@abyss` |
| Secure copy     | `scp {remote file} {local file destination}` |
|                 | e.g. `scp STUDENT\\dbirving@abyss:~/directory/script.py .` |
| Remove netCDF attribute | `ncatted -O -a missing_value,var,d,,` |
| Check netCDF type | `ncdump -k` (see [details](http://www.unidata.ucar.edu/software/netcdf/docs/faq.html#How-can-I-tell-which-format-a-netCDF-file-uses)) |

### Python

| Task   | Command  |
| :----- | :------  |
| Python debugger | `python -m pdb script.py` |
|                 | `c` continue until crash |
|                 | `s` step |
|                 | `n` next | 
| Expand dimension | `old_array = old_array[numpy.newaxis, ...]` |
|                  | `numpy.repeat(old_array, x_times, axis=0)`  |

### Installing Python stuff

There are essentially 3 ways to install things (see this [blog post](https://livesoncoffee.wordpress.com/2012/10/09/python-setup/) for details):

1. Use apt-get to install packages in the Ubuntu repositories  
   e.g. `sudo apt-get install python-scientific`  
2. Use pip (tool for installing and managing Python packages)  
   e.g. `sudo pip install ipython`  
3. Manually install by downloading the source code  
   e.g. `cd ~/gitLocal` (i.e. directory where you want the code)  
   `git clone https://github.com/DamienIrving/example.git`  
   `cd example`  
   `sudo python setup.py install -cython`  

### Textwrangler

* Change font size (zoom doesn't work): View => text display => show fonts
* Replace tabs with spaces: Text => Detab
* Block indentation: [command] and [ or ]
 

### CMIP tos data

Some of this data are on a triangulated grid. To get them onto a regular lat/lon grid, you need to use the following cdo command (at least that's what they've done at CSIRO)

`cdo remapbil,sftlf.nc tos.nc out.nc`

Note that `sftlf.nc` is the file that it copies the new grid from.

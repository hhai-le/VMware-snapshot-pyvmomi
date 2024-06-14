install pyvim and pyvmomi for your python environment

```bash
python -m pip install pyvim pyvomi
```


run with syntax:
```bash
python main.py --host <vcenter ip> \
               --user <vcenter user> \
               --passwd <vcenter password> \
               --vmname <vm name> \
               --snapshot <snapshot name> \
               [ --state <poweron/poweroff>]
```

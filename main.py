from pyVim import connect
from pyVmomi import vim
from pyVim.task import WaitForTask
from time import localtime, strftime
import ssl
import re
import argparse


def si_connect(host_ip, username, password):
    service_instance = connect.SmartConnect(host=host_ip, user=username, pwd=password, sslContext=ssl._create_unverified_context())
    return service_instance
    
def report(message):
    print(strftime("%a, %d %b %Y %H:%M:%S", localtime()) + " : " + message)

def get_obj(content, vimtype, name):
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            return c
    return None

def get_vm_by_name(content, name):
    return get_obj(content,[vim.VirtualMachine], name)


def find_matching_snapshot(snapshots, regex):
    if snapshots is None:
        return None
    if len(snapshots) < 1:
        return None
    return [s for s in snapshots if re.search(regex, s.name)]


def get_snapshots(rootlist):
    results = []
    for s in rootlist:
        results.append(s)
        results += get_snapshots(s.childSnapshotList)
    return results

def revert_to_snap(content, vmname, snapnameregex):
    report("Get snapshots from %s ..." % vmname)
    vm = get_vm_by_name(content,vmname)
    snaps = get_snapshots(vm.snapshot.rootSnapshotList)
    report("Finding snapshot ...")
    target_snap = find_matching_snapshot(snaps, snapnameregex)
    assert len(target_snap) == 1,\
        "More than one snap identified - confused!\n" +\
        "Please use a more unique string."
    report("Snap found matching name ...")
    thesnap2use = target_snap[0]
    assert thesnap2use is not None
    report("Reverting to snapshot ...")
    WaitForTask(thesnap2use.snapshot.RevertToSnapshot_Task())
    report("  done")
     
def poweron_vm(content,vm_name):
    vm = None
    entity_stack = content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()
        if entity.name == vm_name:
            vm = entity
            del entity_stack[0:len(entity_stack)]
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)
    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
        task = vm.PowerOn()

def poweroff_vm(content,vm_name):
    vm = None
    entity_stack = content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()
        if entity.name == vm_name:
            vm = entity
            del entity_stack[0:len(entity_stack)]
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)
    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        task = vm.PowerOff()
   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",help="ESXi or vCenter IP")
    parser.add_argument("--user",help="ESXi or vCenter username")
    parser.add_argument("--passwd",help="ESXi or vCenter password")
    parser.add_argument("--vmname",help="name of VM machine")
    parser.add_argument("--snapshot",help="name of machine's snapshot")
    parser.add_argument("--state", default="poweron",help="Power state of machine after restoring snapshot")
    args = parser.parse_args()
    service_instance = si_connect(args.host, args.user, args.passwd)
    revert_to_snap(service_instance.content,args.vmname,args.snapshot)
    if args.state == 'poweron':
        poweron_vm(service_instance.content,args.vmname)
    else:
        poweroff_vm(service_instance.content,args.vmname)
    connect.Disconnect(service_instance)

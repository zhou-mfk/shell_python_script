#! /bin/bash
#######################################
# Dell服务器硬件信息收集脚本
#
# @ bingbing.guo@bl.com
# @ 2017.04.25

print_usage() {
    echo ""
    echo "这个脚本通过DELL IDRAC接口的SNMP协议采集服务器当前硬件信息"
    echo "SNMP协议采用版本 2c"
    echo ""
    echo "Usage: $0 <hostname>"
    echo ""
    exit 3
}

if [ $# -ne 1 ] ; then
    print_usage
fi

SNMP_COMMUNITY="public"
HOSTNAME=$1

check_port() {
    /usr/bin/nc -t -w2 $1 161 &> /dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: 161 port is not open."
        exit 5
    fi
}
# check_port $HOSTNAME

SNMPBULKWALKCMD="snmpbulkwalk -v2c -c $SNMP_COMMUNITY -Oqv $HOSTNAME"
SNMPWALKCMD="snmpwalk -v2c -c $SNMP_COMMUNITY $HOSTNAME"
SNMPGETCMD="snmpget -v 2c -c $SNMP_COMMUNITY -Oqv $HOSTNAME"

###检测硬件型号###
GetModel=`$SNMPGETCMD sysName.0`
if [[ ! "$GetModel" =~ "idrac" ]]; then
    echo "Error: $HOSTNAME not the iDrac interface."
    exit 5
fi


###Raid Level数值映射###
DellRaidLevel[1]="Unknown"
DellRaidLevel[2]="RAID-0"
DellRaidLevel[3]="RAID-1"
DellRaidLevel[4]="RAID-5"
DellRaidLevel[5]="RAID-6"
DellRaidLevel[6]="RAID-10"
DellRaidLevel[7]="RAID-50"
DellRaidLevel[8]="RAID-60"
DellRaidLevel[9]="Concatenated RAID 1"
DellRaidLevel[10]="Concatenated RAID 5"

###Disk State数值映射###
DellDracDiskState[1]="Unknown"
DellDracDiskState[2]="Ready"
DellDracDiskState[3]="Online"
DellDracDiskState[4]="Foreign"
DellDracDiskState[5]="Offline"
DellDracDiskState[6]="Blocked"
DellDracDiskState[7]="Failed"
DellDracDiskState[8]="Non-RAID"
DellDracDiskState[9]="Removed"

###统计服务器基础信息###
# DELL 服务器型号
SystemModel=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.1.3.12.0`
# DELL 服务器硬件序列号
AssetTag=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.2.1.1.11.0`
# DELL IDRAC访问地址
AcessIp=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.2.1.1.7.0`
#SystemInfoJson='{"system_info": {"system_model":'$SystemModel',"asset_tag":'$AssetTag',"acess_ip":'$AcessIp'}}'
#echo $SystemInfoJson 
GeneralInfoJson='"general_info": {"system_model":'$SystemModel',"asset_tag":'$AssetTag',"acess_ip":'$AcessIp'}'

###统计CPU信息###
ProcessorCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.4.1100.32.1.7.1 | wc -l`
for snmpindex in `seq 1 $ProcessorCount`; do
    ProcessorCore=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.30.1.18.1.${snmpindex}`
    ProcessorModel=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.30.1.23.1.${snmpindex}`
    ProcessorList="$ProcessorList,"'{"cores":"'$ProcessorCore'","model":'$ProcessorModel'}'
done
#ProcessorJson='{"processor":['${ProcessorList#,}']}'
#echo $ProcessorJson
ProcessorJson='"processor":['${ProcessorList#,}']'


###统计Memory信息###
MemoryCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.4.1100.50.1.8.1 | wc -l`
for snmpindex in `seq 1 $MemoryCount`; do
    MemoryManufacturer=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.50.1.21.1.${snmpindex}`
    MemorySize=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.50.1.14.1.${snmpindex}`
    MemorySpeed=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.50.1.15.1.${snmpindex}`
    MemoryList="$MemoryList,"'{"manufacturer":'$MemoryManufacturer',"size":"'$MemorySize'","speed":"'$MemorySpeed'"}'
done
#MemoryJson='{"memory":['${MemoryList#,}']}'
#echo $MemoryJson
MemoryJson='"memory":['${MemoryList#,}']'

###统计Disk信息###
DiskCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.2 | wc -l`
for snmpindex in `seq 1 $DiskCount`; do
    DiskManufacturer=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.3.${snmpindex}`
    DiskSize=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.11.${snmpindex}`
    DiskState=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.4.${snmpindex}`
    DiskList="$DiskList,"'{"manufacturer":'$DiskManufacturer',"size":"'$DiskSize'","state":"'${DellDracDiskState[$DiskState]}'"}'
done
#DiskJson='{"disk":['${DiskList#,}']}'
#echo $DiskJson
DiskJson='"disk":['${DiskList#,}']'

###统计RAID Controller信息###
RaidControllerCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.5.1.20.130.1.1.2.1 | wc -l`
for snmpindex in `seq 1 $RaidControllerCount`; do
    RaidManufacturer=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.130.1.1.2.1`
    RaidLevel=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.140.1.1.13.${snmpindex}`
    RaidSize=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.140.1.1.6.${snmpindex}`
    RaidList="$RaidList,"'{"manufacturer":'$RaidManufacturer',"level":"'${DellRaidLevel[$RaidLevel]}'","size":"'$RaidSize'"}'
done
#RaidJson='{"raid":['${RaidList#,}']}'
#echo $RaidJson
RaidJson='"raid":['${RaidList#,}']'

###统计Disk Volume信息###
#DiskVolumeCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.4.1100.90.1.2.1 | wc -l`
#for snmpindex in `seq 1 $DiskVolumeCount`; do
#    DiskVolumeSize=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.5.1.20.140.1.1.6.${snmpindex}`
#    DiskVolumeRaidClass=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.90.1.2.1.${snmpindex}`
#
#    DiskVolumeList="$DiskVolumeList,"'{"raid_class":"'"raid-"$DiskVolumeRaidClass'","raid_size":"'$DiskVolumeSize'"}'
#done
#echo $DiskVolumeList

###统计Network Volume信息###
NetworkVolumeCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.4.1100.90.1.2.1 | wc -l`
for snmpindex in `seq 1 $NetworkVolumeCount`; do
    NetworkVolumeName=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.1100.90.1.6.1.${snmpindex}`
    NetworkVolumeList="$NetworkVolumeList,"'{"name":'$NetworkVolumeName'}'
done
#NetworkJson='{"Network":['${NetworkVolumeList#,}']}'
#echo $NetworkJson
NetworkJson='"network":['${NetworkVolumeList#,}']'

###统计HBA卡信息###
HBAVolumeIndex=`$SNMPWALKCMD .1.3.6.1.4.1.674.10892.5.4.1100.80.1.8.1 \
    | grep 'QLogic Corp.' \
    | awk '{split($1,arr,"."); print arr[length(arr)]}'`
if [ -n $HbaVolumeIndex ]; then
    for snmpindex in $HBAVolumeIndex; do
        HBAVolumeName=`$SNMPGETCMD .1.3.6.1.4.1.674.10892.5.4.1100.80.1.9.1.${snmpindex}`
        HBAVolumeList="$HBAVolumeList,"'{"name":'$HBAVolumeName'}'
    done

    #HBAJson='{"HBA":['${HBAVolumeList#,}']}'
    #echo $HBAJson
    HBAJson='"hba":['${HBAVolumeList#,}']'
fi

###Power Supply信息###
PowerSupplyCount=`$SNMPBULKWALKCMD 1.3.6.1.4.1.674.10892.5.4.600.12.1.1.1 | wc -l`
for snmpindex in `seq 1 $PowerSupplyCount`; do
    PowerSupplyMaxPower=`$SNMPGETCMD 1.3.6.1.4.1.674.10892.5.4.600.12.1.6.1.${snmpindex}`

    PowerSupplyList="$PowerSupplyList,"'{"maxpower":"'$PowerSupplyMaxPower'"}'
done
#PowerSupplyJson='{"power":['${PowerSupplyList#,}']}'
#echo $PowerSupplyJson
PowerSupplyJson='"power":['${PowerSupplyList#,}']'

Storages='{'"${GeneralInfoJson},${ProcessorJson},${MemoryJson},${DiskJson},${RaidJson},${RaidJson},${NetworkJson},${HBAJson},${PowerSupplyJson}"'}'
echo $Storages
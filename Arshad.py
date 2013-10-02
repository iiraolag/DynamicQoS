import httplib
import json
import commands
import time
import exceptions
import subprocess
import util
import random
LIMIT1='60000000' #unit: bps
LIMIT2='60000000'  #unit:bps
MAXQUEUE=8
MANAGEMENT_PORT='9999'
def createString(*sargs):
    from cStringIO import StringIO
    file_str= StringIO()
    for i in range(len(sargs)):
        file_str.write(sargs[i])
        file_str.write(",")
    return file_str.getvalue()
    
def joinString(switchIP,mgntPort,interfaceName,qosId1,qosId2,typeQoS,queueId,rateLimit):
    from cStringIO import StringIO
    file_str = StringIO()
    file_str.write("ovs-vsctl --db=tcp:")
    file_str.write(switchIP)
    file_str.write(":")
    file_str.write(mgntPort)
    file_str.write(" -- set Port ")
    file_str.write(interfaceName)
    file_str.write(" qos=")
    file_str.write(qosId1)
    file_str.write(" -- --id=")
    file_str.write(qosId1)
    file_str.write("  create  QoS type=linux-htb other-config:")
    file_str.write(typeQoS)
    file_str.write("=")
    file_str.write(rateLimit)
    file_str.write(" queues=")
    file_str.write(str(queueId))
    file_str.write("=")
    file_str.write(qosId2)
    file_str.write(" -- --id=")
    file_str.write(qosId2)
    file_str.write(" create Queue other-config:")
    file_str.write(typeQoS)
    file_str.write("=")
    file_str.write(rateLimit)
    return file_str.getvalue()
#Queue objectis represented for a queue in an interface of an openvswitch. As openvswitch, a queue is managed based on a uuid. Moreover, when a queue is assigned with a
#quality of service policy, another uuid is created to managed QoS
class Queue(object):
    def __init__(self,switchIP,mgntPort,interfaceName):
        self.switchIP=switchIP
        self.mgntPort=mgntPort
        self.interface=interfaceName
        self.queueId=''
        self.queueStatus='Off'
        self.qosId=''
        self.uuid=''
        self.other_config={}
   
    def set_switchIP(self, ip_address):
        self.switchIP=ip_address
    def get_switchIP(self):
        return self.switchIP
    def set_mgntPort(self, port):
        self.mgntPort=port
    def get_mgntPort(self):
        return self.mgntPort
    def set_interface(self, interfaceName):
        self.interface=interfaceName
    def get_interface(self):
        return self.interface
    def set_queueStatus(self, status):
        self.queueStatus=status
    def get_queueStatus(self):
        return self.queueStatus
    def set_qosId(self, qosName):
        self.qosId=qosName
    def get_qosId(self):
        return self.qosId
    def set_queueId(self, queueId):
        self.queueId=queueId
    def get_queueId(self):
        return self.queueId
    def set_otherConfig(self, configType, configValue):
        self.other_config[configType]=configValue
    def get_otherConfig(self,configType):
        return self.other_config(configType)
    def get_allConfigs(self):
        configs={}
        for item in self.other_config:
            configs[item]=self.get_otherConfig(item)
        return configs
    def del_otherConfig(self, configType):
        del self.other_config[configType]
    def del_allConfig(self):
        for item in self.other_config:
            self.del_otherConfig(item)
    def show_config(self,configType):
        print configType+":"+self.get_otherConfig(configType)
    def show_allConfig(self):
        for item in self.other_config:
            self.show_config(item)
            print "\n"
    def set_uuid(self,sUUID):
        self.uuid=sUUID
    def get_uuid(self):
        return self.uuid
    def enableQoS(self,qosId1,qosId2,typeQoS, rateLimit):
        switchIP=self.get_switchIP()
        interfaceName=self.get_interface()
        mgntPort=self.get_mgntPort()
        queueID=self.get_queueId()
        
        strCmd= joinString(switchIP,mgntPort,interfaceName,qosId1,qosId2,typeQoS,queueID,rateLimit)
        print strCmd
        (status,output) = commands.getstatusoutput(strCmd)
        print status
        print "\n"
        print output
        if status==256:
            sQueueUUID=output.split("\n")[1]
            sQoSUUID=output.split("\n")[0]
            self.set_otherConfig(typeQoS,rateLimit)
            self.set_queueStatus="On"
            self.set_uuid(sQueueUUID)
            print "\n"
            print sQueueUUID
            return (sQueueUUID,sQoSUUID)
        else:
            return ("0","0")
   
    
    def disableQoS(self):
        switchIP=self.get_switchIP()
        interface=self.get_interface()
        mgntPort=self.get_mgntPort()
        uuid=self.get_uuid()
        strCmd= "ovs-vsctl"+" --db=tcp:"+switchIP+":"+mgntPort+" destroy Queue "+uuid
        print strCmd
        (status,output) = commands.getstatusoutput(strCmd)
        print status
        if status==256:
            self.del_allConfig()
            self.set_queueStatus="Off"
            self.set_uuid('')
            return status
        else:
            return 0
    def clear_QoSnQueue(self):
        switchIP=self.get_switchIP()
        mgntPort=self.get_mgntPort()
        interfaceName=self.get_interface()
        strCmd= "ovs-vsctl"+" --db=tcp:"+switchIP+":"+mgntPort+"  --  destroy  QoS "+interfaceName+" -- clear Port "+interfaceName+" qos"
        (status,output)=commands.getstatusoutput(strCmd)
        
        print status
        
        if status==256:
            return status
        else:
            return 0    
    def showQueue(self):
        print "switch ip address:"+self.get_switchIP()
        print "\n"
        print "management Port:"+self.get_mgntPort()
        print "\n"
        print "interface:"+self.get_interface()
        print "\n"
        print "queue ID:"+self.get_queueId()
        print "\n"
        print "queue status:"+self.get_queueStatus()
        print "\n"
        print "Qos Id:"+self.get_qosId()
        print "\n"
        self.show_allConfig()
        
class Interface(object):
    def __init__(self, switchID, switchIP, mgntPort, portNumber, interfaceName):
        self.switchID=switchID
        self.switchIP=switchIP
        self.portNumber=portNumber
        self.interface=interfaceName
        self.mgntPort=mgntPort
        self.Queues={}
        self.mapQIDnQUUID={}
        self.qosNqueueUUID={}
        self.availQID=range(0,8)
        self.numQueues=0
        
    def set_mgntPort(self,mgntPort):
        self.mgntPort=mgntPort
    def get_mgntPort(self):
        return self.mgntPort
    def set_switchIP(self,switchIP):
        self.switchIP=switchIP
    def get_switchIP(self):
        return self.switchIP
    def get_switchID(self):
        return self.switchID
    def set_portNumber(self, portNumber):
        self.portNumber=portNumber
    def get_portNumber(self):
        return self.portNumber
    def get_interface(self):
        return self.interface
    def get_numQueues(self):
        return self.numQueues
    def set_numQueues(self):
        numAvailQueues=self.get_numAvailQueues()
        self.numQueues=8-numAvailQueues
    def pop_availQID(self):
        return self.availQID.pop()
    def append_availQID(self, queueId):
        return self.availQID.append(queueId)
    def get_numAvailQueues(self):
        return len(self.availQID)
    def get_mappedQUUID(self,queueID):
        return self.mapQIDnQUUID[queueID]
    def set_mapQIDnQUUID(self,queueID,queueUUID):
        self.mapQIDnQUUID[queueID]=queueUUID
    def set_qosNqueueUUID(self,qosUUID,queueUUID):
        self.qosNqueueUUID[queueUUID]=qosUUID
    def get_qosUUID(self,queueUUID):
        return self.qosNqueueUUID[queueUUID]
    def set_queue(self,queueUUID,queue):
        self.Queues[queueUUID]=queue
    def get_queue(self,queueUUID):
        return self.Queues[queueUUID]
    def add_queue(self, qosId1,qosId2,typeQoS, rateLimit):
        print "--------------Start adding queue---------------"
        print "\n"
        numAvailQueues=self.get_numAvailQueues()
        if numAvailQueues>0:
            queueID=str(self.pop_availQID())
            print "queueID as the interface"+queueID
            switchIP=self.get_switchIP()
            mgntPort=self.get_mgntPort()
            interfaceName=self.get_interface()
            newQueue=Queue(switchIP,mgntPort,interfaceName)
            newQueue.set_queueId(queueID)
            (queueUUID,qosUUID) = newQueue.enableQoS(qosId1,qosId2,typeQoS, rateLimit)
            if queueUUID !=0:
                self.set_numQueues()
                self.set_queue(queueUUID,newQueue)
                #self.Queues[queueUUID]=newQueue
                #self.mapQIDnQUUID[queueID]=queueUUID
                self.set_mapQIDnQUUID(queueID,queueUUID)
                self.set_qosNqueueUUID(qosUUID,queueUUID)
                return str(queueUUID)
            else:
                return "0"
        return "0"
    def modify_queue(self, queueId, qosId1,qosId2, typeQoS, rateLimit):
        switchIP=self.get_switchIP()
        mgntPort=self.get_mgntPort()
        interfaceName=self.get_interface()
        if queueId in self.mapQIDnQUUID:
            currentUUID=self.get_mappedQUUID(queueId)
            self.delete_queue(currentUUID)
            newUUID=self.add_queue(qosId1,qosId2,typeQoS,rateLimit)
            return str(newUUID)
        else:
            return "0"
    def destroy_qos(self, queueUUID):
        qosUUID=self.get_qosUUID(queueUUID)
        switchIP=self.get_switchIP()
        interface=self.get_interface()
        mgntPort=self.get_mgntPort()
        #queueID=self.get_queueId()
        #strCmd= 'dpctl del-queue '+'tcp:'+self.switchIP+":"+mgntPort+" "+port+" "+ queueID
        #strCmd= "ovs-vsctl"+" --db=tcp:"+switchIP+":"+mgntPort+" -- destroy QoS "+interface+" -- clear Port "+interface+" qos"
        strCmd= "ovs-vsctl"+" --db=tcp:"+switchIP+":"+mgntPort+" destroy QoS "+qosUUID
        print strCmd
        (status,output) = commands.getstatusoutput(strCmd)
        print status
        if status==256:
            del self.qosNqueueUUID[queueUUID]
            return status
        else:
            return 0
    def delete_queue(self, queueUUID):
        destroyQoS=self.destroy_qos(queueUUID)
        print destroyQoS
        queue=self.get_queue(queueUUID)
        queueId=queue.get_queueId()
        deletedQueue=queue.disableQoS()
        if deleteQueue !=0:
            del self.Queues[queueUUID]
            del self.mapQIDnQUUID[queueId]
            self.append_availQID(queueId)
            self.set_numQueues()
    def del_unrefQueue(self, uuid):
        switchIP=self.get_switchIP()
        interface=self.get_interface()
        mgntPort=self.get_mgntPort()
        queue=interface.get_queue(uuid)
        status=queue.disableQoS()
        print status
        
        if status==256:
            return status
        else:
            return 0
    def search_queueByUUID(self,sUUID):
        if sUUID in self.Queues:
            return str(self.get_queue(sUUID))
        else:
            return "0"
            
    def get_listQueues(self):
        switchIP=self.get_switchIP()
        mgntPort=self.get_mgntPort()
        interfaceName=self.get_interface()
        strCmd= "ovs-vsctl"+" --db=tcp:"+switchIP+":"+mgntPort+" list Queue"
        (status,output)=commands.getstatusoutput(strCmd)
        UUIDs=[]
        output=output.split("\n")
        for i in output:
            if "_uuid" in i:
                uuid=i.split(":")[1][1:]
                UUIDs.append(uuid)
        return UUIDs
    def clear_QoSnQueue(self):
        switchIP=self.get_switchIP()
        mgntPort=self.get_mgntPort()
        interfaceName=self.get_interface()
        strCmd= "ovs-vsctl"+" --db=tcp:"+switchIP+":"+mgntPort+"  --  destroy  QoS "+interfaceName+" -- clear Port "+interfaceName+" qos"
        (status,output)=commands.getstatusoutput(strCmd)
        
        print status
        
        if status==256:
            return status
        else:
            return 0
    def update_queueConfig(self):
        UUIDs=self.get_listQueues()
        for item in UUIDs:
            if self.search_queueByUUID(item)==0:
                self.del_unrefQueue(item)
    def show_interface(self):
        pass

class SwitchInfo(object):
    def __init__(self, switchID, switchIP, mgntPort):
        self.switchID=switchID
        self.switchIP=switchIP
        self.mgntPort=mgntPort
        self.interfaces={}
    def set_mgntPort(self,mgntPort):
        self.mgntPort=mgntPort
    def get_mgntPort(self):
        return self.mgntPort
    def set_switchIP(self,switchIP):
        self.switchIP=switchIP
    def get_switchIP(self):
        return self.switchIP
    def get_switchID(self):
        return self.switchID
    def set_interface(self,portNumber, interface):
        self.interfaces[portNumber]=interface
    def get_interface(self, portNumber):
        return self.interfaces[portNumber]
    def get_interfaceName(self,portNumber):
        theInterface=self.get_interface(portNumber)
        theInterfaceName=theInterface.get_interface()
        return theInterfaceName
    def add_interface(self, portNumber, name):
        switchID=self.get_switchID()
        switchIP=self.get_switchIP()
        mgntPort=self.get_mgntPort()
        addedInterface=Interface(switchID,switchIP,mgntPort,portNumber, name)
        self.set_interface(portNumber, addedInterface)
        #self.interfaces[portNumber]=addedInterface
    def show_switchInfo(self):
        switchID=self.get_switchID()
        print switchID
        print ":"
        switchIP=self.get_switchIP()
        print switchIP
        print "\n"
    def resetQoS(self):
        pass
class ControllerManagementTools(object):

    def __init__(self, server):
        self.server = server
        self.switches= {}
        self.switchesCaptured= {}
        self.QueueVsFlow={}
    def get(self, data):
        ret = self.rest_call({}, 'GET')
        return json.loads(ret[2])

    def set(self, data):
        ret = self.rest_call(data, 'POST')
        return ret[0] == 200
    def set_switch(self, switchID, switchInfo):
        self.switches[switchID]=switchInfo
    def get_switch(self, switchID):
        return self.switches[switchID]
    def set_QueueVsFlow(self, sFlow, queueUUID):
        self.QueueVsFlow[sFlow]=queueUUID
    def get_QueueVsFlow(self,sFlow):
        return self.QueueVsFlow[sFlow]
    def set_switchesCapture(self,switchID, capturedInfo):
        self.switchesCaptured[switchID]=capturedInfo
    def get_switchesCapture(self,switchID):
        return self.switchesCaptured[switchID]
    def get_byteCaptured(self,switchID):
        capturedInfo=self.get_switchesCapture(switchID)
        return capturedInfo['byteCaptured']
    def set_byteCaptured(self,switchID,byteCaptured):
        capturedInfo=self.get_switchesCapture(switchID)
        capturedInfo['byteCaptured']=byteCaptured
        
    def get_timeCaptured(self,switchID):
        capturedInfo=self.get_switchesCapture(switchID)
        return capturedInfo['timeCaptured']
    def set_timeCaptured(self,switchID,timeCaptured):
        capturedInfo=self.get_switchesCapture(switchID)
        capturedInfo['timeCaptured']=timeCaptured
    def reset_switchesCaptured(self,switchID):
        self.set_timeCaptured(switchID,0)
        self.set_byteCaptured(switchID,0)
    def remove(self, objtype, data):
        ret = self.rest_call(data, 'DELETE')
        return ret[0] == 200

    def rest_call(self, data, action):
        path = '/wm/staticflowentrypusher/json'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            }
        body = json.dumps(data)
        conn = httplib.HTTPConnection(self.server, 8080)
        conn.request(action, path, body, headers)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()
        return ret
    
    def initializeSwitches(self,mgntPort):
        path ='/wm/core/controller/switches/json'
        conn = httplib.HTTPConnection(self.server, 8080)
        conn.request('GET',path)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        results=ret[2]
        decoded_results= json.loads(results)
        for i in range(len(decoded_results)):
            print "switch interface information \n"
            switchMac=decoded_results[i]['dpid']
            switchIP =decoded_results[i]['inetAddress'].split(":")[0][1:]
            print "switchIP "+switchIP
            print "\n"
            initSwitch= SwitchInfo(switchMac,switchIP,mgntPort)
            #ports={}
            for j in range(0,len(decoded_results[i]['ports'])):
                interfaceName=decoded_results[i]['ports'][j]['name']
                
                portNumber=str(decoded_results[i]['ports'][j]['portNumber'])
                print "portNumber "+portNumber+": "+interfaceName
                print "\n"
                initInterface= Interface(switchMac,switchIP,mgntPort, portNumber,interfaceName)
                initInterface.update_queueConfig()
                initSwitch.add_interface(portNumber, interfaceName)
                #ports[portNumber]=Queues(switchIP,interfacesName)
            self.set_switch(switchMac,initSwitch)
            self.get_switch(switchMac).show_switchInfo()
            #self.switches[switchMac]= initSwitch
            capturedInfo={'timeCaptured':0,'byteCaptured':0}
            self.set_switchesCapture(switchMac, capturedInfo)
            #self.switchesCaptured[switchMac]={'timeCaptured':0,'byteCaptured':0}
            
    def trafficVisor(self, mgntPort, idle_Timeout,sourceIP, destinationIP, typeQoS):
        
        qosQueues={}
        maxRate=0
        #difference=0
        count=0
        queues=[]
        bandwidth=0
        while 1:
            path ='/wm/core/switch/all/flow/json'
            conn = httplib.HTTPConnection(self.server, 8080)
            conn.request('GET',path)
            response = conn.getresponse()
            ret = (response.status, response.reason, response.read())
            #results = json.loads(response)
            #print ret[0]
            #print ret[1]
            results=ret[2]
            byteRate=0
            decoded_results= json.loads(results)
            #priorPacketCount=0
            #priorPacketTime=0
            #print "new while loop"
            #print "\n"
            #switches is an array of switches that need to be configured for QoS
            for i in range(len(decoded_results)):
                #print decoded_results.keys()[i]
                switchID = str(decoded_results.keys()[i])
                numberFlows = len(decoded_results.values()[i])
                flowInfo=decoded_results.values()[i]
                byteCount=range(numberFlows)
                durationSeconds=range(numberFlows)
                #byteRate=0
                port=""
                for j in range(numberFlows):
                    src_IP=flowInfo[j]['match']['networkSource']
                    dst_IP= flowInfo[j]['match']['networkDestination']
                    durationSeconds[j] = flowInfo[j]['durationSeconds']
                    byteCount[j]= flowInfo[j]['byteCount']
                    print src_IP
                    print "\n"
                    print dst_IP
                    print "byteCount : %ld" %byteCount[j]
                    print "byteCaptured : %ld" % self.switchesCaptured[switchID]['byteCaptured']
                    print "timeCaptured : %ld" % self.switchesCaptured[switchID]['timeCaptured']
                    print "durationSeconds: %ld" %durationSeconds[j]
                    #get port value
                    
                    if (src_IP==sourceIP)and (dst_IP==destinationIP):
                        priority=str(flowInfo[j]['priority'])
                        #sflow=createString(switchID,priority,src_IP,dst_IP,idle_Timeout,port)
                        #print "flow : "+sflow
                        #flow.append(sflow)
                        port = str(flowInfo[j]['actions'][0]['port'])
                        byteCaptured=self.get_byteCaptured(switchID)
                        if (byteCaptured==0):
                            print "assign new value for byteCaptured"
                            print "\n"
                            self.set_byteCaptured(switchID,byteCount[j])
                            #self.switchesCaptured[switchID]['byteCaptured']=byteCount[j]
                            print "new value for byteCaptured: %ld" % self.get_byteCaptured(switchID)
                            self.set_timeCaptured(switchID, durationSeconds[j])
                            #self.switchesCaptured[switchID]['timeCaptured']=durationSeconds[j]
                            print "new value for timeCaptured: %ld" % self.get_timeCaptured(switchID)
                            #time.sleep(5)
                        else:
                            byteRate= float((byteCount[j]-self.get_byteCaptured(switchID)))/(durationSeconds[j]-self.get_timeCaptured(switchID))
                            print "byteRate : %f" % byteRate
                            self.set_byteCaptured(switchID,byteCount[j])
                            #self.switchesCaptured[switchID]['byteCaptured']=byteCount[j]
                            self.set_timeCaptured(switchID, durationSeconds[j])
                            
                        print "byte rate %0.2f" % byteRate
                if maxRate==0:
                    maxRate=byteRate
                elif (byteRate>maxRate):
                    print "\n byteRate1: "
                    print byteRate;
                    print "\n";
                    print "byteRate2: ";
                    print maxRate;
                    difference=100*(byteRate-maxRate)/byteRate
                    print "different rate %0.2f" % difference
                    if difference>10:
                        maxRate=byteRate
                        print "\n"
                        print "maxRate:"+str(maxRate)
                        selectedSwitch=self.get_switch(switchID)
                        selectedSwitch.show_switchInfo()
                        sflow=createString(switchID,priority,src_IP,dst_IP,idle_Timeout,port)
                        print "flow : "+sflow
                        qosQueue=Queue(selectedSwitch.get_switchIP(),selectedSwitch.get_mgntPort(),selectedSwitch.get_interfaceName(port))
                        qosQueues[sflow]=qosQueue
            print "number of configured switches: %d" % len(qosQueues)
            if len(qosQueues)>0:            
                for k,v in qosQueues.items():
                    print "switch needs to be configured is: "
                    print "\n"
                    print qosQueues[k].get_switchIP()
                    print "\n"
                    flow=k
                    print flow
                    print "\n"
                    qosQueue=qosQueues[k]
                    bandwidth=long((maxRate+10000000)/10000)*10000
                    limitRate=str(bandwidth)
                    print "limitRate = "+ limitRate
                    switchID=self.add_QoS(mgntPort,flow, qosQueue, typeQoS, limitRate)
                    queues.append(qosQueue)
                    del qosQueues[k]
                    difference=0
                    self.reset_switchesCaptured(switchID)
                    time.sleep(15)
            print "--------------------------------------------------------------------------------------------------------------------\n"
            if byteRate<300000:
                count=count+1
            if count>100:
                count=0
                queuesCopy=queues
                for i in range(len(queues)):
                    queuesCopy[i].clear_QoSnQueue()
                queues=[]
            time.sleep(3)
                #return ret[0]
    def clear_QoS(self,switchID, priority, src_IP,dst_IP,port,idle_Timeout):
        strFlow=switchID+":"+priority+":"+src_IP+":"+dst_IP+":"+port+":"+idle_Timeout
        
        queueUUID=self.get_QueueVsFlow(strFlow)
        theSwitch=self.get_switch(switchID)
        theInterface=theSwitch.get_interface(port)
        theInterface.delete_queue(queueUUID)
        del self.QueueVsFlow[strFlow]
    
    def add_QoS(self,mgntPort, flow, qosQueue,typeQoS, rateLimit):
        print "flow QoS: "+flow
        flowInfo=flow.split(",")
        switchID=flowInfo[0]
        priority=flowInfo[1]
        src_IP=flowInfo[2]
        dst_IP=flowInfo[3]
        idle_Timeout=flowInfo[4]
        port=flowInfo[5]
        qosId1="@qos"+str(random.randint(1,100))
        qosId2=qosId1+"2"
        print "qosID="+qosId1
        print "\n"
        print "port= " + port
        print "\n"
        print "typeQoS is "+typeQoS
        print "rateLimit "+rateLimit
        theSwitch=self.get_switch(switchID)
        theInterface=theSwitch.get_interface(port)
        queueUUID=str(theInterface.add_queue(qosId1,qosId2,typeQoS, rateLimit))
        print "queueUUID = "+queueUUID
        print "\n"
        if queueUUID !=0:
            newQueue=theInterface.get_queue(queueUUID)
            newQueue.showQueue()
            queueID=newQueue.get_queueId()
            installedFlow=self.flowSetup(switchID,priority, src_IP, dst_IP, port, queueID,idle_Timeout)
            self.set_QueueVsFlow(flow,queueUUID)
            return switchID
        else:
            return "0"
    
    def flowSetup(self, switchID, priority, src_IP, dst_IP, port, queueID, idle_timeout):
        #switch='tcp:'+switchIP+":"+mgntPort
        #strCmd= 'dpctl add-flow '+switch+" "+"cookie=0,"+" priority="+priority+', dl_type=0x0800'+', nw_src='+src_IP+', nw_dst='+dst_IP+', idle_timeout='+idle_timeout+', actions=enqueue:'+port+':'+queueID
        instructions="enqueue="+str(port)+":"+str(queueID)
        flow1 = {
        'switch':switchID,
        "name":"new-qos",
        "cookie":"0",
        "priority":priority,
        "src-ip":src_IP,
        "dst-ip":dst_IP,
        "ether-type":"0x0800",
        "idle_timeout":idle_timeout,
        "active":"true",
        "actions":instructions
        }
        #print strCmd
        #(status,output) = commands.getstatusoutput(strCmd)
        #print status
        pusher = self.set(flow1)
        return flow1

def main():
    mgntPort=MANAGEMENT_PORT
    controller = ControllerManagementTools('10.0.1.1')
    controller.initializeSwitches(mgntPort)
    src_IP='192.168.5.2'
    dst_IP='192.168.5.5'
    queueID='1'
    idle_Timeout='5'
    mgntPort=MANAGEMENT_PORT
    typeQoS='max-rate'
    #rateLimit='80000000'
    response = controller.trafficVisor(mgntPort,idle_Timeout,src_IP,dst_IP,typeQoS)

if __name__ =="__main__":
    main()

#!/usr/bin/python

# Todo: better to match various DB antried for a tool on the time stamp
#  rather than on index
#  this will require an additional step - fill a dictionary keyed with this
#  timestamp, then fill the ES data structure for uploading from this dict.


import sys
# this command needs to be here, otherwise imports below will fail
sys.path.append('/usr/lib/esmond')

import time
from esmond.api.client.perfsonar.query import ApiConnect, ApiFilters
import os
import json
import datetime
import pycurl
import copy
import math

ESwebsite_base = os.environ.get('ELASTIC_WEB_BASE','empty')
PassWD = os.environ.get('ELASTIC_WEB_PASS','empty')

filters = ApiFilters()

filters.verbose = True
filters.time_end = time.time()
filters.time_start = filters.time_end - 5*86400
filters.time_start = filters.time_end - 900
filters.time_start = filters.time_end - 1800
# filters.time_start = filters.time_end - 3600

conn = ApiConnect('http://localhost:80/', filters)
data_out = {}
megastructure = []

utcnow = datetime.datetime.utcnow()

summary = {}
sdom_helper = {}
ddom_helper = {}

destination_domain = "none"
source_domain = "none"


def get_domain(hostname):
    """ create a domain for matching latency to bandwidth server
    For addresses, these should differ only in their last number
    for both ipv4 and ipv6
    For DN names, they should differ only in the first part of their
    name, before the first dot. Advantage of name is, that one can
    also match IPv4 and IPv6 """
    
    #if hostname.find('.') > 0:
    #    hostname = hostname.rpartition('.')[0]
    #if hostname.find(':') > 0:
    #    hostname = hostname.rpartition(':')[0]
    dom=hostname.partition('.')[-1]
    if not dom:
        dom=hostname
    return dom


def prep_dataStructure(metadata, timestamp=None):
    if timestamp:
        data_out['posted'] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
    data_out['hostname'] = os.uname()[1]
    data_out['destination_name'] = metadata.input_destination
    data_out['destination_ip'] = metadata.destination
    data_out['source_name'] = metadata.input_source
    data_out['source_ip'] = metadata.source
    data_out['tool'] = metadata.tool_name
    data_out['isIpv6'] = 0
    if ":" in metadata.destination:
        data_out['isIpv6'] = 1

        
def upload_ES(path,data):
    """ path is the suffix for the index and separated with a '/' the doc name
        data is the already flattened json """
        
    print ("going to upload to path %s this json %s" % (path,data))
    if ESwebsite_base != 'empty':
        ESwebsite = ESwebsite_base + path.replace("pscheduler/","") + "/doc"
        print ("about to submit to %s" % ESwebsite)
        
        c = pycurl.Curl()
        c.setopt(c.URL, ESwebsite)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, data or '')
        c.setopt(pycurl.SSL_VERIFYPEER, 1)
        c.setopt(pycurl.SSL_VERIFYHOST, 2)
        c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
        
        c.setopt(pycurl.USERPWD, PassWD)
        c.perform()
        c.close()
        print ("submitted")
    else:
        print ("aborted upload, no ESwebsite_base set")


def fill_data_for_packet_trace(event_record):
    """ fill the ES data structure for packet traces"""
    
    global megastructure
    
    dpay = event_record.get_data()
    for dp in dpay.data:
        data_out['hops'] = []
        missingentries = 0
        missingnames = 0
        missingrtt = 0
        lastrtt = 0
        lengthvecrtt = 0
        aspath=""
        timestamp = dp.ts
        data_out['posted'] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
        for hop in dp.val:
            print "   HOP : ", hop
            tmpstr = {}
            foundrtt = False
            foundname = False
            foundentry = False
            for item in hop:
                if not item == 'as':
                    print " ITEM : ", item, hop[item]
                    tmpstr[item] = hop[item]
                else:
                    for i2 in hop['as']:
                        print " I2 : ", i2, hop['as'][i2]
                        tmpstr[i2] = hop['as'][i2]
                    foundentry = True
                if item == 'hostname':
                    foundname = True
                if item == 'rtt':
                    foundrtt = True
                    lengthvecrtt += 1
                    lastrtt = hop['rtt']
            if not foundentry:
                missingentries += 1
            if not foundname:
                missingnames += 1
            if not foundrtt:
                missingrtt += 1
            if 'number' in tmpstr:
                aspath+=" " + str(tmpstr['number'])
            data_out['hops'].append(copy.deepcopy(tmpstr))
        data_out['missingentries'] = missingentries
        data_out['missingnames'] = missingnames
        data_out['missingrtt'] = missingrtt
        data_out['lastrtt'] = lastrtt
        data_out['nhops'] = lengthvecrtt
        data_out['aspath'] = aspath
        # add average to summary
        if not event_record.event_type in summary[destination_domain][source_domain][isIPv6]:
            summary[destination_domain][source_domain][isIPv6][event_record.event_type] = {}
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['missingentries'] = 0
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['missingnames'] = 0
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['missingrtt'] = 0
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['lastrtt'] = 0
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['array'] = []
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['nhops'] = 0
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['aspath'] = ""
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['ashash'] = ""
            summary[destination_domain][source_domain][isIPv6][event_record.event_type]['norm'] = 0
        
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['missingentries'] += missingentries
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['missingnames'] += missingnames
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['missingrtt'] += missingrtt
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['lastrtt'] += lastrtt
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['array'].append({'data': copy.deepcopy(data_out) })
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['nhops'] += lengthvecrtt
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['aspath'] += "," + aspath
        # add new hash only if different from old string
        newhash=str(abs(hash(aspath))%2**32)
        if newhash != summary[destination_domain][source_domain][isIPv6][event_record.event_type]['ashash']:
            if summary[destination_domain][source_domain][isIPv6][event_record.event_type]['ashash']:
                summary[destination_domain][source_domain][isIPv6][event_record.event_type]['ashash'] += "," + newhash
            else:
                summary[destination_domain][source_domain][isIPv6][event_record.event_type]['ashash'] = newhash
        summary[destination_domain][source_domain][isIPv6][event_record.event_type]['norm'] += 1

        data = json.dumps(data_out)
        megastructure.append({'path': md.tool_name, 'data': data})
        data_out.clear()


def process_results_for_iperf(metadata):
    """ process each metadata record and call functions for all event types
    contained in the metadata record """
    
    global megastructure
    
    prep_dataStructure(metadata)
    for et in metadata.get_all_event_types():
        print " event type : >>", et.event_type, "<<"
        print " data type  : >>", et.data_type, "<<"
        print " base uri   : >>", et.base_uri, "<<"
        print " summaries  : >>", et.summaries, "<<"
        index_name=et.event_type
        # strip 'packets' from event_type "packet-retransmits" and "packet-retransmits-subintervals"
        if index_name.startswith("packet-"):
            index_name=index_name[7:]
        # strip 'subinterval' from event_type "throughput-subinterval" and "packet-retransmits-subintervals"
        if index_name.endswith("-subinterval"):
            index_name=index_name[:12]
            
        if et.event_type in ["throughput", "packet-retransmits"]:
            dpay = et.get_data()
            tp = 0
            for dp in dpay.data:
                timestamp = dp.ts
                data_out['posted'] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
                tp = dp.val
                data_out[index_name] = tp
            if not et.event_type in summary[destination_domain][source_domain][isIPv6]:
                summary[destination_domain][source_domain][isIPv6][et.event_type] = {}
                summary[destination_domain][source_domain][isIPv6][et.event_type][index_name] = 0
                summary[destination_domain][source_domain][isIPv6][et.event_type]['array'] = []
                summary[destination_domain][source_domain][isIPv6][et.event_type]['norm'] = 0

            summary[destination_domain][source_domain][isIPv6][et.event_type][index_name] += tp
            summary[destination_domain][source_domain][isIPv6][et.event_type]['array'].append({'data': copy.deepcopy(data_out) })
            summary[destination_domain][source_domain][isIPv6][et.event_type]['norm'] += 1

        if et.event_type in ["throughput-subintervals", "packet-retransmits-subintervals"]:
            dpay = et.get_data()
            for dp in dpay.data:
                timestamp = dp.ts
                data_out['posted'] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
                if not 'throughput-interval' in data_out:
                    data_out['throughput-interval'] = []
                    for dur in dp.val:
                        print "   DUR : ", dur
                        tmpstr = {}
                        for item in dur:
                            if not item == 'val':
                                tmpstr[item] = dur[item]
                            else:
                                tmpstr[index_name] = dur[item]
                        data_out['throughput-interval'].append(copy.deepcopy(tmpstr))
                else:
                    cnt = 0
                    for dur in dp.val:
                        data_out['throughput-interval'][cnt][index_name] = 0
                        if 'val' in dur:
                            data_out['throughput-interval'][cnt][index_name] = dur['val']

    data = json.dumps(data_out)
    megastructure.append({'path': md.tool_name, 'data': data})
    data_out.clear()


def process_results_for_powstream(metadata):
    """ process each metadata record and call functions for all event types
    contained in the metadata record """

    global megastructure
    
    measurements = {}
    
    for et in metadata.get_all_event_types():
        print " event type : >>", et.event_type, "<<"
        print " data type  : >>", et.data_type, "<<"
        print " base uri   : >>", et.base_uri, "<<"
        print " summaries  : >>", et.summaries, "<<"
        if et.event_type in ["time-error-estimates", "packet-duplicates", "packet-count-sent",
                             "packet-reorders", "packet-count-lost", "packet-loss-rate"]:
            dpay = et.get_data()
            print (et.event_type)
            print (dpay)
            for dp in dpay.data:
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
                if not dp.ts in measurements:
                    measurements[dp.ts] = {}
                measurements[dp.ts][et.event_type] = dp.val
                    
        # calculate average and rms for each minute's worth of data, typically 600 packets
        if et.event_type == "histogram-owdelay":
            dpay = et.get_data()
            print (et.event_type)
            print (dpay)
            for dp in dpay.data:
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
                if not dp.ts in measurements:
                    measurements[dp.ts] = {}
                ent=0
                avg=0
                sqr=0
                rms=0
                for dur in dp.val:
                    print ('DUR %s %s' % (dur, (dp.val)[dur]))
                    avg+=float(dur)*int((dp.val)[dur])
                    sqr+=float(dur)*float(dur)*int((dp.val)[dur])
                    ent+=int((dp.val)[dur])
                if ent > 0:
                    avg/=ent
                    rms=math.sqrt(sqr / ent - avg * avg)
                measurements[dp.ts][et.event_type+'-avg'] = avg
                measurements[dp.ts][et.event_type+'-rms'] = rms
                measurements[dp.ts][et.event_type+'-num'] = ent
                print "OWD : ", avg, rms, ent

        # should usually be empty, not sure what's in there ...
        if et.event_type == "failures":
            dpay = et.get_data()
            print (et.event_type)
            print (dpay)
            for dp in dpay.data:
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
    for m in measurements:
        prep_dataStructure(metadata, m)
        data_out['event_type'] = "owdelay"
        for item in measurements[m]:
            data_out[item] = measurements[m][item]
        #print "DA :",data_out
        data = json.dumps(data_out)
        megastructure.append({'path': md.tool_name, 'data': data})
        
        # add average to summary
        if not et.event_type in summary[destination_domain][source_domain][isIPv6]:
            summary[destination_domain][source_domain][isIPv6][et.event_type] = {}
            summary[destination_domain][source_domain][isIPv6][et.event_type]['histogram-owdelay-avg'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['histogram-owdelay-rms'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['histogram-owdelay-num'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['histogram-owdelay-num'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['time-error-estimates'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['packet-duplicates'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['packet-count-sent'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['packet-reorders'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['packet-count-lost'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['packet-loss-rate'] = 0
            summary[destination_domain][source_domain][isIPv6][et.event_type]['array'] = []
            summary[destination_domain][source_domain][isIPv6][et.event_type]['norm'] = 0

        for item in measurements[m]:
            summary[destination_domain][source_domain][isIPv6][et.event_type][item] += measurements[m][item]
        summary[destination_domain][source_domain][isIPv6][et.event_type]['array'].append({'data': copy.deepcopy(data_out) })
        summary[destination_domain][source_domain][isIPv6][et.event_type]['norm'] += 1
        
        data_out.clear()

################################             

def process_results_for_traceroute(metadata):
    """ process each metadata record and call functions for all event types
    contained in the metadata record """
    
    for et in metadata.get_all_event_types():
        print " event type : >>", et.event_type, "<<"
        print " data type  : >>", et.data_type, "<<"
        print " base uri   : >>", et.base_uri, "<<"
        print " summaries  : >>", et.summaries, "<<"
        if et.event_type == "packet-trace":
            data_out['event_type'] = "packet-trace"
            prep_dataStructure(metadata)
            fill_data_for_packet_trace(et)
        # nothing to process here, empty on my perfsonar
        if et.event_type == "path-mtu":
            dpay = et.get_data()
            print (et.event_type)
            print (dpay)
            for dp in dpay.data:
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"


for md in conn.get_metadata():
    #    print md # debug info in __repr__
    print "destination         : >", md.destination, "<"
    print "event_types         : >", md.event_types, "<"
    print "input_destination   : >", md.input_destination, "<"
    print "input_source        : >", md.input_source, "<"
    print "ip_packet_interval  : >", md.ip_packet_interval, "<"
    print "measurement_agent   : >", md.measurement_agent, "<"
    print "metadata_key        : >", md.metadata_key, "<"
    print "sample_bucket_width : >", md.sample_bucket_width, "<"
    print "source              : >", md.source, "<"
    print "subject type        : >", md.subject_type, "<"
    print "Time duration       : >", md.time_duration, "<"
    print "Tool name           : >", md.tool_name, "<"
    print "URI                 : >", md.uri, "<"

    # prefill data_out strucutere with common information
    prep_dataStructure(md)
    
    # create a domain for matching latency to bandwidth server
    destination_domain = get_domain(md.input_destination)
    source_domain = get_domain(md.input_source)
    
    isIPv6 = False
    # prepare average for summary, by domains
    if not destination_domain in summary:
        summary[destination_domain] = {}
        ddom_helper[destination_domain] = {}
    
    isIPv6 = ":" in md.destination
    if isIPv6:
        ddom_helper[destination_domain]['destination_v6'] = md.destination
    else:
        ddom_helper[destination_domain]['destination'] = md.destination
    ddom_helper[destination_domain]['destination_name'] = md.input_destination
    
    if not source_domain in summary[destination_domain]:
        summary[destination_domain][source_domain] = {}
        sdom_helper[source_domain] = {}
    isIPv6 = ":" in md.source
    if isIPv6:
        sdom_helper[source_domain]['source_v6'] = md.source
    else:
        sdom_helper[source_domain]['source'] = md.source
    sdom_helper[source_domain]['source_name'] = md.input_source
    #data_out['isIpv6'] = 0
    #if isIPv6:
    #    data_out['isIpv6'] = 1
    
    summary[destination_domain][source_domain][isIPv6] = {}

    if md.tool_name == "pscheduler/iperf3":
        process_results_for_iperf(md)
    if md.tool_name == "pscheduler/powstream":
        process_results_for_powstream(md)
    if md.tool_name == "pscheduler/traceroute":
        process_results_for_traceroute(md)

#     and ESwebsite_base != 'empty':
print (len(megastructure))
for item in megastructure:
    print "One: ", item
    upload_ES(str(item['path']),item['data'])
    
#print ("doms")
#print (ddom_helper)
#print (sdom_helper)
# print ("this is the summary")
# print (summary)

print ("this is the summary, pretty printed")
for k0 in summary:
    v0=summary[k0]
    resolve=""
    if 'destination' in ddom_helper[k0]:
        resolve=ddom_helper[k0]['destination'] + " "
    if 'destination_v6' in ddom_helper[k0]:
        resolve+=ddom_helper[k0]['destination_v6']
    print ("destination %s %s (%s)" % (k0,ddom_helper[k0]['destination_name'],resolve))
    for k1 in v0:
        v1=v0[k1]
        resolve=""
        if 'source' in sdom_helper[k1]:
            resolve=sdom_helper[k1]['source'] + " "
        if 'source_v6' in sdom_helper[k1]:
            resolve+=sdom_helper[k1]['source_v6']
        print (" source %s %s (%s)" % (k1,sdom_helper[k1]['source_name'],resolve))
        for k2 in v1:
            v2=v1[k2]
            print ("  IPv6 %s" % k2)
            for k3 in v2:
                v3=v2[k3]
                print ("   what : %s" % k3)
                for k4 in v3:
                    v4=v3[k4]
                    print ("    res : %s %s" % (k4,v4))


data_out.clear()
print ("Going to upload summaries")
# process destination
for k0 in summary:
    v0=summary[k0]
    resolve_d=""
    if 'destination' in ddom_helper[k0]:
        resolve_d=ddom_helper[k0]['destination'] + " "
    if 'destination_v6' in ddom_helper[k0]:
        resolve_d+=ddom_helper[k0]['destination_v6']

    # process source
    for k1 in v0:
        data_out['destination_domain'] = k0
        data_out['destination_machine'] = ddom_helper[k0]['destination_name']
        data_out['destination_ips'] = resolve_d
        
        v1=v0[k1]
        resolve_s=""
        if 'source' in sdom_helper[k1]:
            resolve_s=sdom_helper[k1]['source'] + " "
        if 'source_v6' in sdom_helper[k1]:
            resolve_s+=sdom_helper[k1]['source_v6']
            
        data_out['source_domain'] = k1
        data_out['source_machine'] = sdom_helper[k1]['source_name']
        data_out['source_ips'] = resolve_s
        
        data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
        tool_sep=""
        data_out['tool'] = ""
        
        # is it IPv4 or IPv6 ?
        for k2 in v1:
            v2=v1[k2]
            # print ("  IPv6 %s" % k2)
            isIpv6 = k2
            for k3 in v2:
                v3=v2[k3]
                # print ("   what : %s" % k3)
                tool = k3
                if isIpv6:
                    tool += "-ipv6"
                data_out['tool'] = data_out['tool'] + tool_sep + str(tool)
                tool_sep = ", "
                norm = 1
                if 'norm' in v3:
                    norm = v3['norm']
                for k4 in v3:
                    v4=v3[k4]
                    # print ("    res : %s %s" % (k4,v4))

                    # leave as is:
                    #   ashash aspath
                    # if k4 in ['ashash','aspath']:
                    if not k4 in ['hops','array','norm']:
                        data_out[tool+'_'+k4] = v4
                    # float divide by norm:
                    #   averagertt histogram-owdelay-avg histogram-owdelay-num histogram-owdelay-rms lastrtt throughput time-error-estimates
                    if k4 in ['histogram-owdelay-avg','histogram-owdelay-num','histogram-owdelay-rms','lastrtt','throughput','time-error-estimates']:
                        data_out[tool+'_'+k4] = v4 / norm
                    # int divide with rounding up:
                    #   missingentries missingnames missingrtt nhops norm packet-count-lost packet-count-sent packet-duplicates packet-loss-rate
                    #    packet-reorders retransmits
                    if k4 in ['missingentries','missingnames','missingrtt','nhops','norm','packet-count-lost','packet-count-sent',
                              'packet-duplicates','packet-loss-rate','packet-reorders','retransmits']:
                        data_out[tool+'_'+k4] = math.ceil(v4 / norm)
        print (" to be uploaded : %s", str(data_out))
        data = json.dumps(data_out)
        if ESwebsite_base != 'empty':
            ESwebsite_base = ESwebsite_base.replace("new","summary")
        upload_ES("summary",data)
        data_out.clear()

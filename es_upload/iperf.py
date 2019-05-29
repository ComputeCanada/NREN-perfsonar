#!/usr/bin/python

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

ESwebsite_base = "<add your ELK isntance here>"
PassWD = "<password>"

filters = ApiFilters()

filters.verbose = True
filters.time_end = time.time()
filters.time_start = filters.time_end - 5*86400
filters.time_start = filters.time_end - 900

conn = ApiConnect('http://localhost:80/', filters)
data_out = {}
utcnow = datetime.datetime.utcnow()

for md in conn.get_metadata():
    #    print md # debug info in __repr__
    print "Destination         : >", md.destination, "<"
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

    # data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
    data_out['hostname'] = os.uname()[1]
    data_out['destination_name'] = md.input_destination
    data_out['destination_ip'] = md.destination
    data_out['source_name'] = md.input_source
    data_out['source_ip'] = md.source
    data_out['tool'] = md.tool_name
    submit = False
    for et in md.get_all_event_types():
        print " event type : >>", et.event_type, "<<"
        print " data type  : >>", et.data_type, "<<"
        print " base uri   : >>", et.base_uri, "<<"
        print " summaries  : >>", et.summaries, "<<"
        # dpay = et.get_data()
        # print "  data payload : >>>", dpay.data_type, "<<<"
        # for dp in dpay.data:
        #    print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
        # for summ in et.get_all_summaries():
        #    print "Summary type : ", summ
        #    spay = summ.get_data()
        #    print "  summary payload : >>>", spay.data_type, "<<<"
        #    for sp in spay.data:
        #        print "   actual summary data : >>>>", sp.ts, sp.val, "<<<<"
        if et.event_type == "packet-trace":
            submit = True
            ESwebsite = ESwebsite_base + 'traceroute/traceroute/'
            # data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
            data_out['destination_name'] = md.input_destination
            data_out['destination_ip'] = md.destination
            data_out['source_name'] = md.input_source
            data_out['source_ip'] = md.source
            data_out['tool'] = md.tool_name
            data_out['event_type'] = "traceroute"
            dpay = et.get_data()
            data_out['hops'] = []
            missingentries = 0
            missingnames = 0
            missingrtt = 0
            averagertt = 0
            lengthvecrtt = 0
            for dp in dpay.data:
                utcnow = dp.ts
                data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
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
                            averagertt += hop['rtt']
                            lengthvecrtt += 1
                    if not foundentry:
                        missingentries += 1
                    if not foundname:
                        missingnames += 1
                    if not foundrtt:
                        missingrtt += 1
                    data_out['hops'].append(copy.deepcopy(tmpstr))
                data_out['missingentries'] = missingentries
                data_out['missingnames'] = missingnames
                data_out['missingrtt'] = missingrtt
                data_out['averagertt'] = -1
                if lengthvecrtt > 0:
                    data_out['averagertt'] = averagertt / lengthvecrtt

        if et.event_type == "throughput":
            submit = True
            ESwebsite = ESwebsite_base + 'iperf3/iperf3/'
            data_out['event_type'] = "throughput"
            dpay = et.get_data()
            for dp in dpay.data:
                utcnow = dp.ts
                data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
                data_out['throughput'] = dp.val
                # for hop in dp.val:
                #    print "   HOP : ", hop
                #    l = {}
                #    for item in hop:
                #        if not item == 'as':
                #            print " ITEM : ", item, hop[item]
                #            l[item] = hop[item]
                #        else:
                #            for i2 in hop['as']:
                #                print " I2 : ", i2, hop['as'][i2]
                #                l[i2] = hop['as'][i2]
                #    data_out['hops'].append(copy.deepcopy(l))
        if et.event_type == "packet-retransmits":
            submit = True
            ESwebsite = ESwebsite_base + 'iperf3/iperf3/'
            data_out['event_type'] = "throughput"
            dpay = et.get_data()
            for dp in dpay.data:
                utcnow = dp.ts
                data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
                print "   actual data : >>>>", dp.ts, dp.val, "<<<<"
                data_out['retransmits'] = dp.val

        if et.event_type == "throughput-subintervals":
            submit = True
            ESwebsite = ESwebsite_base + 'iperf3/iperf3/'
            data_out['event_type'] = "throughput"
            dpay = et.get_data()
            for dp in dpay.data:
                utcnow = dp.ts
                data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
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
                                tmpstr['throughput'] = dur[item]
                        data_out['throughput-interval'].append(copy.deepcopy(tmpstr))
                else:
                    cnt = 0
                    for dur in dp.val:
                        data_out['throughput-interval'][cnt]['throughput'] = 0
                        if 'val' in dur:
                            data_out['throughput-interval'][cnt]['throughtput'] = dur['val']

        if et.event_type == "packet-retransmits-subintervals":
            submit = True
            ESwebsite = ESwebsite_base + 'iperf3/iperf3/'
            data_out['event_type'] = "throughput"
            dpay = et.get_data()
            for dp in dpay.data:
                utcnow = dp.ts
                data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")
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
                                tmpstr['retransmits'] = dur[item]
                        data_out['throughput-interval'].append(copy.deepcopy(tmpstr))
                else:
                    cnt = 0
                    for dur in dp.val:
                        data_out['throughput-interval'][cnt]['retransmits'] = 0
                        if 'val' in dur:
                            data_out['throughput-interval'][cnt]['retransmits'] = dur['val']
    if submit:
        print data_out
        c = pycurl.Curl()
        data_out['posted'] = utcnow.strftime("%Y-%m-%dT%H:%M:%S")

        data = json.dumps(data_out)
        c.setopt(c.URL, ESwebsite)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, data or '')
        c.setopt(pycurl.SSL_VERIFYPEER, 1)
        c.setopt(pycurl.SSL_VERIFYHOST, 2)
        c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])

        c.setopt(pycurl.USERPWD, PassWD)
        c.perform()
        c.close()

    data_out.clear()

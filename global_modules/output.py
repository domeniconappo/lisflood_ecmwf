# -------------------------------------------------------------------------
# Name:        Output module
# Purpose:
#
# Author:      burekpe
#
# Created:     29.03.2014
# Copyright:   (c) burekpe 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------

from pcraster import*
from pcraster.framework import *
import sys
import os
import string
import math

from global_modules.globals import *
from global_modules.add1 import *


class outputTssMap(object):

    """
    # ************************************************************
    # ***** Output of time series (.tss) and maps*****************
    # ************************************************************
    """

    def __init__(self, out_variable):
        self.var = out_variable

    def initial(self):
        """ initial part of the output module
        """
        binding['Catchments'] = self.var.Catchments #This option does not exist in code!
        binding['1'] = None
        # output for single column eg mapmaximum

        self.var.Tss = {}

        for tss in reportTimeSerieAct.keys():
            where = reportTimeSerieAct[tss]['where'][0]
            outpoints = binding[where]
            if where == "1":
                pass
            elif where == "Catchments":
                outpoints=decompress(outpoints)
            else:
                # read coordinates from settings xml file
                coord = binding[where].split()  # could be gauges, sites, lakeSites etc.
                if len(coord) % 2 == 0:
                    outpoints = valuecell(self.var.MaskMap, coord, outpoints)
                else:
                    try:
                        outpoints = loadmap(where,pcr=True)
                        outpoints = ifthen(outpoints != 0,outpoints)
                        #outpointscm = compress(outpoints)
                          # this is necessary if netcdf maps are loaded !! otherwise strange dis.tss
                    except:
                        msg = "Setting output points\n"
                        raise LisfloodFileError(outpoints,msg)
            #self.var.Tss[tss] = TimeoutputTimeseries(binding[tss], self.var, outpoints, noHeader=Flags['noheader'])

            if option['MonteCarlo']:
                if os.path.exists(os.path.split(binding[tss])[0]):
                    self.var.Tss[tss] = TimeoutputTimeseries(binding[tss].split("/")[-1], self.var, outpoints, noHeader=Flags['noheader'])
                else:
                    msg = "Checking output timeseries \n"
                    raise LisfloodFileError(binding[tss],msg)
            else:
                if os.path.exists(os.path.split(binding[tss])[0]):
                    self.var.Tss[tss] = TimeoutputTimeseries(binding[tss], self.var, outpoints, noHeader=Flags['noheader'])
                else:
                    msg = "Checking output timeseries \n"
                    raise LisfloodFileError(binding[tss],msg)

    def dynamic(self):
        """ dynamic part of the output module
        """

        # ************************************************************
        # ***** WRITING RESULTS: TIME SERIES *************************
        # ************************************************************

        # xxx=catchmenttotal(self.var.SurfaceRunForest * self.var.PixelArea, self.var.Ldd) * self.var.InvUpArea
        # self.var.Tss['DisTS'].sample(xxx)
        # self.report(self.Precipitation,binding['TaMaps'])

        # if fast init than without time series

        if not(option['InitLisfloodwithoutSplit']):

            if Flags['loud']:
                # print the discharge of the first output map loc
                #print " %10.2f"  %cellvalue(maptotal(decompress(eval('self.var.' + reportTimeSerieAct["DisTS"]['outputVar'][0]))),1,1)[0]
                try:
                    print " %10.2f"  %self.var.Tss["DisTS"].firstout(decompress(self.var.ChanQAvg))
                except:
                    pass

            for tss in reportTimeSerieAct.keys():
                # report time series
                what = 'self.var.' + reportTimeSerieAct[tss]['outputVar'][0]
                how = reportTimeSerieAct[tss]['operation'][0]
                if how == 'mapmaximum':
                    changed = compressArray(mapmaximum(decompress(eval(what))))
                    what = 'changed'
                if how == 'total':
                    changed = compressArray(catchmenttotal(decompress(eval(what)) * self.var.PixelAreaPcr, self.var.Ldd) * self.var.InvUpArea)
                    what = 'changed'
                self.var.Tss[tss].sample(decompress(eval(what)))

        # ************************************************************
        # ***** WRITING RESULTS: MAPS   ******************************
        # ************************************************************

        ## started nicely but now it becomes way to complicated, I am not happy about the next part -> has to be chaged

        checkifdouble = []  # list to check if map is reported more than once
        monthly = False
        yearly = False

        # Report END maps
        for maps in reportMapsEnd.keys():
            ## report end map
            try:
                where = os.path.join(str(self.var.currentSampleNumber()), binding[maps].split("/")[-1])
            except:
                where = binding[maps]

            # Output path and name of report map
            what = 'self.var.' + reportMapsEnd[maps]['outputVar'][0]

            if not(where in checkifdouble):
                checkifdouble.append(where)
                # checks if saved at same place, if no: add to list

                if self.var.currentTimeStep() == self.var.nrTimeSteps():
                    # CM mod
                    # CM: Get start date for reporting start step
                    reportStartDate = inttoDate(self.var.currentTimeStep() - 1, self.var.CalendarDayStart)

                    # if suffix with '.' is part of the filename report with
                    # suffix
                    head, tail = os.path.split(where)
                    if '.' in tail:
                        if option['writeNetcdf']:
                            # CM mod: write end map to netCDF file (single)
                            # CM ##########################
                            try:
                                writenet(0, eval(what), where, self.var.DtDay, maps, reportMapsEnd[maps][
                                         'outputVar'][0], reportMapsEnd[maps]['unit'][0], 'd', reportStartDate,
                                         self.var.currentTimeStep(),self.var.currentTimeStep(), flagTime=False)
                            except:
                                print "END",what, where, self.var.DtDay, maps, reportMapsEnd[maps][
                                    'outputVar'][0], reportMapsEnd[maps]['unit'][0], 'd', reportStartDate,
                                self.var.currentTimeStep(),self.var.currentTimeStep()
                            ################################


                        else:
                            report(decompress(eval(what)),where)
                    else:
                        if option['writeNetcdfStack']:
                            # CM ######################
                            try:
                                writenet(0, eval(what), where, self.var.DtDay, maps, reportMapsEnd[
                                         maps]['outputVar'][0], reportMapsEnd[maps]['unit'][0], 'd', reportStartDate,
                                         self.var.currentTimeStep(), self.var.currentTimeStep())
                            except:
                                print "END", what, where, self.var.DtDay, maps, reportMapsEnd[
                                    maps]['outputVar'][0], reportMapsEnd[maps]['unit'][0], 'd', reportStartDate,
                                self.var.currentTimeStep(), self.var.currentTimeStep()
                            ###########################
                        else:
                            self.var.report(decompress(eval(what)), where)


        # Report REPORTSTEPS maps
        for maps in reportMapsSteps.keys():
            # report reportsteps maps
            try:
                where = os.path.join(str(self.var.currentSampleNumber()), binding[maps].split("/")[-1])
            except:
                where = binding[maps]
            what = 'self.var.' + reportMapsSteps[maps]['outputVar'][0]
            if not(where in checkifdouble):
                checkifdouble.append(where)
                # checks if saved at same place, if no: add to list
                if self.var.currentTimeStep() in self.var.ReportSteps:

                  flagcdf = 1  # index flag for writing nedcdf = 1 (=steps) -> indicated if a netcdf is created or maps are appended
                  try:
                      if reportMapsSteps[maps]['monthly'][0] =="True":
                         monthly = True
                         flagcdf = 3 # set to monthly (step) flag
                  except:
                     monthly = False
                  try:
                      if reportMapsSteps[maps]['yearly'][0] =="True":
                         yearly = True
                         flagcdf = 4 # set to yearly (step) flag
                  except:
                     yearly = False

                  if (monthly and self.var.monthend) or (yearly and self.var.yearend) or (monthly==False and yearly==False):
                  # checks if a flag monthly or yearly exists

                    if option['writeNetcdfStack']:
                        # CM mod start
                        # CM: Get start date for reporting start step
                        reportStartDate = inttoDate(self.var.ReportSteps[0]-1,self.var.CalendarDayStart)
                        # CM: get step number for first reporting step
                        reportStepStart = self.var.ReportSteps[0]-self.var.ReportSteps[0]+1
                        # CM: get step number for last reporting step
                        reportStepEnd = self.var.ReportSteps[-1]-self.var.ReportSteps[0]+1


                        # CM #################
                        try:
                            writenet(globals.cdfFlag[flagcdf], eval(what), where, self.var.DtDay, maps, reportMapsSteps[
                                     maps]['outputVar'][0], reportMapsSteps[maps]['unit'][0], 'd', reportStartDate,reportStepStart,reportStepEnd)
                        except:
                            print "REP", what, where, self.var.DtDay, maps, reportMapsSteps[
                            maps]['outputVar'][0], reportMapsSteps[maps]['unit'][0], 'd', reportStartDate,reportStepStart,reportStepEnd
                        ######################
                        # CM mod end
                    else:
                        self.var.report(decompress(eval(what)), where)


        # Report ALL maps
        for maps in reportMapsAll.keys():
            # report maps for all timesteps
            try:
                where = os.path.join(str(self.var.currentSampleNumber()), binding[maps].split("/")[-1])
            except:
                where = binding[maps]
            what = 'self.var.' + reportMapsAll[maps]['outputVar'][0]
            if not(where in checkifdouble):
                checkifdouble.append(where)
                # checks if saved at same place, if no: add to list

                flagcdf = 2  # index flag for writing nedcdf = 1 (=all) -> indicated if a netcdf is created ort maps are appended
                             # cannot check only if netcdf exists, because than an old netcdf will be used accidently
                try:
                   if reportMapsAll[maps]['monthly'][0] =="True":
                      monthly = True
                      flagcdf = 5 # set to monthly flag
                except:
                   monthly = False
                try:
                   if reportMapsAll[maps]['yearly'][0] =="True":
                      yearly = True
                      flagcdf = 6 # set to yearly flag
                except:
                   yearly = False

                if (monthly and self.var.monthend) or (yearly and self.var.yearend) or (monthly==False and yearly==False):
                    # checks if a flag monthly or yearly exists]
                    if option['writeNetcdfStack']:
                        # CM mod start
                        # CM: Get start date for reporting start step
                        reportStartDate = inttoDate(int(binding['StepStart']-1),self.var.CalendarDayStart)
                        # CM: get step number for first reporting step which is always the first simulation step
                        # CM: first simulation step referred to reportStartDate
                        ##reportStepStart = int(binding['StepStart'])
                        reportStepStart = 1
                        # CM: get step number for last reporting step which is always the last simulation step
                        # CM: last simulation step referred to reportStartDate
                        reportStepEnd = int(binding['StepEnd']) - int(binding['StepStart']) + 1

                        # CM #########################
                        try:
                            writenet(globals.cdfFlag[flagcdf], eval(what), where, self.var.DtDay, maps, reportMapsAll[
                                maps]['outputVar'][0], reportMapsAll[maps]['unit'][0], 'd', reportStartDate,reportStepStart,reportStepEnd)
                        except:
                            print "ALL",what, where, self.var.DtDay, maps, reportMapsAll[
                            maps]['outputVar'][0], reportMapsAll[maps]['unit'][0], 'd', reportStartDate,reportStepStart,reportStepEnd
                        ##############################

                        # writenet(globals.cdfFlag[flagcdf], eval(what), where, self.var.currentTimeStep(), maps, reportMapsAll[
                        #     maps]['outputVar'][0], reportMapsAll[maps]['unit'][0], 'f4', self.var.CalendarDayStart)
                    else:
                        self.var.report(decompress(eval(what)), where)


        # set the falg to indicate if a netcdffile has to be created or is only appended
        # if reportstep than increase the counter
        if self.var.currentTimeStep() in self.var.ReportSteps:
            globals.cdfFlag[1] += 1
            if self.var.monthend: globals.cdfFlag[3] += 1
            if self.var.yearend: globals.cdfFlag[4] += 1


        # increase the counter for report all maps
        globals.cdfFlag[2] += 1
        if self.var.monthend: globals.cdfFlag[5] += 1
        if self.var.yearend: globals.cdfFlag[6] += 1


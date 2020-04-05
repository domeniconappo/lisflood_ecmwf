#-------------------------------------------------------------------------------
# Name:        Snow module
# Purpose:
#
# Author:      burekpe
#
# Created:     03/03/2014
# Copyright:   (c) burekpe 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------



from pcraster import*
from pcraster.framework import *
import sys, os, string, math
from time import *


from global_modules.zusatz import *
from global_modules.add1 import *
from global_modules.globals import *

class snow(object):
   """
   # ************************************************************
   # ***** RAIN AND SNOW *****************************************
   # ************************************************************

   # Domain: snow calculations evaluated for center points of 3 sub-pixel
   # snow zones A, B, and C, which each occupy one-third of the pixel surface
   #
   # Variables 'snow' and 'rain' at end of this module are the pixel-average snowfall and rain
   #
   # Zone A: lower third
   # Zone B: center third
   # Zone C: upper third
   """

   def __init__(self, snow_variable):
     self.var=snow_variable

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

   def initial(self):
     """ initial part of the snow module
     """

     self.var.DeltaTSnow=0.9674*loadmap('ElevationStD')*loadmap('TemperatureLapseRate')

       # Difference between (average) air temperature at average elevation of
       # pixel and centers of upper- and lower elevation zones [deg C]
       # ElevationStD:   Standard Deviation of the DEM from Bodis (2009)
       # 0.9674:    Quantile of the normal distribution: u(0,833)=0.9674
       #              to split the pixel in 3 equal parts.
     self.var.SnowDayDegrees = 0.9856
       # day of the year to degrees: 360/365.25 = 0.9856

     self.var.IceDayDegrees = 1.915
       # days of summer (15th June-15th Sept.) to degree: 180/(259-165)
     self.var.SnowSeason = loadmap('SnowSeasonAdj') *0.5
       # default value of range  of seasonal melt factor is set to 1
       # 0.5 x range of sinus function [-1,1]
     self.var.TempSnow = loadmap('TempSnow')
     self.var.SnowFactor = loadmap('SnowFactor')
     self.var.SnowMeltCoef = loadmap('SnowMeltCoef')
     self.var.TempMelt = loadmap('TempMelt')


     SnowCoverAInit=ifthen(defined(self.var.MaskMap),scalar(loadmap('SnowCoverAInitValue')))
     SnowCoverBInit=ifthen(defined(self.var.MaskMap),scalar(loadmap('SnowCoverBInitValue')))
     SnowCoverCInit=ifthen(defined(self.var.MaskMap),scalar(loadmap('SnowCoverCInitValue')))

     self.var.SnowCoverS=[SnowCoverAInit,SnowCoverBInit,SnowCoverCInit]

       # initial snow depth in elevation zones A, B, and C, respectively  [mm]

     self.var.SnowCoverInit=(SnowCoverAInit + SnowCoverBInit + SnowCoverCInit)/3
      # Pixel-average initial snow cover: average of values in 3 elevation zones

     self.null=scalar(0.0)


#--------------------------------------------------------------------------
#--------------------------------------------------------------------------


   def dynamic(self):
     """ dynamic part of the snow module
     """

     SeasSnowMeltCoef = self.var.SnowSeason * np.sin((self.var.CalendarDay-81)* self.var.SnowDayDegrees) + self.var.SnowMeltCoef
     #SeasSnowMeltCoef = self.var.SnowSeason * pcraster.sin((self.var.CalendarDay-81)* self.var.SnowDayDegrees) + self.var.SnowMeltCoef
           # sinus shaped function between the
           # annual minimum (December 21st) and annual maximum (June 21st)
     #SummerSeason = ifthenelse(self.var.CalendarDay > 165,sin((self.var.CalendarDay-165)* self.var.IceDayDegrees ),self.null)
     if (self.var.CalendarDay > 165) and (self.var.CalendarDay < 260) :
        SummerSeason=np.sin((self.var.CalendarDay-165)* self.var.IceDayDegrees)
     else:
        SummerSeason=0

     #SummerSeason = ifthenelse(self.var.CalendarDay > 259,self.null,SummerSeason)
     #SeasSnowMeltCoef = scalar(1.0)
     #SummerSeason = scalar(1.0)



     oneThird=0.33333333333
     Ta=self.var.Tavg
     Pr=self.var.Precipitation
     Delta=self.var.DeltaTSnow
     TSnow=self.var.TempSnow
     SFactor=self.var.SnowFactor
     TempM=self.var.TempMelt
     daydt=self.var.DtDay
     null=self.null


     Snow=null
     Rain=null
     SnowMelt=null
     SnowCover=null

     multIce=7.0*daydt*SummerSeason
     TavgS=[Ta-Delta,Ta,Ta+Delta]


     for i in xrange(3):
        #TavgS=Ta + Delta*(i-1)
           # Temperature at center of each zone (temperature at zone B equals Tavg)
        SnowS = ifthenelse(TavgS[i] < TSnow, SFactor*Pr, null)
           # Precipitation is assumed to be snow if daily average temperature is below TempSnow
           # Snow is multiplied by correction factor to account for undercatch of
           # snow precipitation (which is common)
        RainS=Pr-SnowS
        #RainS = ifthenelse(TavgS[i] >= TSnow, Pr, null)
           # if it's snowing then no rain
        SnowMeltS = (TavgS[i]-TempM)*SeasSnowMeltCoef*(1+0.01*RainS)*daydt

        if i<2: IceMeltS=TavgS[i]*multIce
        else: IceMeltS =Ta*multIce

        SnowMeltS=pcraster.max(pcraster.min(SnowMeltS+IceMeltS,self.var.SnowCoverS[i]),null)
        self.var.SnowCoverS[i] = self.var.SnowCoverS[i] + SnowS - SnowMeltS
        Snow+=SnowS
        Rain+=RainS
        SnowMelt+=SnowMeltS
        SnowCover+=self.var.SnowCoverS[i]

     Snow=Snow*oneThird
     self.var.Rain=Rain*oneThird
     self.var.SnowMelt=SnowMelt*oneThird
     self.var.SnowCover=SnowCover*oneThird


     self.var.TotalPrecipitation += Snow + Rain
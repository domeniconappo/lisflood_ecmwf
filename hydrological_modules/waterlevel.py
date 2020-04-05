# -------------------------------------------------------------------------
# Name:        Water level module
# Purpose:
#
# Author:      burekpe
#
# Created:     06.08.2014
# Copyright:   (c) burekpe 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------


from pcraster import*
from pcraster.framework import *
import sys
import os
import string
import math


from global_modules.zusatz import *
from global_modules.add1 import *
from global_modules.globals import *


class waterlevel(object):

    """
    # ************************************************************
    # ***** WATER LEVEL    *****************************************
    # ************************************************************
    """

    def __init__(self, waterlevel_variable):
        self.var = waterlevel_variable

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

    def initial(self):
        """ initial part of the water level module
        """

        if option['simulateWaterLevels']:
            self.var.FloodPlainWidth = loadmap('FloodPlainWidth')

    def dynamic(self):
        """ dynamic part of the water level module
        """

        # Additional computations for channel and floodplain geometry
        # Activating this option doesn't affect LISFLOOD's behaviour in any way, option only
        # included to allow reporting of water level maps / time series
        # Actual reporting activated using separate options!

        if option['simulateWaterLevels']:

            ChanCrossSectionArea = ifthenelse(self.var.IsChannelKinematic, pcraster.min(self.var.TotalCrossSectionArea,
                                              self.var.TotalCrossSectionAreaBankFull),scalar(0.0))
            # Cross-sectional area for channel only (excluding floodplain) [sq m]
            FloodPlainCrossSectionArea = self.var.TotalCrossSectionArea - ChanCrossSectionArea
            # Floodplain area [sq m]
            ChanWaterDepth = 2*ChanCrossSectionArea/(self.var.ChanUpperWidth+self.var.ChanBottomWidth)
            # Water level in channel [m]
            FloodPlainWaterDepth = FloodPlainCrossSectionArea / self.var.FloodPlainWidth
            # Water level on floodplain [m]
            WaterLevelKin = ChanWaterDepth+FloodPlainWaterDepth
            # Total water level [m]

            self.var.WaterLevel = ifthenelse(self.var.IsChannelKinematic, WaterLevelKin,scalar(0.0))
            # Use WaterLevelKin if kinematic wave routing is used ...

            if option['dynamicWave']:
               self.var.WaterLevel = self.var.WaterLevelDyn
               # ... and WaterLevelDyn if dynamic wave is used (remember WaterLevelDyn has dummy value
               # if dynamic wave is not activated)

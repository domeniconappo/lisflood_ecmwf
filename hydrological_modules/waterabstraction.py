# -------------------------------------------------------------------------
# Name:        Water abstraction module
# Purpose:
#
# Author:      burekpe, rooarie
#
# Created:     13.10.2014
# Copyright:   (c) jrc 2015
# Licence:     <your licence>
# -------------------------------------------------------------------------


from global_modules.add1 import *
import pdb


class waterabstraction(object):

    """
    # ************************************************************
    # ***** Water abstraction ************************************
    # ************************************************************
    """

    def __init__(self, waterabstraction_variable):
        self.var = waterabstraction_variable

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

    def initial(self):
        """ initial part of the water abstraction module
        """

        # self.testmap=windowaverage(self.var.Elevation,5)
        # self.report(self.testmap,"test.map")

# ************************************************************
# ***** WATER USE
# ************************************************************

        if option['wateruse']:
            self.var.WUsePercRemain = loadmap('WUsePercRemain')
            self.var.NoWaterUseSteps = int(loadmap('maxNoWateruse'))
            self.var.GroundwaterBodies = loadmap('GroundwaterBodies')
            self.var.FractionGroundwaterUsed = np.minimum(np.maximum(loadmap('FractionGroundwaterUsed'),globals.inZero),1.0)
            self.var.FractionNonConventionalWaterUsed = loadmap('FractionNonConventionalWaterUsed')
            self.var.FractionLakeReservoirWaterUsed = loadmap('FractionLakeReservoirWaterUsed')
            self.var.EFlowThreshold = loadmap('EFlowThreshold')
            # EFlowThreshold is map with m3/s discharge, e.g. the 10th percentile discharge of the baseline run

            self.var.WUseRegionC = loadmap('WUseRegion').astype(int)
            self.var.IrrigationMult = loadmap('IrrigationMult')


            # ************************************************************
            # ***** water use constant maps ******************************
            # ************************************************************

            self.var.IndustryConsumptiveUseFraction = loadmap('IndustryConsumptiveUseFraction')
            # fraction (0-1)
            self.var.WaterReUseFraction = loadmap('WaterReUseFraction')
            # fraction of water re-used (0-1)
            self.var.EnergyConsumptiveUseFraction = loadmap('EnergyConsumptiveUseFraction')
            # fraction (0-1), value depends on cooling technology of power plants
            self.var.LivestockConsumptiveUseFraction = loadmap('LivestockConsumptiveUseFraction')
            # fraction (0-1)
            self.var.LeakageFraction = np.minimum(np.maximum(loadmap('LeakageFraction')*(1-loadmap('LeakageReductionFraction')),globals.inZero),1.0)
            self.var.DomesticLeakageConstant =  np.minimum(np.maximum(1/(1-self.var.LeakageFraction),globals.inZero),1.0)
            # Domestic Water Abstraction becomes larger in case of leakage
            # LeakageFraction is LeakageFraction (0-1) multiplied by reduction scenario (10% reduction is 0.1 in map)
            # 0.65 leakage and 0.1 reduction leads to 0.585 effective leakage, resulting in 2.41 times more water abstraction
            self.var.DomesticWaterSavingConstant = np.minimum(np.maximum(1-loadmap('WaterSavingFraction'),globals.inZero),1.0)
            # Domestic water saving if in place, changes this value from 1 to a value between 0 and 1, and will reduce demand and abstraction
            # so value = 0.9 if WaterSavingFraction equals 0.1 (10%)
            self.var.DomesticConsumptiveUseFraction = loadmap('DomesticConsumptiveUseFraction')
            # fraction (0-1), typically rather low ~ 0.10
            self.var.LeakageWaterLossFraction = loadmap('LeakageWaterLoss')
            # fraction (0-1), 0=no leakage

            # CM: Initialize water demand. Read from a static map either value or pcraster map or netcdf (single or stack).
            # CM: If reading from NetCDF stack, get time step corresponding to model step.
            # CM: Added management for sub-daily modelling time steps
            # CM: Added possibility to use one single average year to be repeated during the simulation
            if option['useWaterDemandAveYear']:
                # CM: using one water demand average year throughout the model simulation
                self.var.DomesticDemandMM = loadmap('DomesticDemandMaps',timestampflag='closest',averageyearflag=True) * self.var.DtDay
                self.var.IndustrialDemandMM = loadmap('IndustrialDemandMaps',timestampflag='closest',averageyearflag=True) * self.var.DtDay
                self.var.LivestockDemandMM = loadmap('LivestockDemandMaps',timestampflag='closest',averageyearflag=True) * self.var.DtDay
                self.var.EnergyDemandMM = loadmap('EnergyDemandMaps',timestampflag='closest',averageyearflag=True) * self.var.DtDay
            else:
                # CM: using information on water demand from NetCDF files
                self.var.DomesticDemandMM = loadmap('DomesticDemandMaps',timestampflag='closest') * self.var.DtDay
                self.var.IndustrialDemandMM = loadmap('IndustrialDemandMaps',timestampflag='closest') * self.var.DtDay
                self.var.LivestockDemandMM = loadmap('LivestockDemandMaps',timestampflag='closest') * self.var.DtDay
                self.var.EnergyDemandMM = loadmap('EnergyDemandMaps',timestampflag='closest') * self.var.DtDay


            if option['groundwaterSmooth']:
                self.var.GroundwaterBodiesPcr = decompress(self.var.GroundwaterBodies)
                self.var.groundwaterCatch = boolean(decompress((self.var.GroundwaterBodies *self.var.Catchments).astype(int)))
                # nominal(scalar(GroundwaterBodies)*scalar(self.var.Catchments));
                # smoothing for groundwater to correct error by using windowtotal, based on groundwater bodies and catchments
                self.var.LZSmoothRange = loadmap('LZSmoothRange')


            if option['wateruseRegion']:
                WUseRegion = nominal(loadmap('WUseRegion',pcr=True))
                pitWuse1 =  ifthen(self.var.AtLastPoint <> 0,pcraster.boolean(1))
                pitWuse1b = ifthen(defined(pitWuse1),WUseRegion)
                # use every existing pit in the Ldd and number them by the water regions
                # coastal water regions can have more than one pit per water region

                pitWuseMax = areamaximum(self.var.UpArea,WUseRegion)
                pitWuse2 = ifthen(pitWuseMax == self.var.UpArea,WUseRegion)
                # search outlets in the inland water regions by using the maximum  upstream area as criterium

                pitWuse3 = downstream(self.var.LddStructuresKinematic,WUseRegion)
                pitWuse3b = ifthen(pitWuse3 != WUseRegion,WUseRegion)
                # search point where ldd leaves a water region

                pitWuse=cover(pitWuse1b,pitWuse2,pitWuse3b,nominal(0))
                # join all sources of pits

                LddWaterRegion=lddrepair(ifthenelse(pitWuse == 0,self.var.LddStructuresKinematic,5))
                # create a Ldd with pits at every water region outlet
                # this results in a interrupted ldd, so water cannot be transfered to the next water region

                lddC = compressArray(LddWaterRegion)
                inAr = decompress(np.arange(maskinfo['mapC'][0],dtype="int32"))
                # giving a number to each non missing pixel as id
                self.var.downWRegion = (compressArray(downstream(LddWaterRegion,inAr))).astype(np.int32)
                # each upstream pixel gets the id of the downstream pixel
                self.var.downWRegion[lddC==5] = maskinfo['mapC'][0]
                # all pits gets a high number


                # ************************************************************
                # ***** OUTFLOW AND INFLOW POINTS FOR WATER REGIONS **********
                # ************************************************************

                self.var.WaterRegionOutflowPoints = ifthen(pitWuse != 0,boolean(1))
	            # outflowpoints to calculate upstream inflow for balances and Water Exploitation Index
	            # both inland outflowpoints to downstream subbasin, and coastal outlets

                WaterRegionInflow1=boolean(upstream(self.var.LddStructuresKinematic,cover(scalar(self.var.WaterRegionOutflowPoints),0)))
                self.var.WaterRegionInflowPoints=ifthen(WaterRegionInflow1,boolean(1))
	            # inflowpoints to calculate upstream inflow for balances and Water Exploitation Index

            else:
                self.var.downWRegion = self.var.downstruct.copy()
                self.var.downWRegion = self.var.downWRegion.astype(np.int32)


# --------------------------------------------------------

            # ************************************************************
            # ***** Initialising cumulative output variables *************
            # ************************************************************

            # These are all needed to compute the cumulative mass balance error

            self.var.wateruseCum = globals.inZero.copy()
            # water use cumulated amount
            self.var.WUseAddM3Dt = globals.inZero.copy()
            # CM
            self.var.WUseAddM3 = globals.inZero.copy()

            self.var.IrriLossCUM = globals.inZero.copy()
            # Cumulative irrigation loss [mm]
            # abstractionCUM = globals.inZero.copy() # not used
            # Cumulative abstraction from surface water [mm]

            IrrigationWaterDemand = globals.inZero.copy()
            # if not(option['riceIrrigation']):
            #     self.var.TotalAbstractionFromSurfaceWaterM3 = globals.inZero.copy()
            #     # rice irrigation introduced and filled this already
            # CM mod start
            self.var.TotalAbstractionFromSurfaceWaterM3 = globals.inZero.copy()
            # CM mod end


            self.var.TotalAbstractionFromGroundwaterM3 = globals.inZero.copy()
            IrrigationAbstractionFromGroundwaterM3 = globals.inZero.copy()
            # LiveDomAbstractionFromGroundwaterM3 = globals.inZero.copy()   # not used
            self.var.TotalIrrigationAbstractionM3 = globals.inZero.copy()
            self.var.TotalPaddyRiceIrrigationAbstractionM3 = globals.inZero.copy()
            self.var.TotalLivestockAbstractionM3 = globals.inZero.copy()

            self.var.IrrigationType = loadmap('IrrigationType')
            self.var.IrrigationEfficiency = loadmap('IrrigationEfficiency')
            self.var.ConveyanceEfficiency = loadmap('ConveyanceEfficiency')

            self.var.GroundwaterRegionPixels= np.take(np.bincount(self.var.WUseRegionC,weights=self.var.GroundwaterBodies),self.var.WUseRegionC)
            self.var.AllRegionPixels= np.take(np.bincount(self.var.WUseRegionC,weights=self.var.GroundwaterBodies*0.0+1.0),self.var.WUseRegionC)
            self.var.RatioGroundWaterUse = self.var.AllRegionPixels/(self.var.GroundwaterRegionPixels+0.01)
            self.var.FractionGroundwaterUsed = np.minimum(self.var.FractionGroundwaterUsed*self.var.RatioGroundWaterUse, 1-self.var.FractionNonConventionalWaterUsed)
            # FractionGroundwaterUsed is a percentage given at national scale
            # since the water needs to come from the GroundwaterBodies pixels, the fraction needs correction for the non-Groundwaterbodies; this is done here


            #################################################################
            # CINZIA TO BE REMOVED
            # self.var.FractionGroundwaterUsed = 0.1
            #################################################################


            # CM
            self.var.EFlowIndicator = globals.inZero.copy()
            self.var.ReservoirAbstractionM3 = globals.inZero.copy()
            self.var.PotentialSurfaceWaterAvailabilityForIrrigationM3 = globals.inZero.copy()
            self.var.LakeAbstractionM3 = globals.inZero.copy()
            self.var.FractionAbstractedFromChannels = globals.inZero.copy()
            self.var.AreatotalIrrigationUseM3 = globals.inZero.copy()
            self.var.totalAddM3 = globals.inZero.copy()
            self.var.TotalDemandM3 = globals.inZero.copy()



    def dynamic(self):
        """ dynamic part of the water use module
            init water use before sub step routing
        """

        if option['wateruse']:

        # ************************************************************
        # ***** READ WATER DEMAND DATA *****************************
        # ************************************************************

            if option['TransientWaterDemandChange']:
                if option['readNetcdfStack']:
                    if option['useWaterDemandAveYear']:
                        # CM: using average year in NetCDF file format
                        self.var.DomesticDemandMM = readnetcdf(binding['DomesticDemandMaps'], self.var.currentTimeStep(),timestampflag='closest',averageyearflag=True) * self.var.DtDay
                        self.var.IndustrialDemandMM = readnetcdf(binding['IndustrialDemandMaps'], self.var.currentTimeStep(),timestampflag='closest',averageyearflag=True) * self.var.DtDay
                        self.var.LivestockDemandMM = readnetcdf(binding['LivestockDemandMaps'], self.var.currentTimeStep(),timestampflag='closest',averageyearflag=True) * self.var.DtDay
                        self.var.EnergyDemandMM = readnetcdf(binding['EnergyDemandMaps'], self.var.currentTimeStep(),timestampflag='closest',averageyearflag=True) * self.var.DtDay
                    else:
                        # CM: Read from stack of maps in NetCDF format. Get time step corresponding to model step.
                        #self.var.DomesticDemandMM = readnetcdfsparse(binding['DomesticDemandMaps'], self.var.currentTimeStep(), self.var.DomesticDemandMM)
                        #self.var.IndustrialDemandMM = readnetcdfsparse(binding['IndustrialDemandMaps'], self.var.currentTimeStep(), self.var.IndustrialDemandMM)
                        #self.var.LivestockDemandMM = readnetcdfsparse(binding['LivestockDemandMaps'], self.var.currentTimeStep(), self.var.LivestockDemandMM)
                        #self.var.EnergyDemandMM = readnetcdfsparse(binding['EnergyDemandMaps'], self.var.currentTimeStep(), self.var.EnergyDemandMM)
                        # CM: added management for sub-daily model time steps
                        self.var.DomesticDemandMM = readnetcdf(binding['DomesticDemandMaps'], self.var.currentTimeStep(),timestampflag='closest') * self.var.DtDay
                        self.var.IndustrialDemandMM = readnetcdf(binding['IndustrialDemandMaps'], self.var.currentTimeStep(),timestampflag='closest') * self.var.DtDay
                        self.var.LivestockDemandMM = readnetcdf(binding['LivestockDemandMaps'], self.var.currentTimeStep(),timestampflag='closest') * self.var.DtDay
                        self.var.EnergyDemandMM = readnetcdf(binding['EnergyDemandMaps'], self.var.currentTimeStep(),timestampflag='closest') * self.var.DtDay
                else:
                    # CM: Read from stack of maps in Pcraster format
                    self.var.DomesticDemandMM = readmapsparse(binding['DomesticDemandMaps'], self.var.currentTimeStep(), self.var.DomesticDemandMM) * self.var.DtDay
                    self.var.IndustrialDemandMM = readmapsparse(binding['IndustrialDemandMaps'], self.var.currentTimeStep(), self.var.IndustrialDemandMM) * self.var.DtDay
                    self.var.LivestockDemandMM = readmapsparse(binding['LivestockDemandMaps'], self.var.currentTimeStep(), self.var.LivestockDemandMM) * self.var.DtDay
                    self.var.EnergyDemandMM = readmapsparse(binding['EnergyDemandMaps'], self.var.currentTimeStep(), self.var.EnergyDemandMM) * self.var.DtDay


            # ************************************************************
            # ***** LIVESTOCK ********************************************
            # ************************************************************

            LivestockAbstractionMM = self.var.LivestockDemandMM
            self.var.LivestockConsumptiveUseMM =  LivestockAbstractionMM * self.var.LivestockConsumptiveUseFraction
            # the amount that is not returned to the hydrological cycle

            LivestockAbstractionFromGroundwaterM3= np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed*self.var.LivestockConsumptiveUseMM* self.var.MMtoM3,globals.inZero)
            LivestockAbstractionFromNonConventionalWaterM3= self.var.FractionNonConventionalWaterUsed * self.var.LivestockConsumptiveUseMM * self.var.MMtoM3
            LivestockAbstractionFromSurfaceWaterM3=self.var.LivestockConsumptiveUseMM*self.var.MMtoM3 - LivestockAbstractionFromGroundwaterM3 - LivestockAbstractionFromNonConventionalWaterM3

            self.var.TotalLivestockAbstractionM3 += LivestockAbstractionFromGroundwaterM3 + LivestockAbstractionFromSurfaceWaterM3 + LivestockAbstractionFromNonConventionalWaterM3


            # ************************************************************
            # ***** DOMESTIC *********************************************
            # ************************************************************

            DomesticAbstractionMM = self.var.DomesticDemandMM  * self.var.DomesticWaterSavingConstant * self.var.DomesticLeakageConstant
            # Domestic Water Abstraction (mm per day), already taking into account water saving in households and leakage of the supply network
            # Domestic water abstraction is larger if there is leakage, but is smaller if there is water savings
            LeakageMM = (self.var.DomesticLeakageConstant-1) * self.var.DomesticDemandMM  * self.var.DomesticWaterSavingConstant
            # Leakage in mm per day
            LeakageLossMM = LeakageMM * self.var.LeakageWaterLossFraction
            # The leakage amount that is lost (evaporated)
            LeakageSoilMM = LeakageMM - LeakageLossMM
            self.var.DomesticConsumptiveUseMM = self.var.DomesticDemandMM * self.var.DomesticWaterSavingConstant * self.var.DomesticConsumptiveUseFraction + LeakageLossMM
            # DomesticConsumptiveUseMM is the amount that disappears from the waterbalance
            # Assumption here is that leakage is partially lost/evaporated (LeakageWaterLoss fraction)

            DomAbstractionFromGroundwaterM3= np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * self.var.DomesticConsumptiveUseMM* self.var.MMtoM3,globals.inZero)
            DomAbstractionFromNonConventionalWaterM3= self.var.FractionNonConventionalWaterUsed * self.var.DomesticConsumptiveUseMM*self.var.MMtoM3
            DomAbstractionFromSurfaceWaterM3=self.var.DomesticConsumptiveUseMM* self.var.MMtoM3 - DomAbstractionFromGroundwaterM3 - DomAbstractionFromNonConventionalWaterM3


            # ************************************************************
            # ***** INDUSTRY *********************************************
            # ************************************************************

            IndustrialAbstractionMM = self.var.IndustrialDemandMM * (1-self.var.WaterReUseFraction)
            self.var.IndustrialConsumptiveUseMM = IndustrialAbstractionMM * self.var.IndustryConsumptiveUseFraction
            # IndustrialAbstractionMM = scalar(timeinputsparse(IndustrialAbstractionMaps)) * (1-WaterReUseFraction);
	        # Industrial Water Demand (mm per day)
	        # WaterReUseFraction: Fraction of water re-used in industry (e.g. 50% = 0.5 = half of the water is re-used, used twice (baseline=0, maximum=1)
          	# IndustrialConsumptiveUseMM is the amount that evaporates etc
            # only 1 map so this one is loaded in initial!

            IndustrialWaterAbstractionM3 = self.var.IndustrialConsumptiveUseMM * self.var.MMtoM3
            IndustrialAbstractionFromGroundwaterM3 = np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * IndustrialWaterAbstractionM3,globals.inZero)
            IndustrialAbstractionFromNonConventionalWaterM3 = self.var.FractionNonConventionalWaterUsed * IndustrialWaterAbstractionM3
            IndustrialAbstractionFromSurfaceWaterM3 = IndustrialWaterAbstractionM3 - IndustrialAbstractionFromGroundwaterM3 - IndustrialAbstractionFromNonConventionalWaterM3



            # ************************************************************
            # ***** ENERGY ***********************************************
            # ************************************************************

            EnergyAbstractionMM = self.var.EnergyDemandMM
            self.var.EnergyConsumptiveUseMM = EnergyAbstractionMM * self.var.EnergyConsumptiveUseFraction
            # EnergyConsumptiveUseMM is the amount that evaporates etc

            EnergyAbstractionFromSurfaceWaterM3 = self.var.EnergyConsumptiveUseMM * self.var.MMtoM3
            # all taken from surface water



            # ************************************************************
            # ***** IRRIGATION *******************************************
            # ************************************************************

            # water demand from loop3 = irrigated zone
            self.var.Ta[2] = np.maximum(np.minimum(self.var.RWS[2] * self.var.TranspirMaxCorrected, self.var.W1[2] - self.var.WWP1[2]), globals.inZero)

            IrrigationWaterDemandMM = (self.var.TranspirMaxCorrected-self.var.Ta[2]) * self.var.IrrigationMult
            #  a factor (IrrigationMult) add some water (to prevent salinisation)
            # irrigationWaterNeed assumed to be equal to potential transpiration minus actual transpiration
            # in mm here, assumed for the entire pixel, thus later to be corrected with IrrigationFraction
            # IrrigationType (value between 0 and 1) is used here to distinguish between additional adding water until fieldcapacity (value set to 1) or not (value set to 0)
            IrrigationWaterDemandMM = np.where(self.var.FrostIndex > self.var.FrostIndexThreshold,globals.inZero,IrrigationWaterDemandMM)
            # IrrigationWaterDemand is 0 when soil is frozen

            IrrigationWaterAbstractionMM = np.where((self.var.IrrigationEfficiency * self.var.ConveyanceEfficiency) > 0,
                                                    IrrigationWaterDemandMM * self.var.IrrigationFraction / (self.var.IrrigationEfficiency * self.var.ConveyanceEfficiency),
                                                    globals.inZero)
            self.var.IrrigationWaterAbstractionM3 = np.maximum(IrrigationWaterAbstractionMM * self.var.MMtoM3, globals.inZero)
            # irrigation efficiency max 1, ~0.90 drip irrigation, ~0.75 sprinkling
	 	    # conveyance efficiency, around 0.80 for average channel
		    # multiplied by actual irrigated area (fraction) and cellsize(MMtoM3) in M3 per pixel

            IrrigationAbstractionFromGroundwaterM3 = np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * self.var.IrrigationWaterAbstractionM3,globals.inZero)
            IrrigationAbstractionFromSurfaceWaterM3 = np.maximum(self.var.IrrigationWaterAbstractionM3 - IrrigationAbstractionFromGroundwaterM3,globals.inZero)

            # pdb.set_trace()


            # ************************************************************
            # ***** TOTAL ABSTRACTIONS (DEMANDED) ************************
            # ************************************************************

            self.var.TotalAbstractionFromGroundwaterM3 = IrrigationAbstractionFromGroundwaterM3 + DomAbstractionFromGroundwaterM3 + LivestockAbstractionFromGroundwaterM3 + IndustrialAbstractionFromGroundwaterM3
            self.var.TotalAbstractionFromSurfaceWaterM3 =  IrrigationAbstractionFromSurfaceWaterM3 + self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3 + DomAbstractionFromSurfaceWaterM3 + LivestockAbstractionFromSurfaceWaterM3 + IndustrialAbstractionFromSurfaceWaterM3 + EnergyAbstractionFromSurfaceWaterM3

            PaddyRiceWaterAbstractionFromSurfaceWaterMM = self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3 * self.var.M3toMM
                #taken from paddy rice routine

            self.var.TotalDemandM3 = (LivestockAbstractionMM + DomesticAbstractionMM + IrrigationWaterAbstractionMM + PaddyRiceWaterAbstractionFromSurfaceWaterMM + IndustrialAbstractionMM + EnergyAbstractionMM) * self.var.MMtoM3

            self.var.TotalIrrigationAbstractionM3 += IrrigationAbstractionFromGroundwaterM3 + IrrigationAbstractionFromSurfaceWaterM3
            self.var.TotalPaddyRiceIrrigationAbstractionM3 += self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3
                # totals calculated for reporting, for comparing with national reported values and possible calibration

            # ************************************************************
            # ***** ABSTRACTION FROM GROUNDWATER *************************
            # ************************************************************

            self.var.LZ = self.var.LZ - self.var.TotalAbstractionFromGroundwaterM3*self.var.M3toMM
            self.var.IrriLossCUM = self.var.IrriLossCUM + self.var.TotalAbstractionFromGroundwaterM3
            # Abstraction is taken from lower groundwater zone
            # for mass balance calculation also summed up in IrrilossCUM (in M3)


            # ***********************************************************************
            # ***** ABSTRACTION SUPPLIED BY NONCONVENTIONAL SOURCES (DESALINATION) **
            # ***********************************************************************

            NonConventionalWaterM3 = DomAbstractionFromNonConventionalWaterM3 + LivestockAbstractionFromNonConventionalWaterM3 + IndustrialAbstractionFromNonConventionalWaterM3
            # Non conventional water producted is not abstracted from surface water


            # ************************************************************
            # ***** ABSTRACTION FROM LAKES AND RESERVOIRS ****************
            # ************************************************************
            # CM mod start
            if option['simulateReservoirs']:
                # CM
                # PotentialAbstractionFromReservoirsM3 = np.minimum(0.02 * self.var.ReservoirStorageM3, 0.01*self.var.TotalReservoirStorageM3C) #original
                PotentialAbstractionFromReservoirsM3 = np.minimum(0.02 * self.var.ReservoirStorageM3, 0.01*self.var.TotalReservoirStorageM3C) * self.var.DtDay

                PotentialAbstractionFromReservoirsM3 = np.where(np.isnan(PotentialAbstractionFromReservoirsM3),0,PotentialAbstractionFromReservoirsM3)
            else:
                PotentialAbstractionFromReservoirsM3 = globals.inZero.copy()

            if option['simulateLakes']:
                # CM
                # PotentialAbstractionFromLakesM3 = 0.10 * self.var.LakeStorageM3  #original
                PotentialAbstractionFromLakesM3 = 0.10 * self.var.LakeStorageM3 * self.var.DtDay

                PotentialAbstractionFromLakesM3 = np.where(np.isnan(PotentialAbstractionFromLakesM3),0,PotentialAbstractionFromLakesM3)
            else:
                PotentialAbstractionFromLakesM3 = globals.inZero.copy()

            if option['simulateReservoirs'] or option['simulateLakes']:
                PotentialAbstractionFromLakesAndReservoirsM3 = PotentialAbstractionFromLakesM3 + PotentialAbstractionFromReservoirsM3
                    # potential total m3 that can be extracted from all lakes and reservoirs in a pixel
            else:
                PotentialAbstractionFromLakesAndReservoirsM3 = globals.inZero.copy()
            # CM mod end

            AreatotalPotentialAbstractionFromLakesAndReservoirsM3= np.take(np.bincount(self.var.WUseRegionC,weights=PotentialAbstractionFromLakesAndReservoirsM3),self.var.WUseRegionC)
            # potential total m3 that can be extracted from all lakes and reservoirs in the water region

            AreatotalWaterAbstractionFromAllSurfaceSourcesM3= np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            # the total amount that needs to be extracted from surface water, lakes and reservoirs in the water region
            # self.var.FractionAllSurfaceWaterUsed = np.maximum(1 - self.var.FractionGroundwaterUsed - self.var.FractionNonConventionalWaterUsed,globals.inZero)
            # self.var.FractionSurfaceWaterUsed = np.maximum(1 - self.var.FractionGroundwaterUsed - self.var.FractionNonConventionalWaterUsed-self.var.FractionLakeReservoirWaterUsed,globals.inZero)
            # AreatotalWaterToBeAbstractedfromLakesReservoirsM3 = np.where( (self.var.FractionSurfaceWaterUsed+self.var.FractionLakeReservoirWaterUsed)> 0, (self.var.FractionLakeReservoirWaterUsed / (self.var.FractionSurfaceWaterUsed+self.var.FractionLakeReservoirWaterUsed)) * AreatotalWaterAbstractionFromAllSurfaceSourcesM3,globals.inZero)

            AreatotalWaterToBeAbstractedfromLakesReservoirsM3 = self.var.FractionLakeReservoirWaterUsed * AreatotalWaterAbstractionFromAllSurfaceSourcesM3

            self.var.AreatotalWaterAbstractedfromLakesReservoirsM3 = np.minimum(AreatotalWaterToBeAbstractedfromLakesReservoirsM3,AreatotalPotentialAbstractionFromLakesAndReservoirsM3)
                # total amount of m3 abstracted from all lakes and reservoirs in the water regions

            FractionAbstractedByLakesReservoirs = np.where(AreatotalWaterAbstractionFromAllSurfaceSourcesM3 >0,self.var.AreatotalWaterAbstractedfromLakesReservoirsM3 / AreatotalWaterAbstractionFromAllSurfaceSourcesM3,globals.inZero)

            self.var.TotalAbstractionFromSurfaceWaterM3 = self.var.TotalAbstractionFromSurfaceWaterM3 * (1-FractionAbstractedByLakesReservoirs)
                # the original surface water abstraction amount is corrected for what is now already abstracted by lakes and reservoirs

            FractionLakesReservoirsEmptying = np.where(AreatotalPotentialAbstractionFromLakesAndReservoirsM3 > 0, self.var.AreatotalWaterAbstractedfromLakesReservoirsM3 / AreatotalPotentialAbstractionFromLakesAndReservoirsM3,globals.inZero)

            self.var.LakeAbstractionM3 = PotentialAbstractionFromLakesM3 * FractionLakesReservoirsEmptying
            if option['simulateLakes']:
                self.var.LakeStorageM3 = self.var.LakeStorageM3 - self.var.LakeAbstractionM3

            self.var.ReservoirAbstractionM3 = PotentialAbstractionFromReservoirsM3 * FractionLakesReservoirsEmptying
            if option['simulateReservoirs']:
                self.var.ReservoirStorageM3 = self.var.ReservoirStorageM3 - self.var.ReservoirAbstractionM3
                # subtract abstracted water from lakes and reservoir storage


            # ************************************************************
            # ***** Abstraction from channels ****************************
            # ***** average abstraction taken from entire waterregion ****
            # ***** limited by available channel water and e-flow minimum*
            # ************************************************************

            AreaTotalDemandedAbstractionFromSurfaceWaterM3 = np.maximum(np.take(np.bincount(self.var.WUseRegionC, weights=self.var.TotalAbstractionFromSurfaceWaterM3), self.var.WUseRegionC), 0)

            PixelAvailableWaterFromChannelsM3 = np.maximum(self.var.ChanM3Kin - self.var.EFlowThreshold * self.var.DtSec, 0) * (1 - self.var.WUsePercRemain)
            # respecting e-flow

            AreaTotalAvailableWaterFromChannelsM3 = np.maximum(np.take(np.bincount(self.var.WUseRegionC, weights=PixelAvailableWaterFromChannelsM3), self.var.WUseRegionC), 0)
            AreaTotalDemandedWaterFromChannelsM3 =  np.minimum(AreaTotalAvailableWaterFromChannelsM3, AreaTotalDemandedAbstractionFromSurfaceWaterM3)

            self.var.FractionAbstractedFromChannels = np.where(AreaTotalAvailableWaterFromChannelsM3 > 0, np.minimum(AreaTotalDemandedWaterFromChannelsM3 / AreaTotalAvailableWaterFromChannelsM3, 1), 0)
            # # IS THE DEFINITION OF AreaTotalDemandedWaterFromChannelsM3 REDUNDANT WITH np.minimum(...) ABOVE?
            # # fraction that is abstracted from channels (should be 0-1)


            #################################################################
            # CINZIA TO BE REMOVED
            # self.var.FractionAbstractedFromChannels = np.where(AreaTotalAvailableWaterFromChannelsM3 > 0, 0.5, 0)
            #################################################################



            self.var.WUseAddM3 = self.var.FractionAbstractedFromChannels * PixelAvailableWaterFromChannelsM3
            # pixel abstracted water in m3

            self.var.WUseAddM3Dt = self.var.WUseAddM3 * self.var.InvNoRoutSteps
            # splitting water use per timestep into water use per sub time step

            self.var.wateruseCum += self.var.WUseAddM3
            # summing up for water balance calculation
            #If report wateruse
            if (option['repwateruseGauges']) or (option['repwateruseSites']):
                self.var.WUseSumM3 = accuflux(self.var.Ldd, decompress(self.var.WUseAddM3)*self.var.InvDtSec)

            #totalAdd = areatotal(decompress(WUseAddM3),self.var.WUseRegion);
            self.var.totalAddM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.WUseAddM3),self.var.WUseRegionC)

            WaterUseShortageM3 = self.var.TotalAbstractionFromSurfaceWaterM3 - self.var.WUseAddM3
            # amount of M3 that cannot be extracted from any source, including the channels

            self.var.PotentialSurfaceWaterAvailabilityForIrrigationM3 = np.maximum(PixelAvailableWaterFromChannelsM3 - self.var.TotalAbstractionFromSurfaceWaterM3 + IrrigationAbstractionFromSurfaceWaterM3 + self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3,0.0)
            # available water excluding the surface water irrigation needs


            # ************************************************************
            # ***** Water Allocation *************************************
            # ***** average abstraction taken from entire waterregion ****
            # ***** limited by available channel water and e-flow minimum*
            # ************************************************************

            #totalAbstr = areatotal(decompress(TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegion)
            self.var.AreaTotalAbstractionFromSurfaceWaterM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromSurfaceWaterM3 - self.var.WUseAddM3),self.var.WUseRegionC)
            self.var.AreaTotalAbstractionFromGroundwaterM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromGroundwaterM3),self.var.WUseRegionC)

            # demand
            AreaTotalDemandM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalDemandM3),self.var.WUseRegionC)

            #totalEne = areatotal(decompress(self.var.EnergyConsumptiveUseMM*self.var.MMtoM3),self.var.WUseRegion)
            AreatotalIrriM3 = np.take(np.bincount(self.var.WUseRegionC,weights=IrrigationAbstractionFromSurfaceWaterM3 + self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalDomM3 = np.take(np.bincount(self.var.WUseRegionC,weights=DomAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalLiveM3 = np.take(np.bincount(self.var.WUseRegionC,weights=LivestockAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalIndM3 = np.take(np.bincount(self.var.WUseRegionC,weights=IndustrialAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalEneM3 = np.take(np.bincount(self.var.WUseRegionC,weights=EnergyAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)

            # Allocation rule: Domestic ->  Energy -> Livestock -> Industry -> Irrigation
            self.var.AreatotalIrrigationShortageM3 = np.take(np.bincount(self.var.WUseRegionC,weights=WaterUseShortageM3),self.var.WUseRegionC)
            self.var.AreatotalIrrigationUseM3 = np.maximum(AreatotalIrriM3-self.var.AreatotalIrrigationShortageM3,0.0)

            with np.errstate(all='ignore'):
                fractionIrrigationAvailability = np.where(AreatotalIrriM3 > 0, self.var.AreatotalIrrigationUseM3/AreatotalIrriM3,1.0)

                self.var.IrrigationWaterAbstractionM3 = fractionIrrigationAvailability*IrrigationAbstractionFromSurfaceWaterM3 + IrrigationAbstractionFromGroundwaterM3
                # real irrigation is percentage of avail/demand for waterregion * old surface + old groundwater abstraction
                IrrigationWaterDemand = self.var.IrrigationWaterAbstractionM3*self.var.M3toMM
                IrrigationWaterDemand = np.where(self.var.IrrigationFraction > 0,IrrigationWaterDemand/self.var.IrrigationFraction,0.0)

            # for mass balance calculate the loss of irrigation water

            #---------------------------------------------------------
            # updating soil in loop3=irrigation
            #---------------------------------------------------------

            Wold=self.var.W1[2]
                #WWP3No3=WRes1+(WS1-WRes1)/((1+(GenuAlpha1*(10**3.0))**GenuN1)**GenuM1);

            IrrigationDemandW1b = np.maximum(IrrigationWaterDemand - (self.var.WFilla - self.var.W1a[2]),0)
            self.var.W1a[2] = np.where(self.var.W1a[2] >= self.var.WFilla, self.var.W1a[2], np.minimum(self.var.WFilla,self.var.W1a[2]+IrrigationWaterDemand))
            self.var.W1b[2] = np.where(self.var.W1b[2] >= self.var.WFillb, self.var.W1b[2], np.minimum(self.var.WFillb,self.var.W1b[2]+IrrigationDemandW1b))
            self.var.W1[2] = np.add(self.var.W1a[2], self.var.W1b[2])
	        # if irrigated soil is less than Pf3 then fill up to Pf3 (if there is water demand)
		    # if more than Pf3 the additional water is transpirated
		    # there is already no water demand if the soil is frozen
            Wdiff=self.var.W1[2]-Wold
            self.var.Ta[2] =  self.var.Ta[2] + IrrigationWaterDemand - Wdiff

            self.var.IrriLossCUM = self.var.IrriLossCUM - self.var.IrrigationWaterAbstractionM3*self.var.IrrigationEfficiency*self.var.ConveyanceEfficiency - Wdiff * self.var.MMtoM3 * self.var.IrrigationFraction

            # Added to TA but also
            # for mass balance calculate the loss of irrigation water
            # AdR: irrigation demand added to W1 and Ta; so assumption here that soil moisture stays the same
		    # we could also abstract more water equivalent to satisfy Ta and bring soil moisture to pF2 or so, for later consideration#
            # self.var.Ta[2] = np.where(self.var.FrostIndex > self.var.FrostIndexThreshold, globals.inZero, self.var.Ta[2])
            # transpiration is 0 when soil is frozen

            #---------------------------------------------------------
            # E-flow
            #---------------------------------------------------------

            self.var.EFlowIndicator=np.where(self.var.ChanQ <= self.var.EFlowThreshold,globals.inZero + 1.0,globals.inZero)
            # if ChanQ is less than EflowThreshold, EFlowIndicator becomes 1


            # ************************************************************
            # ***** update state variables                             ***
            # ************************************************************
            # CM Update state variables for changes to W1a[2] and W1b[2]
            self.var.Theta1a[2] = self.var.W1a[2] / self.var.SoilDepth1a[2]
            self.var.Theta1b[2] = self.var.W1b[2] / self.var.SoilDepth1b[2]


            # ************************************************************
            # ***** smooth lower zone with correction                  ***
            # ************************************************************

            if option['groundwaterSmooth']:

                LZPcr = decompress(self.var.LZ)

                Range=self.var.LZSmoothRange*celllength()

                LZTemp1 = ifthen(self.var.GroundwaterBodiesPcr == 1,LZPcr)
                LZTemp2 = ifthen(self.var.GroundwaterBodiesPcr == 1,windowtotal(LZTemp1,Range))
                LZTemp3 = windowtotal(LZTemp1*0+1, Range)
                LZSmooth = ifthenelse(LZTemp3 == 0,0.0,LZTemp2/LZTemp3)

                LZPcr = ifthenelse(self.var.GroundwaterBodiesPcr == 0,LZPcr,0.9*LZPcr+0.1*LZSmooth)

                diffCorr=0.1*areaaverage(LZSmooth-LZTemp1, self.var.groundwaterCatch)
                # error of 0.1  LZSmooth operation (same factor of 0.1 as above)
                LZPcr -= cover(diffCorr,0)
                # correction of LZ by the average error from smoothing operation

                self.var.LZ = compressArray(LZPcr)

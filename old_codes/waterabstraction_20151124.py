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
            # ***** Domestic Use constants **************
            # ************************************************************
            LeakageFraction = np.minimum(np.maximum(loadmap('LeakageFraction')*(1-loadmap('LeakageReductionFraction')),globals.inZero),1.0)
            self.var.DomesticLeakageConstant =  np.minimum(np.maximum(1/(1-LeakageFraction),globals.inZero),1.0)
             # Domestic Water Abstraction becomes larger in case of leakage
             # LeakageFraction is LeakageFraction (0-1) multiplied by reduction scenario (10% reduction is 0.1 in map)
             # 0.65 leakage and 0.1 reduction leads to 0.585 effective leakage, resulting in 2.41 times more water abstraction
            self.var.DomesticWaterSavingConstant = np.minimum(np.maximum(1-loadmap('WaterSavingFraction'),globals.inZero),1.0)
             # Domestic water saving if in place, changes this value from 1 to a value between 0 and 1, and will reduce demand and abstraction

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

            WUseNo = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 370]
            self.var.Dom = []   # domestic water use
            self.var.Liv = []   # livestock
            self.var.WUse1 = []

            self.var.WUse1.append(12)
            j = 0
            for i in xrange(1, 367):
                if i >= WUseNo[j + 1]:
                    j += 1
                self.var.WUse1.append(j)

            j = 0
            for i in xrange(12):
                WUseName = generateName(binding['DomesticAbstractionMaps'], WUseNo[i])
                self.var.Dom.append(loadLAI(binding['DomesticAbstractionMaps'], WUseName, i))
                WUseName = generateName(binding['LivestockDemandMaps'], WUseNo[i])
                self.var.Liv.append(loadLAI(binding['LivestockDemandMaps'], WUseName, i))

            self.var.IndustrialAbstractionMM = loadmap('IndustrialAbstractionMaps') *  (1-loadmap('WaterReUseFraction'))
            self.var.IndustrialConsumptiveUseMM = self.var.IndustrialAbstractionMM * loadmap('IndustryConsumptiveUseFraction')
              #IndustrialAbstractionMM = scalar(timeinputsparse(IndustrialAbstractionMaps)) * (1-WaterReUseFraction);
	          # Industrial Water Demand (mm per day)
	          # WaterReUseFraction: Fraction of water re-used in industry (e.g. 50% = 0.5 = half of the water is re-used, used twice (baseline=0, maximum=1)
          	  # IndustrialConsumtiveUseMM is the amount that evaporates etc
              # only 1 map so this one is loaded in initial!

            self.var.EnergyAbstractionMM = loadmap('EnergyAbstractionMaps')
            self.var.EnergyConsumptiveUseMM = self.var.EnergyAbstractionMM * loadmap('EnergyConsumptiveUseFraction')
               # EnergyAbstractionMM = scalar(timeinputsparse(EnergyAbstractionMaps));
	           # Energy Water Demand (mm per day)
               # EnergyConsumtiveUseMM is the amount that evaporates etc
            self.var.LivestockConsumptiveUseFraction = loadmap('LivestockConsumptiveUseFraction')
            self.var.DomesticConsumptiveUseFraction = loadmap('DomesticConsumptiveUseFraction')
            self.var.LeakageWaterLossFraction = loadmap('LeakageWaterLoss')

            # Initialising cumulative output variables
            # These are all needed to compute the cumulative mass balance error

            self.var.wateruseCum = globals.inZero.copy()
            # water use cumulated amount
            self.var.WUseAddM3Dt = globals.inZero.copy()

            self.var.IrriLossCUM = globals.inZero.copy()
            # Cumulative irrigation loss [mm]
            abstractionCUM = globals.inZero.copy()
            # Cumulative abstraction from surface water [mm]

            IrrigationWaterDemand = globals.inZero.copy()
            if not(option['riceIrrigation']):
               self.var.TotalAbstractionFromSurfaceWaterM3 = globals.inZero.copy()
               # rice irrigation introduced and fille this already

            self.var.TotalAbstractionFromGroundwaterM3 = globals.inZero.copy()
            IrrigationAbstractionFromGroundwaterM3 = globals.inZero.copy()
            LiveDomAbstractionFromGroundwaterM3 = globals.inZero.copy()
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

    def dynamic(self):
        """ dynamic part of the water use module
            init water use before sub step routing
        """

        if option['wateruse']:

            # ************************************************************
            # ***** LIVESTOCK ********************************************
            # ************************************************************

            self.var.LivestockDemandMM = self.var.Liv[self.var.WUse1[self.var.CalendarDay]]
             # Livestock Water Demand (mm per day)
            self.var.LivestockConsumptiveUseMM = self.var.LivestockDemandMM * self.var.LivestockConsumptiveUseFraction
             # the amount that is not returned

            LivestockAbstractionFromGroundwaterM3= np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed*self.var.LivestockConsumptiveUseMM* self.var.MMtoM3,globals.inZero)
            LivestockAbstractionFromNonConventionalWaterM3= self.var.FractionNonConventionalWaterUsed * self.var.LivestockConsumptiveUseMM * self.var.MMtoM3
            LivestockAbstractionFromSurfaceWaterM3=self.var.LivestockConsumptiveUseMM*self.var.MMtoM3 - LivestockAbstractionFromGroundwaterM3 - LivestockAbstractionFromNonConventionalWaterM3

            self.var.TotalLivestockAbstractionM3 += LivestockAbstractionFromGroundwaterM3 + LivestockAbstractionFromSurfaceWaterM3 + LivestockAbstractionFromNonConventionalWaterM3


            # ************************************************************
            # ***** DOMESTIC *********************************************
            # ************************************************************

            DomesticBasicAbstractionMM = self.var.Dom[self.var.WUse1[self.var.CalendarDay]] * self.var.DomesticWaterSavingConstant
            # Domestic Water Abstraction (mm per day), already taking into account water saving in households
            self.var.DomesticAbstractionMM = DomesticBasicAbstractionMM  * self.var.DomesticLeakageConstant
            # Domestic water abstraction is larger if there is leakage, but is smaller if there is water savings
            LeakageMM = self.var.DomesticAbstractionMM - DomesticBasicAbstractionMM
            self.var.DomesticConsumtiveUseMM =  self.var.DomesticAbstractionMM * self.var.DomesticConsumptiveUseFraction + LeakageMM * self.var.LeakageWaterLossFraction
            # DomesticConsumtiveUseMM is the amount that disappears from the waterbalance
            # Assumption here is that leakage is partially lost/evaporated (LeakageWaterLoss fraction)

            DomAbstractionFromGroundwaterM3= np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * self.var.DomesticConsumtiveUseMM* self.var.MMtoM3,globals.inZero)
            DomAbstractionFromNonConventionalWaterM3= self.var.FractionNonConventionalWaterUsed * self.var.DomesticConsumtiveUseMM*self.var.MMtoM3
            DomAbstractionFromSurfaceWaterM3=self.var.DomesticConsumtiveUseMM* self.var.MMtoM3 - DomAbstractionFromGroundwaterM3 - DomAbstractionFromNonConventionalWaterM3

            # DomAbstractionFromGroundwaterM3 = globals.inZero
            # DomAbstractionFromSurfaceWaterM3 = globals.inZero
            # DomAbstractionFromNonConventionalWaterM3 = globals.inZero


            # ************************************************************
            # ***** IRRIGATION *******************************************
            # ************************************************************

            # water demand from loop3 = irrigated zone
            self.var.Ta[2] = np.maximum(np.minimum(self.var.RWS[2] * self.var.TranspirMaxCorrected, self.var.W1[2] - self.var.WWP1[2]), globals.inZero)

            #IrrigationWaterDemandMM = (self.var.TranspirMaxCorrected-self.var.Ta[2])+ \
            #      np.maximum(self.var.WFC1[2]-self.var.W1[2],0) * self.var.IrrigationType
            IrrigationWaterDemandMM = (self.var.TranspirMaxCorrected-self.var.Ta[2]) * self.var.IrrigationMult
                #  a factor (IrrigationMult) add some water (to prevent salinisation)

            # irrigationWaterNeed assumed to be equal to potential transpiration minus actual transpiration
            # in mm here, assumed for the entire pixel, thus later to be corrected with IrrigationFraction
            # IrrigationType (value between 0 and 1) is used here to distinguish between additional adding water until fieldcapacity (value set to 1) or not (value set to 0)
            IrrigationWaterDemandMM = np.where(self.var.FrostIndex > self.var.FrostIndexThreshold,globals.inZero,IrrigationWaterDemandMM)
            # IrrigationWaterDemand is 0 when soil is frozen

            IrrigationWaterAbstractionMM = np.where((self.var.IrrigationEfficiency * self.var.ConveyanceEfficiency) > 0, IrrigationWaterDemandMM * self.var.IrrigationFraction / (self.var.IrrigationEfficiency * self.var.ConveyanceEfficiency),globals.inZero)
            self.var.IrrigationWaterAbstractionM3 = np.maximum(IrrigationWaterAbstractionMM * self.var.MMtoM3, globals.inZero)
            # irrigation efficiency max 1, ~0.90 drip irrigation, ~0.75 sprinkling
		    # conveyance efficiency, around 0.80 for average channel
		    # multiplied by actual irrigated area (fraction) and cellsize(MMtoM3) in M3 per pixel

            # self.var.IrrigationWaterAbstractionM3 = self.var.FractionGroundwaterUsed * 0.0 + 0.000000001
            # NOT OK: self.var.IrrigationWaterAbstractionM3 = globals.inZero + 5.0
            # OK self.var.IrrigationWaterAbstractionM3 = globals.inZero
            IrrigationAbstractionFromGroundwaterM3 = np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * self.var.IrrigationWaterAbstractionM3,globals.inZero)
            # NOT OK: IrrigationAbstractionFromGroundwaterM3 = 0.5 * self.var.IrrigationWaterAbstractionM3
            # IrrigationAbstractionFromGroundwaterM3 = globals.inZero
            # NOT OK: IrrigationAbstractionFromGroundwaterM3 = np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * self.var.IrrigationWaterAbstractionM3*0.0 + 5.0,globals.inZero)
            # NOT OK IrrigationAbstractionFromGroundwaterM3 = np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * self.var.IrrigationWaterAbstractionM3*0.0,globals.inZero)
            IrrigationAbstractionFromSurfaceWaterM3 = np.maximum(self.var.IrrigationWaterAbstractionM3 - IrrigationAbstractionFromGroundwaterM3,globals.inZero)
            # OK: IrrigationAbstractionFromSurfaceWaterM3 = globals.inZero

            # pdb.set_trace()

             # ************************************************************
             # ***** INDUSTRY AND ENERGY **********************************
             # ************************************************************

            EnergyAbstractionFromSurfaceWaterM3 = self.var.EnergyConsumptiveUseMM * self.var.MMtoM3
                # all taken from surface water
            IndustrialWaterAbstractionM3 = self.var.IndustrialConsumptiveUseMM * self.var.MMtoM3
            IndustrialAbstractionFromGroundwaterM3 = np.where(self.var.GroundwaterBodies > 0, self.var.FractionGroundwaterUsed * IndustrialWaterAbstractionM3,globals.inZero)
            IndustrialAbstractionFromNonConventionalWaterM3 = self.var.FractionNonConventionalWaterUsed * IndustrialWaterAbstractionM3
            IndustrialAbstractionFromSurfaceWaterM3 = IndustrialWaterAbstractionM3 - IndustrialAbstractionFromGroundwaterM3 - IndustrialAbstractionFromNonConventionalWaterM3

            # EnergyAbstractionFromSurfaceWaterM3 = globals.inZero
            # IndustrialAbstractionFromGroundwaterM3 = globals.inZero
            # IndustrialAbstractionFromSurfaceWaterM3 = globals.inZero
            # self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3 = globals.inZero


             # ************************************************************
             # ***** TOTAL ABSTRACTIONS (DEMANDED) ************************
             # ************************************************************

            self.var.TotalAbstractionFromGroundwaterM3 = IrrigationAbstractionFromGroundwaterM3 + DomAbstractionFromGroundwaterM3 + LivestockAbstractionFromGroundwaterM3 + IndustrialAbstractionFromGroundwaterM3
            self.var.TotalAbstractionFromSurfaceWaterM3 =  IrrigationAbstractionFromSurfaceWaterM3 + self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3 + DomAbstractionFromSurfaceWaterM3 + LivestockAbstractionFromSurfaceWaterM3 + IndustrialAbstractionFromSurfaceWaterM3 + EnergyAbstractionFromSurfaceWaterM3

            PaddyRiceWaterAbstractionFromSurfaceWaterMM = self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3 * self.var.M3toMM
                #taken from paddy rice routine
            self.var.TotalDemandM3 = (self.var.LivestockDemandMM + self.var.DomesticAbstractionMM + IrrigationWaterAbstractionMM + PaddyRiceWaterAbstractionFromSurfaceWaterMM + self.var.IndustrialAbstractionMM + self.var.EnergyAbstractionMM) * self.var.MMtoM3

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

            self.var.NonConventionalWaterM3 = DomAbstractionFromNonConventionalWaterM3 + LivestockAbstractionFromNonConventionalWaterM3 + IndustrialAbstractionFromNonConventionalWaterM3
               # Non conventional water producted is not abstracted from surface water


             # ************************************************************
             # ***** ABSTRACTION FROM LAKES AND RESERVOIRS ****************
             # ************************************************************

            PotentialAbstractionFromReservoirsM3 = np.minimum(0.02 * self.var.ReservoirStorageM3, 0.01*self.var.TotalReservoirStorageM3C)
            PotentialAbstractionFromReservoirsM3 = np.where(np.isnan(PotentialAbstractionFromReservoirsM3),0,PotentialAbstractionFromReservoirsM3)
            PotentialAbstractionFromLakesM3 = 0.10 * self.var.LakeStorageM3
            PotentialAbstractionFromLakesM3 = np.where(np.isnan(PotentialAbstractionFromLakesM3),0,PotentialAbstractionFromLakesM3)

            PotentialAbstractionFromLakesAndReservoirsM3 = PotentialAbstractionFromLakesM3 + PotentialAbstractionFromReservoirsM3
                # potential total m3 that can be extracted from all lakes and reservoirs in a pixel
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
            self.var.LakeStorageM3 = self.var.LakeStorageM3 - self.var.LakeAbstractionM3

            self.var.ReservoirAbstractionM3 = PotentialAbstractionFromReservoirsM3 * FractionLakesReservoirsEmptying

            self.var.ReservoirStorageM3 = self.var.ReservoirStorageM3 - self.var.ReservoirAbstractionM3
                # subtract abstracted water from lakes and reservoir storage


            # ************************************************************
            # ***** Abstraction from channels ****************************
            # ***** average abstraction taken from entire waterregion ****
            # ***** limited by available channel water and e-flow minimum*
            # ************************************************************

            AreaTotalDemandedAbstractionFromSurfaceWaterM3 = np.maximum(np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegionC),globals.inZero)

            PixelAvailableWaterFromChannelsM3 = np.maximum(self.var.ChanQ-self.var.EFlowThreshold,0.0)*self.var.DtSec*(1-self.var.WUsePercRemain)
                # respecting e-flow

            AreaTotalAvailableWaterFromChannelsM3 = np.maximum(np.take(np.bincount(self.var.WUseRegionC,weights=PixelAvailableWaterFromChannelsM3),self.var.WUseRegionC),globals.inZero)
            AreaTotalDemandedWaterFromChannelsM3 =  np.minimum (AreaTotalAvailableWaterFromChannelsM3, AreaTotalDemandedAbstractionFromSurfaceWaterM3)

            self.var.FractionAbstractedFromChannels = np.where(AreaTotalDemandedWaterFromChannelsM3 > 0, np.minimum(AreaTotalAvailableWaterFromChannelsM3/AreaTotalDemandedWaterFromChannelsM3,1.0),globals.inZero)
                # fraction that is abstracted from channels (should be 0-1)
                # cannot exceed demand (therefore cut off at 1)
            self.var.WUseAddM3 = self.var.FractionAbstractedFromChannels*self.var.TotalAbstractionFromSurfaceWaterM3
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

            self.var.WaterUseShortageM3 = self.var.TotalAbstractionFromSurfaceWaterM3 - self.var.WUseAddM3
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
            self.var.AreaTotalDemandM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalDemandM3),self.var.WUseRegionC)

            #totalEne = areatotal(decompress(self.var.EnergyConsumptiveUseMM*self.var.MMtoM3),self.var.WUseRegion)
            AreatotalIrriM3 = np.take(np.bincount(self.var.WUseRegionC,weights=IrrigationAbstractionFromSurfaceWaterM3 + self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalDomM3 = np.take(np.bincount(self.var.WUseRegionC,weights=DomAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalLiveM3 = np.take(np.bincount(self.var.WUseRegionC,weights=LivestockAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalIndM3 = np.take(np.bincount(self.var.WUseRegionC,weights=IndustrialAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalEneM3 = np.take(np.bincount(self.var.WUseRegionC,weights=EnergyAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)

            # Allocation rule: Domestic ->  Energy -> Livestock -> Industry -> Irrigation
            self.var.AreatotalIrrigationShortageM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.WaterUseShortageM3),self.var.WUseRegionC)
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

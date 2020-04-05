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
            IndustrialAbstractionFromSurfaceWaterM3 = IndustrialWaterAbstractionM3 - IndustrialAbstractionFromGroundwaterM3

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


             # ************************************************************
             # ***** ABSTRACTION FROM LAKES AND RESERVOIRS ****************
             # ************************************************************

            PotentialAbstractionFromReservoirsM3 = np.maximum(self.var.ReservoirStorageM3 - 0.1*self.var.TotalReservoirStorageM3C,globals.inZero)
            PotentialAbstractionFromLakesM3 = np.maximum(self.var.LakeStorageM3,globals.inZero)
            self.var.PotentialAbstractionFromLakesReservoirsM3 = PotentialAbstractionFromLakesM3 + PotentialAbstractionFromReservoirsM3
                # potential total m3 that can be extracted from all lakes and reservoirs in a pixel
            AreatotalPotentialAbstractionFromLakesReservoirsM3= np.take(np.bincount(self.var.WUseRegionC,weights=self.var.PotentialAbstractionFromLakesReservoirsM3),self.var.WUseRegionC)
                # potential total m3 that can be extracted from all lakes and reservoirs in the water region
            self.var.AreatotalWaterAbstractionFromAllSurfaceSourcesM3= np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
                # the total amount that needs to be extracted from surface water, lakes and reservoirs in the water region

            # self.var.FractionAllSurfaceWaterUsed = np.maximum(1 - self.var.FractionGroundwaterUsed - self.var.FractionNonConventionalWaterUsed,globals.inZero)
            self.var.FractionSurfaceWaterUsed = np.maximum(1 - self.var.FractionGroundwaterUsed - self.var.FractionNonConventionalWaterUsed-self.var.FractionLakeReservoirWaterUsed,globals.inZero)

            AreatotalWaterToBeAbstractedfromLakesReservoirsM3 = np.where( (self.var.FractionSurfaceWaterUsed+self.var.FractionLakeReservoirWaterUsed)> 0, (self.var.FractionLakeReservoirWaterUsed / (self.var.FractionSurfaceWaterUsed+self.var.FractionLakeReservoirWaterUsed)) * self.var.AreatotalWaterAbstractionFromAllSurfaceSourcesM3,globals.inZero)
            self.var.AreatotalWaterAbstractedfromLakesReservoirsM3 = np.minimum(AreatotalWaterToBeAbstractedfromLakesReservoirsM3,AreatotalPotentialAbstractionFromLakesReservoirsM3)
                # total amount of m3 abstracted from all lakes and reservoirs in the water regions
            FractionAbstractedByLakesReservoirs = np.where(self.var.AreatotalWaterAbstractionFromAllSurfaceSourcesM3 >0,self.var.AreatotalWaterAbstractedfromLakesReservoirsM3 / self.var.AreatotalWaterAbstractionFromAllSurfaceSourcesM3,globals.inZero)
            self.var.TotalAbstractionFromSurfaceWaterM3 *= (1-FractionAbstractedByLakesReservoirs)
                # the original surface water abstraction amount is corrected for what is now already abstracted by lakes and reservoirs

            FractionLakesReservoirsEmptying = np.where(AreatotalPotentialAbstractionFromLakesReservoirsM3 > 0,self.var.AreatotalWaterAbstractedfromLakesReservoirsM3 / AreatotalPotentialAbstractionFromLakesReservoirsM3,globals.inZero)
            self.var.LakeAbstractionM3 = PotentialAbstractionFromLakesM3 * FractionLakesReservoirsEmptying
            self.var.LakeStorageM3 -= self.var.LakeAbstractionM3
            self.var.ReservoirAbstractionM3 = PotentialAbstractionFromReservoirsM3 * FractionLakesReservoirsEmptying
            self.var.ReservoirStorageM3 -= self.var.ReservoirAbstractionM3
             # subtract abstracted water from lakes and reservoir storage

            PotentialAbstractionFromReservoirsM3 = np.maximum(self.var.ReservoirStorageM3 - 0.1*self.var.TotalReservoirStorageM3C,globals.inZero)
            PotentialAbstractionFromLakesM3 = np.maximum(self.var.LakeStorageM3,globals.inZero)
            self.var.PotentialAbstractionFromLakesReservoirsM3 = PotentialAbstractionFromLakesM3 + PotentialAbstractionFromReservoirsM3
             # calculate new lake and reservoir potential abstraction (available water) after current timestep abstractions
             # NOTE: this layer contains potentially missing values and might need to be covered with 0 values


            # ************************************************************
            # ***** AdDeRoo's code for abstraction from channels *********
            # ***** average abstraction taken from entire waterregion ****
            # ***** limited by available channel water and e-flow minimum*
            # ************************************************************

            # self.var.TotalAbstractionFromSurfaceWaterM3=globals.inZero+2.0 GOES OK
            # self.var.TotalAbstractionFromSurfaceWaterM3=np.maximum(self.var.TotalAbstractionFromSurfaceWaterM3*0.0+2.0,globals.inZero) GOES WRONG
            # self.var.TotalAbstractionFromSurfaceWaterM3=self.var.TotalAbstractionFromSurfaceWaterM3*0.0+2.0 GOES WRONG
#            AreaTotalDemandedAbstractionFromSurfaceWaterM3 = np.maximum(np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegionC),globals.inZero)
            # AreaTotalDemandedAbstractionFromSurfaceWaterM3 = 5.0 GOES OK

#            PixelAvailableWaterFromChannelsM3 = np.maximum(self.var.ChanM3Kin*(1-self.var.WUsePercRemain),globals.inZero)
                # respecting e-flow
#            AreaTotalAvailableWaterFromChannelsM3 = np.maximum(np.take(np.bincount(self.var.WUseRegionC,weights=PixelAvailableWaterFromChannelsM3),self.var.WUseRegionC),globals.inZero)
#            AreaTotalAbstractedWaterFromChannelsM3 =  np.minimum (AreaTotalAvailableWaterFromChannelsM3, AreaTotalDemandedAbstractionFromSurfaceWaterM3)
#            FractionAbstractedFromChannels = np.where(AreaTotalAvailableWaterFromChannelsM3 > 0, AreaTotalAbstractedWaterFromChannelsM3 / AreaTotalAvailableWaterFromChannelsM3,globals.inZero)
            # FractionAbstractedFromChannels = AreaTotalAbstractedWaterFromChannelsM3*0.00001 GOES WRONG
            # FractionAbstractedFromChannels = AreaTotalAvailableWaterFromChannelsM3*0.00001 GOES OK
            # FractionAbstractedFromChannels = 0.01 GOES OK
                # fraction that is abstracted from channels (0-1)
#            self.var.WUseAddM3 = FractionAbstractedFromChannels * self.var.ChanM3Kin
                # pixel abstracted water in m3


            # ************************************************************
            # ***** PeterBurek's code for abstraction
            # ***** average abstraction taken from neigbouring rivers ****
            # ***** limited by available channel water and e-flow minimum*
            # ************************************************************

            # Calculate water abstraction from channels, which is limited by water available in channels

            UpstreamWUse = self.var.TotalAbstractionFromSurfaceWaterM3
            # UpstreamWUse = globals.inZero.copy()
            # wateruse for loop is amount of water per timestep [cu m]

            ChanMIter = self.var.ChanM3Kin.copy()
            # for Iteration loop: First value is amount of water available in the channel
            ChanLeft = self.var.WUsePercRemain * ChanMIter
            # WUsePercRemain of the discharge must stay in the river (environmental flow, ecological flow)
            self.var.WUseAddM3 = globals.inZero.copy()
            # real water consumption is set to 0

            for NoWaterUseExe in xrange(self.var.NoWaterUseSteps):

                ChanHelp = np.maximum(ChanMIter - UpstreamWUse, ChanLeft)
                WUseIter = np.maximum(UpstreamWUse - (ChanMIter - ChanHelp),0)
                # new amount is amount - water use till a limit
                # new water use is wateruse - water is used from channel
                # network
                ChanMIter = ChanHelp.copy()
                self.var.WUseAddM3 += UpstreamWUse - WUseIter
                # water use is added up; the sum is the same as sum of original
                # TEST TEST
                UpstreamWUse = np.bincount(self.var.downWRegion, weights=WUseIter)[:-1]
                # Peter's code: UpstreamWUse=np.bincount(self.var.downWRegion, weights=WUseIter)[:-1]
                # remaining water use is moved down the the river system,
                # old code: UpstreamWUse = upstream(self.var.LddWaterRegion, WUseIter)


            # *******************************************************************************
            # ***** End of PeterBurek's code for abstraction, start of remaining calculations
            # *******************************************************************************

            self.var.WUseAddM3Dt = self.var.WUseAddM3 * self.var.InvNoRoutSteps
            # splitting water use per timestep into water use per sub time step

            self.var.wateruseCum += self.var.WUseAddM3
            # summing up for water balance calculation
            #If report wateruse
            if (option['repwateruseGauges']) or (option['repwateruseSites']):
                self.var.WUseSumM3 = accuflux(self.var.Ldd, decompress(self.var.WUseAddM3)*self.var.InvDtSec)

            #totalAdd = areatotal(decompress(WUseAddM3),self.var.WUseRegion);
            self.var.totalAddM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.WUseAddM3),self.var.WUseRegionC)

            #totalAbstr = areatotal(decompress(TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegion)
            self.var.AreaTotalAbstractionFromSurfaceWaterM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            self.var.AreaTotalAbstractionFromGroundwaterM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalAbstractionFromGroundwaterM3),self.var.WUseRegionC)

            # demand
            self.var.AreaTotalDemandM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.TotalDemandM3),self.var.WUseRegionC)

            #totalEne = areatotal(decompress(self.var.EnergyConsumptiveUseMM*self.var.MMtoM3),self.var.WUseRegion)
            AreatotalIrriM3 = np.take(np.bincount(self.var.WUseRegionC,weights=IrrigationAbstractionFromSurfaceWaterM3 + self.var.PaddyRiceWaterAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalDomM3 = np.take(np.bincount(self.var.WUseRegionC,weights=DomAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalLiveM3 = np.take(np.bincount(self.var.WUseRegionC,weights=LivestockAbstractionFromSurfaceWaterM3),self.var.WUseRegionC)
            AreatotalIndM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.IndustrialConsumptiveUseMM*self.var.MMtoM3),self.var.WUseRegionC)
            AreatotalEneM3 = np.take(np.bincount(self.var.WUseRegionC,weights=self.var.EnergyConsumptiveUseMM*self.var.MMtoM3),self.var.WUseRegionC)

            # Allocation rule: Domestic ->  Energy -> Livestock -> Industry -> Irrigation
            # for the moment all uses except irrigation are added up and treated together
            AreatotalWaterAvailableforIrrigationM3 = self.var.totalAddM3 - (AreatotalDomM3 + AreatotalEneM3 + AreatotalLiveM3 + AreatotalIndM3)
            self.var.AreatotalIrrigationShortageM3 = np.maximum(-(AreatotalWaterAvailableforIrrigationM3-AreatotalIrriM3),0.0)
            AreatotalIrrigationUseM3 = np.maximum(AreatotalIrriM3-self.var.AreatotalIrrigationShortageM3,0.0)

            with np.errstate(all='ignore'):
                fractionIrrigationAvailability = np.where(AreatotalIrriM3 > 0, AreatotalIrrigationUseM3/AreatotalIrriM3,1.0)

                self.var.IrrigationWaterAbstractionM3 = fractionIrrigationAvailability*IrrigationAbstractionFromSurfaceWaterM3 + IrrigationAbstractionFromGroundwaterM3
                  # real irrigation is percentage of avail/demand for waterregion * old surface + old groundwater abstraction
                IrrigationWaterDemand = self.var.IrrigationWaterAbstractionM3*self.var.IrrigationEfficiency*self.var.ConveyanceEfficiency*self.var.M3toMM
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

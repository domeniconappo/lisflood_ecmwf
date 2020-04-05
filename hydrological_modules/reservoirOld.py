# -------------------------------------------------------------------------
# Name:        Reservoir module
# Purpose:
#
# Author:      burekpe
#
# Created:     29.03.2014
# Copyright:   (c) burekpe 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------

from global_modules.add1 import *

class reservoir(object):

    """
    # ************************************************************
    # ***** RESERVOIR    *****************************************
    # ************************************************************
    """

    def __init__(self, reservoir_variable):
        self.var = reservoir_variable

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

    def initial(self):
        """ initial part of the reservoir module
        """
        # ************************************************************
        # ***** RESERVOIRS
        # ************************************************************

        if option['simulateReservoirs']:

            # NoSubStepsRes=max(1,roundup(self.var.DtSec/loadmap('DtSecReservoirs')))
            # Number of sub-steps based on value of DtSecReservoirs,
            # or 1 if DtSec is smaller than DtSecReservoirs
            # DtSubRes=self.var.DtSec/loadmap('NoSubStepsRes')
            # Corresponding sub-timestep (seconds)

            self.var.ReservoirSitesC = loadmap('ReservoirSites')
            if self.var.ReservoirSitesC.size==0:
                option['simulateReservoirs']=False
                return
            # break if no reservoirs

            self.var.ReservoirSitesC[self.var.ReservoirSitesC < 1] = 0
            self.var.ReservoirSitesC[self.var.IsChannel == 0] = 0
            # Get rid of any reservoirs that are not part of the channel network
            self.var.ReservoirSitesCC = np.compress(self.var.ReservoirSitesC>0,self.var.ReservoirSitesC)
            self.var.ReservoirIndex = np.nonzero(self.var.ReservoirSitesC)[0]

            self.var.IsStructureKinematic = np.where(self.var.ReservoirSitesC > 0 , np.bool8(1),self.var.IsStructureKinematic)
            #self.var.IsStructureKinematic = ifthenelse(defined(self.var.ReservoirSites), pcraster.boolean(1), self.var.IsStructureKinematic)
            # Add reservoir locations to structures map (used to modify LddKinematic
            # and to calculate LddStructuresKinematic)


            ReservoirSitePcr = loadmap('ReservoirSites',pcr=True)
            self.var.ReservoirSites = ReservoirSitePcr
            ReservoirSitePcr = ifthen((defined(ReservoirSitePcr) & boolean(decompress(self.var.IsChannel))), ReservoirSitePcr)
            # Get rid of any reservoirs that are not part of the channel network
            # (following logic of 'old' code the inflow into these reservoirs is
            # always zero, so either change this or leave them out!)


            TotalReservoirStorageM3 = lookupscalar(binding['TabTotStorage'], ReservoirSitePcr)
            TotalReservoirStorageM3C = compressArray(TotalReservoirStorageM3)
            self.var.TotalReservoirStorageM3CC = np.compress(self.var.ReservoirSitesC > 0,TotalReservoirStorageM3C)

            # Total storage of each reservoir [m3]
            ConservativeStorageLimit = lookupscalar(binding['TabConservativeStorageLimit'], ReservoirSitePcr)
            ConservativeStorageLimitC = compressArray(ConservativeStorageLimit)
            self.var.ConservativeStorageLimitCC = np.compress(self.var.ReservoirSitesC > 0,ConservativeStorageLimitC)

            # Conservative storage limit (fraction of total storage, [-])
            NormalStorageLimit = lookupscalar(binding['TabNormalStorageLimit'], ReservoirSitePcr)
            NormalStorageLimitC = compressArray(NormalStorageLimit)
            self.var.NormalStorageLimitCC = np.compress(self.var.ReservoirSitesC > 0,NormalStorageLimitC)

            # Normal storage limit (fraction of total storage, [-])
            FloodStorageLimit = lookupscalar( binding['TabFloodStorageLimit'], ReservoirSitePcr)
            FloodStorageLimitC = compressArray(FloodStorageLimit)
            self.var.FloodStorageLimitCC = np.compress(self.var.ReservoirSitesC > 0,FloodStorageLimitC)

            # Flood storage limit (fraction of total storage, [-])
            NonDamagingReservoirOutflow = lookupscalar(binding['TabNonDamagingOutflowQ'], ReservoirSitePcr)
            NonDamagingReservoirOutflowC = compressArray(NonDamagingReservoirOutflow)
            self.var.NonDamagingReservoirOutflowCC = np.compress(self.var.ReservoirSitesC > 0,NonDamagingReservoirOutflowC)

            # Non-damaging reservoir outflow [m3/s]
            NormalReservoirOutflow = lookupscalar( binding['TabNormalOutflowQ'], ReservoirSitePcr)
            NormalReservoirOutflowC = compressArray(NormalReservoirOutflow)
            self.var.NormalReservoirOutflowCC = np.compress(self.var.ReservoirSitesC > 0,NormalReservoirOutflowC)


            # Normal reservoir outflow [m3/s]
            MinReservoirOutflow = lookupscalar(binding['TabMinOutflowQ'], ReservoirSitePcr)
            MinReservoirOutflowC = compressArray(MinReservoirOutflow)
            self.var.MinReservoirOutflowCC = np.compress(self.var.ReservoirSitesC > 0,MinReservoirOutflowC)


            # Minimum reservoir outflow [m3/s]

            # Repeatedly used expressions in reservoirs routine
            self.var.DeltaO = self.var.NormalReservoirOutflowCC - self.var.MinReservoirOutflowCC
            self.var.DeltaLN = self.var.NormalStorageLimitCC - 2 * self.var.ConservativeStorageLimitCC
            self.var.DeltaLF = self.var.FloodStorageLimitCC -  self.var.NormalStorageLimitCC

            #ReservoirInitialFillValue = loadmap('ReservoirInitialFillValue')
            #ReservoirInitialFill = ifthenelse(ReservoirInitialFillValue == -9999, self.var.NormalStorageLimit, ReservoirInitialFillValue)
            ReservoirInitialFillValue = loadmap('ReservoirInitialFillValue')
            if np.max(ReservoirInitialFillValue)==-9999:
               ReservoirInitialFill = self.var.NormalStorageLimitCC,
            else:
                ReservoirInitialFill =  np.compress(self.var.ReservoirSitesC > 0, ReservoirInitialFillValue)

            self.var.ReservoirFillCC = ReservoirInitialFill
            # Initial reservoir fill (fraction of total storage, [-])
            # -9999: assume reservoirs are filled to normal storage limit
            ReservoirStorageIniM3CC = ReservoirInitialFill * self.var.TotalReservoirStorageM3CC
            # Initial reservoir storage [m3]
            self.var.ReservoirStorageM3CC = ReservoirStorageIniM3CC.copy()
            #self.var.ReservoirFill = ReservoirInitialFill.copy()
            #  Initial fill of reservoirs (fraction of total storage, [-])

            self.var.ReservoirStorageIniM3 = globals.inZero.copy()
            np.put(self.var.ReservoirStorageIniM3,self.var.ReservoirIndex,ReservoirStorageIniM3CC)


    def dynamic_inloop(self):
        """ dynamic part of the lake routine
           inside the sub time step routing routine
        """

        # ************************************************************
        # ***** RESERVOIR
        # ************************************************************

        if option['simulateReservoirs']:


            #ReservoirInflow = cover(ifthen(defined(self.var.ReservoirSites), upstream(
            #    self.var.LddStructuresKinematic, self.var.ChanQ)), scalar(0.0))

            ReservoirInflowCC = np.bincount(self.var.downstruct, weights=self.var.ChanQ)[self.var.ReservoirIndex]
            # ReservoirInflow=cover(ifpcr(defined(self.var.ReservoirSites),upstream(self.var.LddStructuresKinematic,self.var.ChanQ)),null)
            # Reservoir inflow in [m3/s]
            # 20-2-2006: Replaced ChanQKin by ChanQ (if this results in problems change back to ChanQKin!)
            # 21-2-2006: Inflow now taken from 1st upstream cell(s), using LddStructuresKinematic
            # (LddStructuresKinematic equals LddKinematic, but without the pits/sinks upstream of the structure
            # locations; note that using Ldd here instead would introduce MV!)

            QResInM3Dt = ReservoirInflowCC * self.var.DtRouting
            # Reservoir inflow in [m3] per timestep
            ReservoirOutflow1 = np.minimum( self.var.MinReservoirOutflowCC, self.var.ReservoirStorageM3CC * self.var.InvDtSec)
            # Reservoir outflow [m3/s] if ReservoirFill le
            # 2*ConservativeStorageLimit
            ReservoirOutflow2 = self.var.MinReservoirOutflowCC + self.var.DeltaO * (self.var.ReservoirFillCC - 2 * self.var.ConservativeStorageLimitCC) / self.var.DeltaLN
            # Reservoir outflow [m3/s] if NormalStorageLimit le ReservoirFill
            # gt 2*ConservativeStorageLimit
            ReservoirOutflow3 = self.var.NormalReservoirOutflowCC + ((self.var.ReservoirFillCC - self.var.NormalStorageLimitCC)
                                / self.var.DeltaLF) * np.maximum(ReservoirInflowCC - self.var.NormalReservoirOutflowCC,
                                self.var.NonDamagingReservoirOutflowCC - self.var.NormalReservoirOutflowCC)
            # Reservoir outflow [m3/s] if FloodStorageLimit le ReservoirFill gt NormalStorageLimit
            # NEW 24-9-2004: linear transition between normal and non-damaging
            # outflow.
            ReservoirOutflow4 = np.maximum((self.var.ReservoirFillCC - self.var.FloodStorageLimitCC) *
                self.var.TotalReservoirStorageM3CC * self.var.InvDtSec, self.var.NonDamagingReservoirOutflowCC)
            # Reservoir outflow [m3/s] if ReservoirFill gt FloodStorageLimit
            # Depending on ReservoirFill the reservoir outflow equals ReservoirOutflow1, ReservoirOutflow2,
            # ReservoirOutflow3 or ReservoirOutflow4
            ReservoirOutflow = ReservoirOutflow1.copy()
            ReservoirOutflow = np.where(self.var.ReservoirFillCC > 2 * self.var.ConservativeStorageLimitCC,
                                ReservoirOutflow2, ReservoirOutflow)
            ReservoirOutflow = np.where(self.var.ReservoirFillCC > self.var.NormalStorageLimitCC,
                                ReservoirOutflow3, ReservoirOutflow)
            ReservoirOutflow = np.where(self.var.ReservoirFillCC > self.var.FloodStorageLimitCC,
                                ReservoirOutflow4, ReservoirOutflow)

            QResOutM3DtCC = ReservoirOutflow * self.var.DtRouting
            # Reservoir outflow in [m3] per sub step
            QResOutM3DtCC = np.minimum(QResOutM3DtCC, self.var.ReservoirStorageM3CC + QResInM3Dt)
            # Check to prevent outflow from becoming larger than storage +
            # inflow
            QResOutM3DtCC = np.maximum(QResOutM3DtCC, self.var.ReservoirStorageM3CC
                               + QResInM3Dt - self.var.TotalReservoirStorageM3CC)
            # NEW 24-9-2004: Check to prevent reservoir storage from exceeding total capacity
            # expression to the right of comma always negative unlesss capacity
            # is exceeded
            self.var.ReservoirStorageM3CC += QResInM3Dt - QResOutM3DtCC
            # New reservoir storage [m3]
            self.var.ReservoirFillCC = self.var.ReservoirStorageM3CC / self.var.TotalReservoirStorageM3CC
            # New reservoir fill


            # expanding the size
            self.var.QResOutM3Dt = globals.inZero.copy()
            np.put(self.var.QResOutM3Dt,self.var.ReservoirIndex,QResOutM3DtCC)

            self.var.ReservoirStorageM3 = globals.inZero.copy()
            self.var.ReservoirFill = globals.inZero.copy()
            np.put(self.var.ReservoirStorageM3,self.var.ReservoirIndex,self.var.ReservoirStorageM3CC)
            np.put(self.var.ReservoirFill,self.var.ReservoirIndex,self.var.ReservoirFillCC)


"""
 ######################################################################

 ##       ####  ######  ######## ##        #######   #######  ########
 ##        ##  ##    ## ##       ##       ##     ## ##     ## ##     ##
 ##        ##  ##       ##       ##       ##     ## ##     ## ##     ##
 ##        ##   ######  ######   ##       ##     ## ##     ## ##     ##
 ##        ##        ## ##       ##       ##     ## ##     ## ##     ##
 ##        ##  ##    ## ##       ##       ##     ## ##     ## ##     ##
 ######## ####  ######  ##       ########  #######   #######  ########

######################################################################
"""

__authors__ = "Ad de Roo, Emiliano Gelati, Peter Burek, Johan van der Knijff, Niko Wanders"
__version__ = "Version: 2.12.05 ecmwf"
__date__ ="20 Nov 2019"
__copyright__ = "Copyright 2018, European Commission - Joint Research Centre"
__maintainer__ = "Ad de Roo"
__status__ = "Operation EFAS"


#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# to work with the new grid engine JRC - workaround with error on pyexpat
from pyexpat import *
import xml.dom.minidom
from netCDF4 import Dataset
from pcraster import *
from pcraster.framework import *

# ---------------------------


from Lisflood_initial import *
from Lisflood_dynamic import *
from Lisflood_monteCarlo import *
from Lisflood_EnKF import *

#class LisfloodModel(LisfloodModel_ini, LisfloodModel_dyn):
class LisfloodModel(LisfloodModel_ini, LisfloodModel_dyn, LisfloodModel_monteCarlo, LisfloodModel_EnKF):
    """ Joining the initial and the dynamic part
        of the Lisflood model
    """

# ==================================================
# ============== LISFLOOD execute ==================
# ==================================================

def Lisfloodexe():

    # read options and bindings and launch Lisflood model computation
    # CM: returns option binding and ReportSteps - global dictionaries
    optionBinding(settings, optionxml)
    # read all the possible option for modelling and for generating output
    # read the settingsfile with all information about the catchments(s)
    # and the choosen option for modelling and output

    bindkey = sorted(binding.keys())  # CM: not used!

    #os.chdir(outputDir[0])
    # this prevent from using relative path in settings!


    checkifDate('StepStart','StepEnd')
    # check 'StepStart' and 'StepEnd' to be >0 and 'StepStart'>'StepEnd'
    # return modelSteps

    # CM remove steps from ReportSteps that are not included in simulation period
    for key in list(ReportSteps.keys()):  ## creates a list of all keys
        ReportSteps[key] = [x for x in ReportSteps[key] if x >= modelSteps[0]]
        ReportSteps[key] = [x for x in ReportSteps[key] if x <= modelSteps[1]]

    if option['InitLisflood']: print "INITIALISATION RUN"

    #CM: print start step and end step
    print "Start Step - End Step: ",modelSteps[0]," - ", modelSteps[1]
    print "Start Date - End Date: ",inttoDate(modelSteps[0]-1,Calendar(binding['CalendarDayStart']))," - ",\
        inttoDate(modelSteps[1]-1,Calendar(binding['CalendarDayStart']))


    if Flags['loud']:
        # CM: print state file date
        print "State file Date: ",
        try:
            print inttoDate(Calendar(binding["timestepInit"]), Calendar(binding['CalendarDayStart']))
        except:
            print Calendar(binding["timestepInit"])

        # CM: print start step and end step for reporting model state maps
        print "Start Rep Step  - End Rep Step: ", ReportSteps['rep'][0], " - ", ReportSteps['rep'][-1]
        print "Start Rep Date  - End Rep Date: ", inttoDate(Calendar(ReportSteps['rep'][0] - 1),
                                                            Calendar(binding['CalendarDayStart'])), \
            " - ", inttoDate(Calendar(ReportSteps['rep'][-1] - 1), Calendar(binding['CalendarDayStart']))

        # CM: messages at model start
        print"%-6s %10s %11s\n" %("Step","Date","Discharge"),


    # CM: Lisflood e' una istanza della classe LisfloodModel, la quale descrive il comportamento generale del modello
    # CM: LisfloodModel include i due metodi initial (per l'inizializzazione) e dynamic (calcoli da ripetere ad ogni passo di tempo)
    Lisflood = LisfloodModel()
    # CM: stLisflood e' una istanza della classe DynamicFramework
    # CM: applico la DynamicFramework al modello Lisflood, specifico istante iniziale e finale
    stLisflood = DynamicFramework(Lisflood, firstTimestep=modelSteps[0], lastTimeStep=modelSteps[1])
    stLisflood.rquiet = True
    stLisflood.rtrace = False


    """
    ----------------------------------------------
    Monte Carlo and Ensemble Kalman Filter setting
    ----------------------------------------------
    """
    # CM: Ensamble Kalman filter
    try:
        EnKFset = option['EnKF']
    except:
        EnKFset = 0
    # CM: MonteCarlo
    try:
        MCset = option['MonteCarlo']
    except:
        MCset = 0
    if option['InitLisflood']:
        MCset = 0
        EnKFset = 0
    if EnKFset and not MCset:
        msg = "Trying to run EnKF with only 1 ensemble member \n"
        raise LisfloodError(msg)
    if EnKFset and FilterSteps[0] == 0:
        msg = "Trying to run EnKF without filter timestep specified \nRunning LISFLOOD in Monte Carlo mode \n"
        print LisfloodWarning(msg)
        EnKFset = 0
    if MCset and EnsMembers[0] <= 1:
        msg = "Trying to run Monte Carlo simulation with only 1 member \nRunning LISFLOOD in deterministic mode \n"
        print LisfloodWarning(msg)
        MCset = 0
    if MCset:
        mcLisflood = MonteCarloFramework(stLisflood, nrSamples=EnsMembers[0])
        if nrCores[0] > 1:
            mcLisflood.setForkSamples(True, nrCPUs=nrCores[0])
        if EnKFset:
            kfLisflood = EnsKalmanFilterFramework(mcLisflood)
            kfLisflood.setFilterTimesteps(FilterSteps)
            print LisfloodRunInfo(mode = "Ensemble Kalman Filter", outputDir = outputDir[0], Steps = len(FilterSteps), ensMembers=EnsMembers[0], Cores=nrCores[0])
            kfLisflood.run()
        else:
            print LisfloodRunInfo(mode = "Monte Carlo", outputDir = outputDir[0], ensMembers=EnsMembers[0], Cores=nrCores[0])
            mcLisflood.run()
    else:
        """
        ----------------------------------------------
        Deterministic run
        ----------------------------------------------
        """
        print LisfloodRunInfo(mode = "Deterministic", outputDir = outputDir[0])
    # CM: run of the model inside the DynamicFramework
        stLisflood.run()
    # cProfile.run('stLisflood.run()')
    # python -m cProfile -o  l1.pstats lisf1.py settingsNew3.xml
    # gprof2dot -f pstats l1.pstats | dot -Tpng -o callgraph.png

    if Flags['printtime']:
        print "\n\nTime profiling"
        print "%2s %-17s %10s %8s" %("No","Name","time[s]","%")
        div = 1
        timeSum = np.array(timeMesSum)
        if MCset:
            div = div * EnsMembers[0]
        if EnKFset:
            div = div * (len(FilterSteps)+1)
        if EnKFset or MCset:
            timePrint = np.zeros(len(timeSum)/div)
            for i in range(len(timePrint)):
                timePrint[i] = np.sum(timeSum[range(i, len(timeSum), len(timeSum)/div)])
        else:
            timePrint = timeSum
        for i in xrange(len(timePrint)):
            print "%2i %-17s %10.2f %8.1f"  %(i,timeMesString[i],timePrint[i],100 * timePrint[i] / timePrint[-1])
    i=1

# ==================================================
# ============== USAGE ==============================
# ==================================================


def usage():
    """ prints some lines describing how to use this program
        which arguments and parameters it accepts, etc
    """
    print 'LisfloodPy - Lisflood using pcraster Python framework'
    print 'Authors: ', __authors__
    print 'Version: ', __version__
    print 'Date: ', __date__
    print 'Status: ', __status__
    print """
    Arguments list:
    settings.xml     settings file

    -q --quiet       output progression given as .
    -v --veryquiet   no output progression is given
    -l --loud        output progression given as time step, date and discharge
    -c --check       input maps and stack maps are checked, output for each input map BUT no model run
    -h --noheader    .tss file have no header and start immediately with the time series
    -t --printtime   the computation time for hydrological modules are printed
    -d --debug       debug outputs
    """
    sys.exit(1)

def headerinfo():

   print "LisfloodPy ",__version__," ",__date__,
   print """
Water balance and flood simulation model for large catchments\n
(C) Institute for Environment and Sustainability
    Joint Research Centre of the European Commission
    TP122, I-21020 Ispra (Va), Italy\n"""


# ==================================================
# ============== MAIN ==============================
# ==================================================

if __name__ == "__main__":
    # CM: if arguments are missing display usage info
    if len(sys.argv) < 2:
        usage()

    # CM read OptionTserieMaps.xml in the same folder as Lisflood main (lisf1.py)
    LF_Path = os.path.dirname(sys.argv[0])
    LF_Path = os.path.abspath(LF_Path)

    # OptionTserieMaps.xml file
    optionxml = os.path.normpath(LF_Path + "/OptionTserieMaps.xml")

    # CM: setting.xml file
    settings = sys.argv[1]

    # CM: arguments list
    args = sys.argv[2:]

    # CM: Flags - set model behavior (quiet,veryquiet, loud, checkfiles, noheader,printtime,debug)
    globalFlags(args)
    # setting of global flag e.g checking input maps, producing more output information
    if not(Flags['veryquiet']) and not(Flags['quiet']) : headerinfo()
    Lisfloodexe()



#
#___INFO__MARK_BEGIN__
##########################################################################
#
# script /H01_Fresh_Water/Lisflood_actualModel/Lisflood/lisf1.job
# run in the Grid:  qsub lisf1.job 

#
##########################################################################
#___INFO__MARK_END__

#
# What the script does: script.py settings
#The grid settings use the UNIX storage path, instead of local windows PC folder "c:\....")

# tell grid I want C shell
!/bin/sh 
# where to send emails about the status of the job (if the mail works!)
$ -M adrian.trif@jrc.ec.europa.eu    

# I want to receive emails at START and FINISH of job
#$ -m abe  
#$ -o /H01_Fresh_Water/Europe/output/testgrid/tmp.out
#$ -e /H01_Fresh_Water/Europe/output/testgrid/tmp.err


echo "Start - `date`"

python /H01_Fresh_Water/Lisflood_actualModel/Lisflood/lisf1.py /H01_Fresh_Water/Europe/LisfloodEurope/settingsEurope5kObs_GRID.xml

echo "Finish - `date`"

# -- other settings script name ---
#$ -N Lisf1grid 
#$ -S /bin/sh

#! /usr/bin/env python
#
# python script to generate a valid stepfile for WRF cycling 
#
import sys
import os
import pandas
import calendar

filename = 'stepfile' # default filename
lecho = False
lperiod = False
dateargs = [] # list of date arguments passed to date_range
for arg in sys.argv[1:]:
  if arg[:11] == '--interval=':
    freq = arg[11:].lower() # remains a string and is interpreted by date_range
  elif arg[:8] == '--steps=':
    lperiod = True; periods = int(arg[8:]) + 1 # each step is bounded by two timestamps
  elif arg == '-e' or arg == '--echo': 
    lecho = True
  elif arg == '-h' or arg == '--help':
    print ''
    print "Usage: "+sys.argv[0]+" [-e] [-h] [--interval=interval] [--steps=steps] begin-date [end-date]"
    print "       Interval, begin-date and end-date or steps must be specified."
    print ""
    print "  --interval=   step spacing / interval (D=days, W=weeks, M=month)"
    print "  --steps=      number of steps in stepfile"
    print "  -e | --echo   print steps to stdout instead of writing to stepfile"
    print "  -h | --help   print this message"
    print ''
    sys.exit(1)    
  else: 
    dateargs.append(arg)
    
# output patterns
lmonthly = False
dateform = '%Y-%m-%d_%H:%M:%S'
# N.B.: because pandas date_range always anchors intervals at the end of the month, we have to subtract one
#       day and add it again later, in order to re-anchor at the first of the month
stepform = '%Y-%m-%d'
offset = pandas.DateOffset() # no offset
if 'w' in freq:
  oo = 1 if '-sun' in freq else 0
  offset = pandas.DateOffset(days=pandas.to_datetime(dateargs[0]).dayofweek + oo)
elif 'm' in freq: 
  lmonthly = True
  stepform = '%Y-%m'
  offset = pandas.DateOffset(days=pandas.to_datetime(dateargs[0]).day)

begindate = pandas.to_datetime(dateargs[0]) - offset 
# check input and generate datelist
if lperiod:
  if len(dateargs) != 1: raise ValueError, 'Can only specify begin-date, if the number of periods is given.'
  datelist = pandas.date_range(begindate, periods=periods, freq=freq) # generate datelist
else:
  if len(dateargs) != 2: raise ValueError, 'Specify begin-date and end-date, if no number of periods is given.'
  enddate = pandas.to_datetime(dateargs[1]) - offset
  datelist = pandas.date_range(begindate, enddate, freq=freq) # generate datelist

# open file, if not writing to stdout
if not lecho: stepfile = open(filename, mode='w')
# iterate over dates (skip first)
lastdate = datelist[0] + offset # first element
for date in datelist[1:]:
  currentdate = date + offset
  if lmonthly:
    mon = date.month +1 
    if mon == 2: maxdays = 29 if calendar.isleap(date.year) else 28  
    elif mon in [4, 6, 9, 11]: maxdays = 30
    else: maxdays = 31
    if currentdate > date + pandas.DateOffset(days=maxdays): 
      currentdate = date + pandas.DateOffset(days=maxdays)
    
  #TODO: there is still a problem with varying length of month: 
  #print lastdate, currentdate
  # generate line for last step
  stepline = "{0:s}   '{1:s}'  '{2:s}'\n".format(lastdate.strftime(stepform),lastdate.strftime(dateform),
                                                 currentdate.strftime(dateform))
  # write to appropriate output 
  if lecho: sys.stdout.write(stepline)
  else: stepfile.write(stepline)
  # remember last step
  lastdate = currentdate
# close file
if not lecho: stepfile.close()

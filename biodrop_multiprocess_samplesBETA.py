import numpy as np
import logging
import pwd
import grp
import os
import time
import shutil
from utils import *
import json
import argparse
import subprocess
import glob
import sys
from os import path
from datetime import datetime


num_cpus = os.cpu_count()
logfile_filename = '/home/cisco/VFO/biodrop_multiprocess_samples.log'
working_directory = '/home/cisco/VFO/'


process_directory = '/var/www/html/process_samples/'
job_filemask =process_directory+'*.job'

file_list = glob.glob(job_filemask)

procs_list = []
proc_filename_list = {}


nowork = True
if len(file_list) > 0:
	nowork = False

logfile=""

if nowork==False:
	logfile = open(logfile_filename,'a')
	logfile.write('\n<START OF PROCESS>\n')
	date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
	logfile.write('Start_TimeStamp:'+date_time_stamp+'\n')

	logfile.write('CPUs:'+str(num_cpus)+'\n')

	if num_cpus > 1:
		num_cpus = num_cpus - 1 #reserve core (for server itself)

	logfile.write('CPUsAssignedToProcess:'+str(num_cpus)+'\n')
	logfile.write('ProcessDirectory:'+process_directory+'\n')
	logfile.write('JobFiles:'+str(len(file_list))+'\n')
	logfile.close()
else:
	logfile = open(logfile_filename,'a')
	date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
	logfile.write('<NO WORK>'+date_time_stamp+'\n')
	logfile.close()
	sys.exit()



for filename in file_list:
	if path.exists(filename):

		renamed_file = False
		error_text = ''
		try:
			os.rename(filename,filename+'.proc')
			renamed_file = True
		except Exception as err:
			error_text='*RENAME ERROR*:'+filename+'\n'

		logfile = open(logfile_filename,'a')
		if len(error_text)>0:
			logfile.write(error_text)	
		logfile.write('PROCS_Count:'+str(len(procs_list))+'\n')
		logfile.close()

		if renamed_file == True:
			logfile = open(logfile_filename,'a')
			logfile.write('ProcessingJobFile:'+filename+'.proc'+'\n')
			# GET THE INFO AND CREATE THE CMD LINE CALL
			file=open(filename+'.proc','rt')
			contents = file.read()
			my_dict = json.loads(contents)
			file.close()
			user_id = my_dict['user_id']
			data_dir = my_dict['data_dir']
			test_id = my_dict['test_id']
			audio_file = my_dict['audio_file']
			user_id = my_dict['user_id']
			mode = my_dict['mode']

			cmdcall = '/home/cisco/miniconda3/bin/python3 '+working_directory+'healthdrop_audio_processor.py --data_dir '+data_dir
			cmdcall = cmdcall +' --user_id '+user_id
			cmdcall = cmdcall +' --test_id '+test_id
			cmdcall = cmdcall +' --audio_file '+audio_file
			cmdcall = cmdcall +' --mode 1'

			logfile.write('JOB_UserID:'+user_id+'\n')
			logfile.write('JOB_CMD:'+cmdcall+'\n')

			a_proc=subprocess.Popen(cmdcall,shell=True, cwd=working_directory)
			procs_list.append(a_proc)
			proc_filename_list[str(a_proc.pid)]=filename+'.proc'

			logfile.write('JOB_EXECUTED:'+proc_filename_list[str(a_proc.pid)]+'\n')


			date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
			logfile.write('JOB_Start_TimeStamp:'+date_time_stamp+'\n')
			logfile.write('JOB_PID:'+str(a_proc.pid)+'\n')

			if len(procs_list)>=num_cpus:
				logfile.write('[[WARNING: Procs_Limit_Saturation_Detected]] list_count:'+str(len(procs_list))+'- CPUs:'+str(num_cpus)+'\n')
			logfile.close()

			while len(procs_list)>=num_cpus:
				time.sleep(5.0)
				for proc in procs_list:
					if proc.poll() is None:
						continue
					logfile = open(logfile_filename,'a')
					date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
					logfile.write('JOB_End_TimeStamp:'+date_time_stamp+'\n')
					logfile.write('JOB_Release_PID:'+str(proc.pid)+'\n')
					logfile.write('JOB_Removing_Job_File:'+proc_filename_list[str(proc.pid)]+'\n')
					os.remove(proc_filename_list[str(proc.pid)])
					procs_list.remove(proc)
					del proc_filename_list[str(proc.pid)]
					logfile.write('JOB_Removal_Process:Complete\n')
					logfile.write('JOB_Procs_Remaining_Release:'+str(len(procs_list))+'\n')
					logfile.close()


if len(procs_list):
	logfile = open(logfile_filename,'a')
	date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
	logfile.write('Procs_To_Release:'+str(len(procs_list))+'\n')
	logfile.write('Procs_<END_FLUSH>_Start_TimeStamp:'+date_time_stamp+'\n')
	logfile.close()

	while len(procs_list):
		time.sleep(5.0)
		for proc in procs_list:
			if proc.poll() is None:
				continue
			logfile = open(logfile_filename,'a')
			date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
			logfile.write('JOB_End_TimeStamp:'+date_time_stamp+'\n')
			logfile.write('JOB_Releasing_PID'+str(proc.pid)+'\n')
			logfile.write('JOB_Removing_Job_File:'+proc_filename_list[str(proc.pid)]+'\n')
			os.remove(proc_filename_list[str(proc.pid)])
			procs_list.remove(proc)
			del proc_filename_list[str(proc.pid)]
			logfile.write('JOB_Removal_Process:Complete\n')
			logfile.write('JOB_Procs_Remaining_Release:'+str(len(procs_list))+'\n')
			logfile.close()
	
	logfile = open(logfile_filename,'a')
	date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
	logfile.write('Procs_<END_FLUSH>_End_TimeStamp:'+date_time_stamp+'\n')
	logfile.close()

logfile = open(logfile_filename,'a')
date_time_stamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
logfile.write('End_TimeStamp:'+date_time_stamp+'\n')
logfile.write('<END OF PROCESS>'+'\n')
logfile.close()


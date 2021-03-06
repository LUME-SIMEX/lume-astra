#!/usr/bin/env python3

from astra import parsers, tools, archive

from pmd_beamphysics import ParticleGroup

import numpy as np


import tempfile
import shutil
import os, platform
from time import time


           
class AstraGenerator:
    """
    Class to run Astra's particle generator
    
    
    The file for Astra is written in:
    .output_file
    
    
    
    
    """
    def __init__(self, 
                 input_file = None,
                 generator_bin = '$GENERATOR_BIN',
                 #path=None,
                 use_tempdir=True,
                 workdir=None,                 
                 verbose=False
                ):
        # Save init
        self.generator_bin = generator_bin 
        self.original_input_file = input_file
        #self.path = path
        self.use_tempdir = use_tempdir
        self.workdir = workdir
        self.verbose=verbose  
        
        # Run control
        self.configured = False
        self.finished = False
        
        # These will be filled
        self.input = {}
        self.output = {}
        
        # Call configure
        if input_file:
            self.load_input(input_file)
            self.configure()
        

        
    def load_input(self, input_filePath, absolute_paths=True):
        f = tools.full_path(input_filePath)
        self.original_path, self.original_input_file = os.path.split(f) # Get original path, filename
        self.input = parsers.parse_astra_input_file(f)['input']            
           
        
    def configure(self):
        
        # Check that binary exists
        self.generator_bin = tools.full_path(self.generator_bin)
        assert os.path.exists(self.generator_bin), 'ERROR: Generator binary does not exist:'+self.generator_bin    

        
        # Set paths
        if self.use_tempdir:
            # Need to attach this to the object. Otherwise it will go out of scope.
            self.tempdir = tempfile.TemporaryDirectory(dir=self.workdir)
            self.path = self.tempdir.name
        else:
            # Work in place
            self.path = self.original_path            
    
        self.input_file = os.path.join(self.path, self.original_input_file)    
        
        # make the ouput file an absolute path
        self.input['fname'] = os.path.join(self.path, 'generator.part')
        
        self.configured = True

        
    def get_run_script(self, write_to_path=True):
        """
        Assembles the run script. Optionally writes a file 'run' with this line to path.
        """
        
        #_, infile = os.path.split(self.input_file)
        
        runscript = [self.generator_bin, self.input_file]
            
        if write_to_path:
            with open(os.path.join(self.path, 'run'), 'w') as f:
                f.write(' '.join(runscript))
            
        return runscript        
        
        
    def run(self):  
        
        self.write_input_file()
        
        runscript = self.get_run_script()
        res = tools.execute2(runscript, timeout=None)
        self.log = res['log']

        self.vprint(self.log)
        
        # This is the file that should be written
        if os.path.exists(self.input['fname']):
            self.finished = True
        else:
            print(self.input['fname'], 'does not exist.')
            #print('The input file already exists! This is a problem!')
            print(f'Here is what the current working dir looks like: {os.listdir(self.path)}')
            
 
        self.load_output()
        
    @property
    def output_file(self):
        return os.path.join(self.path, self.input['fname'])
        
    def load_output(self):
        pfile = self.output_file
        data = parsers.parse_astra_phase_file(pfile)
        # Clock time is used when at cathode
        data['t'] = data['t_clock']
        P = ParticleGroup(data=data)
        
        self.output['particles'] = P
        
    def write_input_file(self):
        
        parsers.write_namelists({'input':self.input}, self.input_file)     
        
        
    def vprint(self, *args, **kwargs):
        # Verbose print
        if self.verbose:
            print(*args, **kwargs)           
        
        
        

    

        
          
  

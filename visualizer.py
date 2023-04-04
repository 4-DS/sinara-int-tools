from graphviz import Digraph
import logging

from pathlib import Path

import sys
import os
import json
import glob
from subprocess import STDOUT, PIPE, Popen, run, CalledProcessError

import json
    
logging.basicConfig(stream=sys.stdout)

logger = logging.getLogger('test.SystemTest')
main_logger = logging.getLogger('visualizer')


def _prettify_url(url):
    words = url.split("/")
    parts = 0
    result=""

    for i in words[1:]:
        result = f"{result}/{i}"
        parts += 1
        if parts == 3:
            result = f"{result}\\n"
            parts = 0
    return result

def _prettify_params(params):
    if params is None:
        return ""

    logger.debug('_prettify_params')
    logger.debug(repr(params))
    
    pparams = json.dumps(params, default=str, ensure_ascii=False, indent=4)   
    logger.debug(repr(pparams))
    pparams = pparams.translate({
            ord("{"): "", 
            ord("}"): "" 
    })

    logger.debug(repr(pparams)) 
    pparams=pparams.rstrip()

    logger.debug(repr(pparams))
    pparams = "\n".join([ w[4:] for w in pparams.split("\n") ])

    logger.debug(repr(pparams))
    pparams = pparams.translate( {
            ord("\n"): "\\l",
            ord(" "): "\ " 
    })
    logger.debug(repr(pparams))

    return pparams+"\\l"

def is_step(step_folder):
    params_files = glob.glob(f"{step_folder}/params/*.json")
    for step_params_file in params_files:
        with open(step_params_file, 'r') as sp:
            try:
                params = json.load(sp)
                if 'step_params' in params:
                    if 'step_name' in params['step_params']:
                        return True
            except Exception as e:
                main_logger.error(f'Error reading {param_file}, skipping')
                main_logger.debug(e)
    return False

def get_step_folders(steps_folder_glob):
    result = []
    step_folders = glob.glob(f"{steps_folder_glob}")
    for folder in step_folders:
        if os.path.isdir(folder):
            try:
                if is_step(folder):
                    result.append(folder)
            except Exception as e:
                main_logger.error(f'Cannot read step_params.json in step at {folder}, skipping step')
                main_logger.error(e)
    return result

def run_steps(step_list):
    #run sinara steps
    current_env = {}
    current_env.update(os.environ)
    current_env.update({"VISUALIZER_SESSION_RUN_ID": os.getenv("VISUALIZER_SESSION_RUN_ID")})
    
    for step_dir in step_list:
        with Popen(f"python step.dev.py", \
                   shell=True, \
                   stdout=PIPE, \
                   stderr=STDOUT, \
                   cwd=step_dir, \
                   env=current_env) as child_process, \
             open(f'{step_dir}.log', 'w') as logfile:

            for line in child_process.stdout:
                decoded_line = line.decode("utf-8")
                sys.stdout.write(decoded_line)
                logfile.write(decoded_line)
            child_process.communicate()
            #print(child_process.returncode )
            
            #if child_process.returncode != 0:
            #    raise Exception(f"SINARA Python module '{self.input_nb_name}' is failed!")


def show(graph_name):
    
    t = Digraph(graph_name)
    t.attr(rank='max')
    t.attr('node', shape='record', fontsize='10', fontname = "Courier", color='orange', fillcolor='lightblue2', style='filled')
    t.attr('edge', shape='circle', color='orange1')
    
    run_id_folder = os.getenv("VISUALIZER_SESSION_RUN_ID")
       
    #show sinara_notebooks
    substeps = glob.glob(f"{run_id_folder}/*.json")
    for substep_report in substeps:

        with open(f'{substep_report}') as json_file:
           susbtep_content = json.load(json_file)

        #for k,v in self._dsml_notebooks.items(): 
        #    t.node(k,"{" + k + "|" + _prettify_params(v.params) + "}")
        #    t.attr('node', shape='Mrecord')
        #k = step_name + '-' + os.path.basename(substep)
        step_name = susbtep_content['step_name']
        substep_name = susbtep_content['substep_name']
        #v = {}
        #v["params"] = {}
        t.node(step_name,"{" + step_name + "|" + substep_name + "}")
        t.attr('node', shape='Mrecord')

        #show resource catalogue

        #for k,v in self.entity_catalogue.items():
        #    t.node(v,"{" + k + "|" + _prettify_url(v) + "}")

        t.attr('node', shape='Mrecord', fontsize='10', fontname = "Courier", style='solid')

        #show dsml notebooks resources and artifacts

        #k = step + '-' + os.path.basename(substep) 
        a7s = susbtep_content.get("outputs")
        r7s = susbtep_content.get("inputs")

        if r7s is not None:
            for rk, rv in r7s.items():
                #t.node(rv,"{" + rk + "|" + _prettify_url(rv) + "}")
                #t.edge(rv,k)

                t.node(rk,"{" + rk + "}")
                t.edge(rk,step_name)



        if a7s is not None:
            for ak, av in a7s.items():
                #t.node(av,"{" + ak + "|" + _prettify_url(av) + "}")
                #t.edge(k,av)

                t.node(ak,"{" + ak + "}")
                t.edge(step_name,ak)
    return t

def get_visualizer_run_id():
    from datetime import datetime
    current_folder = os.path.abspath(os.path.dirname(__file__))
    run_id = os.path.join(current_folder, 'tmp', 'visualizer', f"run-{datetime.now().strftime('%y-%m-%d-%H%M%S')}")
    os.environ["VISUALIZER_SESSION_RUN_ID"] = run_id
    return run_id
    
def visualize_pipeline(steps_folder_glob=None, graph_name=None):
    if not steps_folder_glob:
        main_logger.error('"steps_folder_glob" was not provided, cannot get steps')
        return None
        
    if not graph_name:
        graph_name = 'graph'
  
    os.environ["DESIGN_MODE"] = 'TRUE'
    visualizer_run_id = get_visualizer_run_id()
    os.makedirs(visualizer_run_id)
    step_list = get_step_folders(steps_folder_glob)
    
    run_steps(step_list)
    # return graphviz object to render it in a cell
    return show(graph_name)
import sys, json, os, glob, subprocess
import numpy as np

def move_mda_data(source_animal_path, target_animal_path, animal, dates):
    for date in dates:
        source_mda_paths = glob.glob(f'{source_animal_path}/{date}/*.mda')
        source_mda_paths.sort()
        for source_path in source_mda_paths:
            filename = source_path.split('/')[-1]
            target_dir = f'{target_animal_path}/{date}/'
            os.makedirs(target_dir, exist_ok=True)
            print('copying', source_path, 'to', target_dir)
            status = subprocess.call(f'rsync -avP {source_path} {target_dir}', shell=True)


def run_sort(animal, dates, ntrodes, input_path, output_path, curation_args,
             extract_marks=True, extract_clips=True, clip_size=100, freq_min=600,
             freq_max=6000, adjacency_radius=-1, detect_threshold=3, detect_sign=-1):

    for date in dates:
        print(f'running {animal} date:{date} ntrodes:{ntrodes}')
        mountain_mda_path = os.path.join(input_path, str(date), f'{date}_{animal}.mountain/')
        mountain_out_path = os.path.join(output_path, str(date), 'ms4')
        for nt in ntrodes:
            mountain_mda_nt_path = mountain_mda_path + f'/nt{nt}/'
            mountain_out_nt_path = mountain_out_path + f'/nt{nt}/'
            os.makedirs(mountain_out_nt_path, exist_ok=True)
            mda_opts = {'anim':animal, 'date':date, 'ntrode':nt, 'data_location':input_path}
            raw_mda = mountain_mda_nt_path+'/raw.mda'

            # create concatenated mda if it doesn't exist
            if not os.path.isfile(raw_mda):
                os.makedirs(mountain_mda_nt_path, exist_ok=True)
                # create params if it doesn't exist
                params_file = os.path.join(mountain_mda_nt_path, 'params.json')
                if not os.path.isfile(params_file):
                    params= {"samplerate":30000}
                    with open(params_file, 'w') as f:
                        json.dump(params, f, indent=4, sort_keys=True)
                print('creating concatenated epochs .mda: ', raw_mda)
                pyp.concat_eps(dataset_dir=mountain_mda_nt_path, mda_opts=mda_opts)

            print('####### NTRODE_INPUT:', raw_mda)
            print('####### NTRODE_OUTPUT', mountain_out_nt_path)

            pyp.filt_mask_whiten(dataset_dir=mountain_mda_nt_path,output_dir=mountain_out_nt_path,
                                 freq_min=freq_min,freq_max=freq_max, opts={})

            pyp.ms4_sort_on_segs(dataset_dir=mountain_mda_nt_path,output_dir=mountain_out_nt_path,
                                 adjacency_radius=adjacency_radius,detect_threshold=detect_threshold,
                                 detect_sign=detect_sign, mda_opts=mda_opts, opts={})
            pyp.merge_burst_parents(dataset_dir=mountain_mda_nt_path,output_dir=mountain_out_nt_path,opts={})
            pyp.add_curation_tags(dataset_dir=mountain_out_nt_path,output_dir=mountain_out_nt_path,**curation_args)

            if extract_marks:
                pyp.extract_marks(dataset_dir=mountain_out_nt_path,output_dir=mountain_out_nt_path)

            if extract_clips:
                pyp.extract_clips(dataset_dir=mountain_out_nt_path,output_dir=mountain_out_nt_path,clip_size=clip_size)
    return
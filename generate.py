import argparse
import json
import utils
import numpy as np
from joblib import Parallel, delayed
import os

# define the program description
des_text = 'Please use -i to specify the json file and -o to specify the output path.'

# initiate the parser
parser = argparse.ArgumentParser(description=des_text)
parser.add_argument('--input', '-i', help="(Required) Path of VoTT JSON file")
parser.add_argument('--output', '-o', help="(Optional) Path of output files")
args = parser.parse_args()

if not args.input:
    print('Please specify the json file with -i')
    exit(1)

input_path = args.input

if not args.output:
    output_path = './results/'
else:
    output_path = args.output
    if not output_path.endswith('/'):
        output_path += '/'

with open(input_path, 'r', encoding='utf-8') as f:
    json_file = json.load(f)

tags = sorted(json_file['tags'],key=utils.sort_tag)
print('Label catagories:', len(tags))
print([elem['name'] for elem in tags])
print(json_file['tags'])

tags_color = {}
for tag in tags:
    tags_color.update({tag['name']: tag['color']})
assets = json_file['assets']

print('\nTotal assets:', len(assets.keys()))

labelled = []
negatives = []
for asset_id in assets.keys():
    asset = assets[asset_id]['asset']
    if 'regions' in assets[asset_id].keys():
        regions = assets[asset_id]['regions']
        if len(regions) > 0:
            labelled.append(asset_id)
        else:
            negatives.append(asset_id)
        
print('Labelled frames  :', len(labelled))
print('Unlabelled frames:', len(negatives))

# WIDTH = int(1920 / SAMPLE_RATE)
# HEIGHT = int(1080 / SAMPLE_RATE)

removed_asset_id = []
for asset_id in assets.keys():
    asset = assets[asset_id]['asset']
    if 'regions' in assets[asset_id].keys():
        regions = assets[asset_id]['regions']
        if len(regions) == 0:
            removed_asset_id.append(asset_id)
        else:
            for region in regions:
                if not len(region['tags']) == 1:
                    removed_asset_id.append(asset_id)
                    break
    
print('Removed frames:', len(removed_asset_id))

desired_frames = []
for asset_id in assets.keys():
    if asset_id in removed_asset_id:
        continue
    asset = assets[asset_id]['asset']

    desired_frames.append(asset['timestamp'])
        
desired_frames.sort()

if False:
    video = mpy.VideoFileClip('./000001.mov')
    find_nearest_frames(video, desired_frames)

print('\nDesired frames: ', len(desired_frames))
# print(desired_frames)

os.makedirs(f'{output_path}vis', exist_ok=True)
os.makedirs(f'{output_path}vis_with_raw', exist_ok=True)
os.makedirs(f'{output_path}tensors', exist_ok=True)
Parallel(n_jobs=16)(delayed(utils.generate_labels)\
                (assets[asset_id], input_path, output_path, desired_frames, tags, tags_color)\
                 for asset_id in assets.keys())

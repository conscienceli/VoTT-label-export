import numpy as np
from PIL import Image, ImageDraw, ImageColor
import pickle

def find_inner_point(image):
    image = np.array(image)
    for row_id, row in enumerate(image):
        edge_point_count = 0
        for col_id, element in enumerate(row):
            if element and not image[row_id][col_id-1]:
                edge_point_count += 1
                if edge_point_count == 2:
                    return (col_id-1, row_id)
                elif edge_point_count > 2:
                    break
            elif element and edge_point_count:
                break
    return None


def draw_with_mask(image, mask, color):
    image = np.array(image, dtype=np.uint8)
    mask = np.array(mask, dtype=np.uint8)
    for row_id, row in enumerate(mask):
        for col_id, element in enumerate(row):
            if not element:
                continue
            image[row_id, col_id] = (image[row_id, col_id] + color) / 2
    return image


def draw_tensor_with_mask(tensor, mask, channel, new_value):
    tensor = np.array(tensor, dtype=np.uint8)
    mask = np.array(mask, dtype=np.uint8)
    for row_id, row in enumerate(mask):
        for col_id, element in enumerate(row):
            if not element:
                continue
            tensor[row_id, col_id, channel] = new_value
    return tensor


def standard_alpha_image(height, width):
    image = np.zeros((height, width, 4), dtype=np.uint8)
    for row_id, row in enumerate(image):
        for col_id, element in enumerate(row):
            image[row_id, col_id] = np.array((element[0],element[1],element[2],255))
    return Image.fromarray(image, 'RGBA')


def standard_labeled_tensor(height, width, channel):
    tensor = np.zeros((height, width, channel), dtype=np.uint8)
    for row_id, row in enumerate(tensor):
        for col_id, element in enumerate(row):
            tensor[row_id, col_id, 0] = 1
    return tensor


def generate_labels(record, input_path, output_path, desired_frames, tags, tags_color):
    asset = record['asset']
    regions = record['regions']
    if not asset['timestamp'] in desired_frames:
        return

    # For debug
    # if asset['name'].find('575.5') < 0:
    #     return
    
    raw_img_path = '/'.join(input_path.split('/')[:-1]) + '/' + asset['name']

    labeled_image = standard_labeled_tensor(asset['size']['height'], asset['size']['width'], len(tags)+1)
    labeled_image_vis = standard_alpha_image(asset['size']['height'], asset['size']['width'])
    labeled_image_vis_with_raw = Image.open(raw_img_path).convert('RGBA')
    
    for region in regions:
        flood_region = np.zeros((asset['size']['height'], asset['size']['width']), dtype=np.uint8)
        flood_region = Image.fromarray(flood_region, '1')
        draw = ImageDraw.Draw(flood_region)
        pre_point = region['points'][0]
        for curr_point in region['points'][1:]:
            draw.line((pre_point['x'], pre_point['y'], curr_point['x'], curr_point['y']), fill=1)
            pre_point = curr_point
        curr_point = region['points'][0]
        draw.line((pre_point['x'], pre_point['y'], curr_point['x'], curr_point['y']), fill=1)
        del draw
        inner_point = find_inner_point(flood_region)
        while inner_point:
            ImageDraw.floodfill(flood_region, xy=inner_point, value=1)
            inner_point = find_inner_point(flood_region)
        
        region_color = ImageColor.getrgb(tags_color[region['tags'][0]])
        
        labeled_image_vis = draw_with_mask(labeled_image_vis, flood_region, (region_color[0],region_color[1],region_color[2],200))
        labeled_image_vis = Image.fromarray(labeled_image_vis, 'RGBA')
        labeled_image_vis_with_raw = draw_with_mask(labeled_image_vis_with_raw, flood_region, (region_color[0],region_color[1],region_color[2],200))
        labeled_image_vis_with_raw = Image.fromarray(labeled_image_vis_with_raw, 'RGBA')
    
    labeled_image_vis.save(f"{output_path}vis/{asset['name']}.png")
    labeled_image_vis_with_raw.save(f"{output_path}vis_with_raw/{asset['name']}.png")
   
    labeled_image_temp = standard_labeled_tensor(asset['size']['height'], asset['size']['width'], len(tags)+1)
    for i in range(labeled_image.shape[-1]):
        labeled_image_temp[:,:,i] = np.array(Image.fromarray(labeled_image[:,:,i]*255,'L').resize((asset['size']['width'], asset['size']['height'])), dtype=np.uint8)/255
    labeled_image = labeled_image_temp
        
    with open(f"{output_path}tensors/{asset['name']}.pickle", 'wb') as pickle_file:
        pickle.dump(labeled_image, pickle_file)
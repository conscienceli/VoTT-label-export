import numpy as np
from PIL import Image, ImageDraw, ImageColor
import pickle

def find_inner_point(image, raw_image=None):
    image = np.array(image)
    if raw_image:
        raw_image = np.array(raw_image)
    else:
        raw_image = image

    for row_id, row in enumerate(image):
        for col_id, element in enumerate(row):
            if element and not image[row_id][col_id-1]:
                if is_inside_image(raw_image, row_id, col_id-1):
                    return (col_id-1, row_id)
    return None

def is_inside_image(image, row_id, col_id):
    dir_num = sum([1 for i in range(col_id) if image[row_id, i] and (i==0 or not image[row_id, i-1])])
    if dir_num == 0 or dir_num % 2 == 0:
        return False
    dir_num = sum([1 for i in range(row_id) if image[i, col_id] and (i==0 or not image[i-1, col_id])])
    if dir_num == 0 or dir_num % 2 == 0:
        return False
    return True

# def is_point_surrounded(image, point):
#     image = np.array(image)
#     col_id, row_id = point
#     print('ksfj: ', point)
#     print(col_id == 0 or image[row_id][col_id-1])
#     print(col_id == image.shape[1]-1 or image[row_id][col_id+1])
#     print(row_id == 0 or image[row_id-1][col_id])
#     print(row_id == image.shape[0]-1 or image[row_id+1][col_id])
#     if  (col_id == 0 or image[row_id][col_id-1]) \
#         and (col_id == image.shape[1]-1 or image[row_id][col_id+1]) \
#         and (row_id == 0 or image[row_id-1][col_id]) \
#         and (row_id == image.shape[0]-1 or image[row_id+1][col_id]):
#         return True
#     else:
#         return False

def draw_with_mask(image, mask, color):
    image = np.array(image, dtype=np.uint8)
    mask = np.array(mask, dtype=np.uint8)
    for row_id, row in enumerate(mask):
        for col_id, element in enumerate(row):
            if not element:
                continue
            if color[-1] == 255:
                image[row_id, col_id] = color
            else:
                color_sum = float(color[3]) + 255.
                image[row_id, col_id, :3] = (image[row_id, col_id, :3].astype(np.float)*255./color_sum + [float(i)*float(color[3])/color_sum for i in color[:3]]).astype(np.uint8)
                image[row_id, col_id, 3] = 255
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
    # if asset['name'].find('474') < 0:
    #     return
    
    raw_img_path = '/'.join(input_path.split('/')[:-1]) + '/' + asset['name']

    labeled_image = standard_labeled_tensor(asset['size']['height'], asset['size']['width'], len(tags)+1)
    labeled_image_vis = standard_alpha_image(asset['size']['height'], asset['size']['width'])
    labeled_image_vis_with_raw = Image.open(raw_img_path).convert('RGBA')
    labeled_image_vis_with_raw.save(f"{output_path}raw/{asset['name']}.png")

    for tag in tags:
        for region in regions:
            if not region['tags'][0] == tag['name']:
                continue

            # For debug
            # if not region['tags'][0] == 'Field':
            #     continue

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
            flood_region_raw = flood_region.copy()
            # For debug
            # draw.line((curr_point['x'], curr_point['y'], inner_point[0], inner_point[1]), fill=1)
            # ImageDraw.floodfill(flood_region, xy=inner_point, value=1)

            while inner_point:
                # For debug
                # if is_point_surrounded(flood_region, inner_point):
                #     flood_region[inner_point[1], inner_point[0]] = 1
                # else:
                #     ImageDraw.floodfill(flood_region, xy=inner_point, value=1)
                # flood_region = np.array(flood_region)
                # flood_region[454, 1279:1500] = 1

                ImageDraw.floodfill(flood_region, xy=inner_point, value=1)
                inner_point = find_inner_point(flood_region, flood_region_raw)

                # For debug
                # flood_region = np.array(flood_region)
                # flood_region[inner_point[1], inner_point[0]:inner_point[0]+50] = 1
                # break
            
            region_color = ImageColor.getrgb(tags_color[region['tags'][0]])
            
            labeled_image_vis = draw_with_mask(labeled_image_vis, flood_region, (region_color[0],region_color[1],region_color[2],255))
            labeled_image_vis = Image.fromarray(labeled_image_vis, 'RGBA')
            labeled_image_vis_with_raw = draw_with_mask(labeled_image_vis_with_raw, flood_region, (region_color[0],region_color[1],region_color[2],150))
            labeled_image_vis_with_raw = Image.fromarray(labeled_image_vis_with_raw, 'RGBA')
    
    labeled_image_vis.save(f"{output_path}vis/{asset['name']}.png")
    labeled_image_vis_with_raw.convert('RGB').save(f"{output_path}vis_with_raw/{asset['name']}.jpg")
   
    labeled_image_temp = standard_labeled_tensor(asset['size']['height'], asset['size']['width'], len(tags)+1)
    for i in range(labeled_image.shape[-1]):
        labeled_image_temp[:,:,i] = np.array(Image.fromarray(labeled_image[:,:,i]*255,'L').resize((asset['size']['width'], asset['size']['height'])), dtype=np.uint8)/255
    labeled_image = labeled_image_temp
        
    # with open(f"{output_path}tensors/{asset['name']}.pickle", 'wb') as pickle_file:
    #     pickle.dump(labeled_image, pickle_file)
import argparse
import re
import os
import cv2
import json
import pandas as pd

def extract_info(result):
    pattern_ = ': |\\t\(left_x: +| +top_y: +| +width: +| +height: +|\)'
    total_dict = {}
    for image_result in result.split('Enter Image Path: ')[2:]:
        if image_result == '':
            continue
        result_dict = {}
        image_result = image_result.split('\n')

        path_sec = image_result[0].split(': ')
        image_path = path_sec[0]
        result_dict['sec'] = path_sec[1].split(' ')[2] + ' ' + path_sec[1].split(' ')[3]

        result_info = pd.DataFrame([re.split(pattern_, object_) for object_ in image_result[1:-1]])
        result_info = result_info.drop(6,axis=1)
        result_info.columns = ['predict','precent','left_x','top_y','width','height']
        result_dict['image_result'] = result_info

        total_dict[image_path] = result_dict
    return total_dict

def convertBack(x, y, w, h):
    xmin = int(x)
    xmax = int(x + w)
    ymin = int(y)
    ymax = int(y + h)
    return xmin, ymin, xmax, ymax

def cvDrawBoxes(result_info, img):
    for num, detection in result_info['image_result'].iterrows():
        x, y, w, h = detection[['left_x', 'top_y','width','height']]
        xmin, ymin, xmax, ymax = convertBack(float(x), float(y), float(w), float(h))
        pt1 = (xmin, ymin)
        pt2 = (xmax, ymax)
        cv2.rectangle(img, pt1, pt2, (0, 255, 0), 1)
        cv2.putText(img,
                    detection['predict'] +
                    " [" + detection['precent'] + "]",
                    (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    [0, 255, 0], 2)
    return img


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input_txt', 
                        type=str , 
                        required=True,
                        help = '입력 darknet v4 result txt')
    parser.add_argument('-o','--output_dir',
                        type=str , 
                        required=True,
                        help = '결과 jpg,csv,json 저장 경로')
    args = parser.parse_args()

    output_dir = args.output_dir
    with open(args.input_txt,'r') as f:
        result = f.read()

    # txt 파일에서 데이터 정제
    total_dict = extract_info(result)
    for image_path, result_info in total_dict.items():
        # jpg 이미지 생성
        img = cv2.imread(image_path)
        img = cvDrawBoxes(result_info,img)
        cv2.imwrite(os.path.join(output_dir, os.path.basename(image_path)),img)
        
        # json 생성
        json_data = result_info['image_result']['predict'].value_counts().to_dict()
        json_data['sec'] = result_info['sec']
        json_path = os.path.join(\
                output_dir, \
                os.path.basename(image_path).split('.')[0] + '.json')
        with open(json_path, "w") as json_file:
            json.dump(json_data, json_file)

        # csv 파일 생성
        csv_path = os.path.join(\
                output_dir, \
                os.path.basename(image_path).split('.')[0] + '.csv')
        result_info['image_result'][['predict',	'precent']].to_csv(csv_path)

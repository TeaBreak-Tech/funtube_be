#import util_preparation as up
import pandas as pd
import random
import os
import csv

from .models import *

PREVENT_DURATION = 60
START_PREVENT_DURATION = 60
END_PREVENT_DURATION = 60


def generagte_random_ads(video_id,):
    
    N_ADS = 3

    # 确定插入的广告
    # 可用广告在 ad_urls.csv 里查询
    ads = []
    ads = [[ad.ad_id, ad.link] for ad in Ad.objects.all()]
    # reader = csv.reader(open(r"/home/www/res/ad/ad_urls.csv", "r",encoding="utf8"))
    # for item in reader:
    #     ad_id = int(item[0])
    #     ad_url = item[1]
    #     ads.append([ad_id, ad_url])
    # 随机取 N_ADS 个
    ads = random.sample(ads, N_ADS)

    # 确定插入时间
    # 遍历全部_shot.csv，找到当前视频的对应 _shot.csv
    available_times = []
    for path,dir_list,file_list in os.walk(r"/home/www/res/video_shot_csv"):
        for file_name in file_list:
            id = int(file_name.split("/")[-1].split("_")[0].replace("video",""))
            if(video_id==id):
                # 读取 _shot.csv, 获取全部镜头信息
                reader = csv.reader(open(r"/home/www/res/video_shot_csv/"+file_name, "r",encoding="utf8"))
                v_length = pd.read_csv(r"/home/www/res/video_shot_csv/"+file_name).iloc[-1]["end_time"]
                # 遍历每个镜头
                for item in reader:
                    # print(item[3])
                    if reader.line_num == 1: continue
                    START_TIME_COL = 2
                    END_TIME_COL = 3

                    start_time = float(item[START_TIME_COL])
                    end_time = float(item[END_TIME_COL])

                    # 每一个镜头的结束时间可以作为候选时间点
                    # 离开头和结尾过近(END_PREVENT_DURATION)的时间点自动剔除

                    

                    if end_time > START_PREVENT_DURATION and end_time < v_length - END_PREVENT_DURATION:
                        available_times.append(end_time)

    #print(available_times)

    def randomize_time():  
        ad_times = random.sample(available_times, N_ADS)
        ad_times.sort()
        for i in range(0,N_ADS):
            if (i-1)>0:
                if abs(ad_times[i] - ad_times[i-1]) < PREVENT_DURATION:
                    ad_times = randomize_time()
                    break
            if (i+1)<len(ad_times):
                if abs(ad_times[i] - ad_times[i+1]) < PREVENT_DURATION:
                    ad_times = randomize_time()
                    break
        return ad_times

    if len(available_times) > N_ADS:
        ad_times = randomize_time()
        #print(ad_times)
    else:
        #print("ERROR: len(available_times) <= N_ADS")
        return []

    # print(ad_times)

    result = []
    for i in range(0, N_ADS):
        result.append({
            "ad_id":ads[i][0],
            "time":ad_times[i],
            "url":ads[i][1],
        })
    #print(result)
    return result

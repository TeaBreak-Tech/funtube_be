from django.db.models.query import QuerySet
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from secrets import token_urlsafe
from django.views.decorators.http import require_http_methods
from .models import *
from django.forms.models import model_to_dict
from django.utils import timezone
from .Random_positions import generagte_random_ads
import pandas as pd

import datetime
import random
import uuid
import time
import json

TOKEN_LENGTH = 50

def setConfig(visitor, config_dic:dict):
    try:
        new_config_dic = json.loads(visitor.config)
    except:
        visitor.config = "{"+"}"
        visitor.save()
        new_config_dic = {}
    for key in config_dic.keys():
        new_config_dic[key] = config_dic[key]
    visitor.config = json.dumps(new_config_dic)
    visitor.save()

def getConfig(visitor,key):
    try:
        return json.loads(visitor.config).get(key,None)
    except:
        return None

def index(request):
    return HttpResponse("Hello, world. You're at the api index.")


def getViewNum(visitor,video_id):
    n_view_dic = getConfig(visitor,"n_view_dic")
    changed = False
    if not n_view_dic:
        n_view_dic = {}
        changed = True
    if not n_view_dic.get(str(video_id)):
        n_view_dic[str(video_id)] = random.randint(0,100)
        changed = True
    if changed:
        setConfig(visitor,{"n_view_dic":n_view_dic})
    return n_view_dic[str(video_id)]

def getPubDate(visitor,video_id):
    pub_date_dic = getConfig(visitor,"pub_date_dic")
    changed = False
    if not pub_date_dic:
        pub_date_dic = {}
        changed = True
    if not pub_date_dic.get(str(video_id)):
        a1=(2021,1,1,0,0,0,0,0,0)
        a2=(2021,6,23,0,0,0,0,0,0)
        start=time.mktime(a1)    #生成开始时间戳
        end=time.mktime(a2)      #生成结束时间戳  
        t=random.randint(start,end)    #在开始和结束时间戳中随机取出一个
        date_touple=time.localtime(t)          #将时间戳生成时间元组
        date_str=time.strftime("%Y-%m-%d",date_touple)  #将时间元组转成格式化字符串（1976-05-21）
        print(date_str)
        pub_date_dic[str(video_id)] = date_str
        changed = True
    if changed:
        setConfig(visitor,{"pub_date_dic":pub_date_dic})
    return pub_date_dic.get(str(video_id))


# 自动化加载和处理视频数据
def load_video_list(request):
    # 本函数仅在修改实验设置时使用，用于完全重置数据库视频设置
    import os
    import csv
    #import cv2
    video_url_list = []
    for path,dir_list,file_list in os.walk(r"/home/www/res/video"):
        #print (file_list)
        for file_name in file_list: 
            #print(os.path.join(path, file_name) )
            id = int(file_name.split("/")[-1].split("_")[0].replace("video",""))
            #print(id)
            video_url_list.append({"id":id,"url":"/video/"+file_name})
    
    # 读取video.csv,根据ID读取视频
    reader = csv.reader(open(r"/home/www/res/video.csv", "r",encoding="utf8"))
    id_col = 0
    title_col = 1
    cat_col = 2
    tag_col = 3
    video_info_list = []
    #ad_col = 3
    for item in reader:
        if reader.line_num == 1:
            #print(item)
            id_col = item.index("id")
            title_col = item.index("title")
            cat_col = item.index("categories")
            tag_col = item.index("tags")
            #ad_col = item.index("ad1")
            continue
        try:
            id = int(item[id_col])
        except: continue
        video_info_list.append({
            "id":id,
            "title":item[title_col],
            "cat":item[cat_col].split(" "),
            "tag":item[tag_col].split(" "),
        })

    ad_config_list = []
    # 读取 config.csv 为每个视频添加几种广告配置
    reader2 = csv.reader(open(r"/home/www/res/config.csv", "r",encoding="utf8"))
    video_id_col = 0
    config_num_col = 1
    config_col = 2
    for item in reader2:
        item = [ entry.replace(" ","").replace("\t","") for entry in item ]
        if reader2.line_num == 1:
            try:video_id_col = item.index("video_id")
            except: pass
            config_num_col = item.index("config_num")
            config_col = item.index("config")
            continue
        try:
            video_id = int(item[video_id_col])
        except: continue
        ad_config_list.append({
            "video_id":video_id,
            "config_num":item[config_num_col],
            "config":item[config_col].replace("\'","\""),
        })

    # 将视频数据逐个在config中查询，最后取视频文件和视频信息都存在的视频作为最终结果（交集）
    # 已经存在的视频信息将会被保留或更改
    for video_url in video_url_list:
        id = video_url["id"]
        for video_info in video_info_list:
            if video_info["id"] == id:
                try: video = Video.objects.get(id=id)
                except: 
                    video = Video()
                    video.video_id = video_info["id"]
                video.title = video_info["title"]
                video.url = video_url["url"]
                video.cover_url = "/poster/poster_"+str(id)+".jpg"
                video.save()
                
                for cat_title in video_info["cat"]:
                    try: cat = Cat.objects.get(cat_title=cat_title)
                    except:
                        cat = Cat()
                        cat.cat_title = cat_title
                        cat.save()
                    video_cat = Video_cat()
                    video_cat.video = video
                    video_cat.cat = cat
                    video_cat.save()
                
                for tag_title in video_info["tag"]:
                    try: tag = Tag.objects.get(tag_title=tag_title)
                    except:
                        tag = Tag()
                        tag.tag_title = tag_title
                        tag.save()
                    video_tag = Video_tag()
                    video_tag.video = video
                    video_tag.tag = tag
                    video_tag.save()

                for ad_config_info in ad_config_list:
                    if id==ad_config_info["video_id"]:
                        try: ad_config = AdConfig.objects.get(video = video,config_num = ad_config_info["config_num"])
                        except: ad_config = AdConfig()
                        ad_config.video = video
                        ad_config.config_num = ad_config_info["config_num"]
                        ad_config.config = ad_config_info["config"]
                        ad_config.save()
                print("added video, id =", id,"title =", video.title)
    
    # 加载全部广告文件
    ads = {}
    for path,dir_list,file_list in os.walk(r"/home/www/res/ad"):
        #print (file_list)
        for file_name in file_list: 
            #print(os.path.join(path, file_name) )
            if file_name.split(".")[1] in ['csv', 'json']: continue
            id = int(file_name.split(".")[0].replace("ad_",""))
            ads[id] = "/ad/"+file_name



    # 从广告配置文件中读取相关广告信息, 填充进广告数据中
    # 仅文件和信息都存在的广告才会被加载进去
    # 已经存在的广告信息将会被保留或更改
    reader3 = csv.reader(open(r"/home/www/res/ad/ad_info.csv", "r",encoding="utf8"))
    for item in reader3:
        id = int(item[0])
        if ads.get(id):
            try:
                ad = Ad.objects.get(ad_id=id)
            except:
                ad = Ad()
                ad.ad_id = item[0]
            ad.src = ads.get(id) 
            ad.href = item[1]
            ad.brand = item[2]
            ad.product = item[3]
            ad.cb = item[4]
            ad.db = item[5]
            ad.cb_name = item[8]
            ad.db_name = item[10]
            ad.cp_name = item[9]
            ad.dp_name = item[11]
            ad.save()

    # 给所有数据库视频抽取封面图
    # for video in Video.objects.all():
    #     video_path = "/home/www/res/video/" + video.url.split("/")[-1]

    # 读取全部镜头信息
    for path,dir_list,file_list in os.walk(r"/home/www/res/video_shot_csv"):
        for file_name in file_list:
            id = int(file_name.split("/")[-1].split("_")[0].replace("video",""))
            video = Video.objects.get(video_id = id)
            # 读取 _shot.csv, 获取全部镜头信息
            reader = csv.reader(open(r"/home/www/res/video_shot_csv/"+file_name, "r",encoding="utf8"))
            v_length = pd.read_csv(r"/home/www/res/video_shot_csv/"+file_name).iloc[-1]["end_time"]

            for item in reader:
                # print(item[3])
                if reader.line_num == 1: continue
                START_TIME_COL = 2
                END_TIME_COL = 3

                end_time = float(item[END_TIME_COL])
                shot = Shot(video=video, end_time = end_time)
                shot.save()
            
            video.length = v_length
            video.save()



    return JsonResponse({"status":"success"})

@require_http_methods(["POST"])
def new_session(request):
    token = request.COOKIES.get("token")
    visitor_id = request.COOKIES.get("visitor_id")
    body_dict = json.loads(request.body.decode('utf-8'))
    pid = body_dict.get("pid")
    player_type = body_dict.get("player_type")
    client = body_dict.get("client",0)
    video_id = body_dict.get("video_id") # 在问卷访问情况下会忽略 vide_id, 在其余情况下必须提供有效id
    is_new_visitor = True
    try:
        if pid: 
            # 如果pid查找到了该用户
            visitor = Visitor.objects.get(pid=pid)
        else:
            # 在没有pid的系统中,用 visitor_id 找到了对应用户：
            visitor = Visitor.objects.get(pk=visitor_id)
        # 如果两种方式都没有获取到用户，进入exception，以下代码不会被执行
        is_new_visitor = False
        
    except:
        # 如果有pid但没有对应用户，或者没有pid并且visitor_id也不对应用户，那么创建用户
        token = token_urlsafe(TOKEN_LENGTH)
        # 无论新用户来自哪个来源,都要给该用户分配一个问卷专用的视频
        #video_list = Video.objects.filter(client=0)
        video = Video.objects.get(pk=1)
        visitor = Visitor()
        #visitor.visitor_id = visitor_id
        # 无论新用户来自哪个来源,都要给该用户分配一个广告配置版本 1/2/3/4
        visitor.save()
        #visitor.config_num = visitor.visitor_id%4 + 1
        visitor.token = token
        #visitor.video = video
        visitor.pid = pid
        visitor.save()
        # 全部广告放入备选
        for ad in Ad.objects.all():
            if ad.ad_id != 1:
                visitor.ads_candidate.add(ad)
        visitor.save()
        # 随机分配一个初始广告
        ad_to_show = random.sample(list(visitor.ads_candidate.all()),1)[0]
        visitor.ad_to_show = ad_to_show
        visitor.ads_candidate.remove(ad_to_show)
        visitor.save()
        
    # 现在确保有了 visitor 对象
    if client==1:
        # 如果用户来自于问卷
        try:
            # 如果请求中指定了一个有效video,则使用这个video，并且更新用户的video分配状况
            video = Video.objects.get(pk=video_id)
            visitor.video = video
            visitor.save()
        except:
            try:
                video = Video.objects.filter(client=1).order_by('url')[int(video_id)]
                visitor.video = video
                visitor.save()
            except:
                # 如果未指定视频，获取该用户的默认视频
                video = visitor.video
    else:
        #print("request for video",video_id)
        # 如果用户来自于主站,则请求中要求包含有效的 video_id 参数
        try: video = Video.objects.get(pk=video_id)
        except: 
            try: video = Video.objects.get(pk=int(video_id))
            except:
                # 如果不包含，则视为净注册一个用户而不开始session
                response = JsonResponse({
                    "is_new_visitor":is_new_visitor,
                    "visitor_id":visitor.visitor_id,
                    "create_time":visitor.created_time,
                    #"config_num":visitor.config_num,
                })
                response.set_cookie("token", visitor.token)
                response.set_cookie("visitor_id", visitor.visitor_id)
                return response
    # 现在确保有了 visitor 对象和 video 对象
    session = Session()
    #session_id = uuid.uuid4()
    #session.session_id = session_id
    session.visitor = visitor
    session.video = video # 给当前 session 赋予同样的 video
    session.pid = pid
    session.player_type = player_type
    session.save()
    #print(video,visitor.config_num)
    
    # 生成广告方案

    # 方案1，配置文件预先存入数据表，每个【视频+方案号】对应一个方案详情，一个访客拥有一个方案号
    # ads = AdConfig.objects.get(video=video,config_num=visitor.config_num).config

    # 方案2，是使用随机插入算法返回一个列表。这个列表存入与用户一一对应的专属 Config 中
    # 此方案中，Config model 已被废除
    # ads = []
    # # 先在用户 config 中查找当前视频是否有广告方案记录
    # all_ad_config = getConfig(visitor,"ad_config")
    # if all_ad_config:
    #     curr_ad_config = all_ad_config.get(str(video.video_id), [])
    # else:
    #     curr_ad_config = []
    #     all_ad_config = {}
    # if curr_ad_config and len(curr_ad_config) > 0:
    #     # 如果有
    #     ads = curr_ad_config
    #     print(all_ad_config.keys())
    # else:
    #     # 如果对应的视频没有记录，则随机生成广告方案，并存入用户设置
    #     ads = generagte_random_ads(video.video_id)
    #     all_ad_config[video.video_id] = ads
    #     print(all_ad_config)
    #     setConfig(visitor,{"ad_config":all_ad_config})

    # 方案3 每个视频里只插播一个广告，位点固定，具体是哪个广告留给其他接口决定
    ads = []
    # 先在用户 config 中查找当前视频是否有广告方案记录
    all_ad_config = getConfig(visitor,"ad_config")
    if all_ad_config:
        curr_ad_config = all_ad_config.get(str(video.video_id), [])
    else:
        curr_ad_config = []
        all_ad_config = {}
    if curr_ad_config and len(curr_ad_config) > 0:
        # 如果有
        ads = curr_ad_config
        print(all_ad_config.keys())
    else:
        # 如果对应的视频没有记录，则随机生成广告方案，并存入用户设置
        ads = generagte_random_ads(video.video_id,1)
        ads[0]["ad_id"] = "auto"; ads[0]["src"] = "auto"
        all_ad_config[video.video_id] = ads
        print(all_ad_config)
        setConfig(visitor,{"ad_config":all_ad_config})

    session.ad_config = ads
    session.save()
    # for ad_info in ads:
    #     ad = Ad.objects.get(ad_id=ad_info["ad_id"])
    #     ad_info.update(url = ad.href)
    response = JsonResponse({
        "is_new_visitor":is_new_visitor,
        "visitor_id":visitor.visitor_id,
        "session_id":session.session_id,
        "create_time":visitor.created_time,
        "videos":[{
            "video_id": video.video_id,
            "title": video.title,
            "url": video.url,
            "cover_url": video.cover_url,
            #"svi_raw": [float(i) for i in video.svi_raw.split(' ')],
            "created_time": getPubDate(visitor,video.video_id),
            "description":video.description,
            "ads":ads,
        } for video in [video] ],
        "views":getViewNum(visitor,video.video_id)
    })
    response.set_cookie("token", visitor.token)
    response.set_cookie("visitor_id", visitor.visitor_id)
    return response

def logout(request):
    response = HttpResponse("video add success")
    response.set_cookie("token", None)
    response.set_cookie("visitor_id", None)
    return response

@require_http_methods(["POST"])
def add_video(request):
    video = Video()
    body_dict = json.loads(request.body.decode('utf-8'))
    video.video_id = uuid.uuid4()
    video.title = body_dict.get("title")
    video.url = body_dict.get("url")
    video.cover_url = body_dict.get("cover_url")
    video.svi_raw = ' '.join([ str(i) for i in body_dict.get("svi_raw")])
    # auto created_time
    video.created_time = datetime.datetime.now()
    video.description=body_dict.get("description","该视频没有描述")
    video.client = body_dict.get("client",0)
    video.save()
    return HttpResponse("video add success")

@require_http_methods(["POST"])
def new_event(request):
    body_dict = json.loads(request.body.decode('utf-8'))
    pid = body_dict.get("pid")
    if pid:
        try: visitor = Visitor.objects.get(pid=pid)
        except: return HttpResponse("visitor DNE",status=401)
    else:
        token = request.COOKIES.get("token")
        visitor_id = request.COOKIES.get("visitor_id")
        try: visitor:Visitor = Visitor.objects.get(pk=visitor_id)
        except: return HttpResponse("visitor DNE",status=401)
    event = Event()
    #event_id = uuid.uuid4()
    #event.event_id = event_id
    session_id = body_dict.get("session_id")
    video_info = body_dict.get("video_info")
    buffered = body_dict.get("buffered",0)
    try: buffered = int(buffered)
    except: buffered = 0
    #print(session_id)
    try: session:Session = Session.objects.get(pk=session_id)
    except: return HttpResponse("session DNE",status=402)
    event.session = session
    event.video_info = video_info
    event.label = body_dict.get("label")
    event.description = body_dict.get("description")
    raw_timestamp = body_dict.get("timestamp")
    #print ("\n\n",video_info,"\n\n")
    timestamp = timezone.now()#timezone.fromtimestamp(float(raw_timestamp/1000))
    event.timestamp = timestamp
    event.video_time = float(body_dict.get("video_time"))
    event.volume = float(body_dict.get("volume"))
    event.buffered = buffered
    event.playback_rate = float(body_dict.get("playback_rate"))
    event.full_page = bool(body_dict.get("full_page"))
    event.full_screen = bool(body_dict.get("full_screen"))
    event.player_height = int(body_dict.get("player_height"))
    event.player_width = int(body_dict.get("player_width"))
    event.save()

    if video_info.split('_')[0]=='ad':
        ad_id = int( video_info.split('_')[1] )
        ad:Ad = Ad.objects.get(ad_id = ad_id)
        # 如果是新的ad,那么增加观看记录，更新用户的 ad_to_show
        #if not ad in list(visitor.ads.all()):
        # print("new add visited")
        visitor.ads.add(ad)
        session.ads.add(ad)
        if visitor.ads_candidate.count() > 0:
            ad_to_show = random.sample(list(visitor.ads_candidate.all()),1)[0]
            visitor.ad_to_show = ad_to_show
            visitor.save()
            # 只有第一次看到广告才排除这个广告及其竞争者
            if visitor.ads_candidate.count() > (Ad.objects.count()-3):
                print("Removing first ad and its cpmpetitor")
                visitor.ads_candidate.remove(ad_to_show)
                # 移除竞争者
                print(ad.cb)
                comp = Ad.objects.get(ad_id=ad.cb.split('_')[1])
                visitor.ads_candidate.remove(comp)
                visitor.save()
                print(visitor.ads_candidate.all())
            # else do nothing
        # Never have "else". "Count>0" is just for insurance.
        # else:
        #     print("playing existing add")

    return HttpResponse("event saved")

@require_http_methods(["GET","POST"])
def get_video_list(request):
    # 获取当前访客身份 visitor:Visitor
    body_dict = json.loads(request.body.decode('utf-8'))
    pid = body_dict.get("pid")
    if pid:
        try: visitor = Visitor.objects.get(pid=pid)
        except: return HttpResponse("visitor DNE",status=401)
    else:
        token = request.COOKIES.get("token")
        visitor_id = request.COOKIES.get("visitor_id")
        try: visitor = Visitor.objects.get(pk=visitor_id)
        except: return HttpResponse("visitor DNE",status=401)
    # 获取视频列表
    video_list_ids = getConfig(visitor,"video_list")
    if(video_list_ids):
        video_list = [ Video.objects.get(video_id=vid) for vid in video_list_ids ]
    else:
        video_list = list(Video.objects.all())
        random.shuffle(video_list)
        video_list_ids = [ video.video_id for video in video_list ]
        setConfig(visitor,{"video_list":video_list_ids})

    return JsonResponse({
        "result":[{
            "video_id": video.video_id,
            "title": video.title,
            "url": video.url,
            "cover_url": video.cover_url,
            #"svi_raw": [float(i) for i in video.svi_raw.split(' ')],
            "created_time": getPubDate(visitor,video.video_id),
            "description":video.description,
            "views":getViewNum(visitor,video.video_id),
        } for video in video_list ]
    })

@require_http_methods(["GET"])
def get_video_by_tag(request,cat_id):
    # 获取当前访客身份 visitor:Visitor
    pid = request.GET.get("pid")
    if pid:
        try: visitor = Visitor.objects.get(pid=pid)
        except: return HttpResponse("visitor DNE",status=401)
    else:
        token = request.COOKIES.get("token")
        visitor_id = request.COOKIES.get("visitor_id")
        try: visitor = Visitor.objects.get(pk=visitor_id)
        except: return HttpResponse("visitor DNE",status=401)
    # 获取视频列表
    try:cat_id = int(cat_id)
    except: cat_id = 0
    if cat_id!=0:
        cat = Cat.objects.get(cat_id=cat_id)
        video_lists_by_cat = getConfig(visitor,"video_lists_by_cat")
        if video_lists_by_cat:
            cat_video_list_ids = video_lists_by_cat.get(cat.cat_title)
        else:
            video_lists_by_cat = {}
            cat_video_list_ids = None

        if cat_video_list_ids:
            cat_video_list = [ Video.objects.get(video_id=vid) for vid in cat_video_list_ids ]
        else:
            cat_video_list = [ video_cat.video for video_cat in Video_cat.objects.filter(cat_id=cat_id) ]
            random.shuffle(cat_video_list)
            cat_video_list_ids = [ video.video_id for video in cat_video_list ]
            video_lists_by_cat[cat.cat_title] = cat_video_list_ids
            setConfig(visitor,{"video_lists_by_cat":video_lists_by_cat})

        

        return JsonResponse({
            "title":cat.cat_title,
            "videos":[{
                "video_id": video.video_id,
                "title": video.title,
                "url": video.url,
                "cover_url": video.cover_url,
                #"svi_raw": [float(i) for i in video_cat.video.svi_raw.split(' ')],
                "created_time": getPubDate(visitor,video.video_id),
                "description": video.description,
                "views":getViewNum(visitor,video.video_id),
            }for video in cat_video_list ]
        })
    else:
        video_list_ids = getConfig(visitor,"video_list")
        if(video_list_ids):
            video_list = [ Video.objects.get(pk=vid) for vid in video_list_ids ]
        else:
            video_list = list(Video.objects.all())
            random.shuffle(video_list)
            video_list_ids = [ video.video_id for video in video_list ]
            setConfig(visitor,{"video_list":video_list_ids})
        return JsonResponse({
            "title":"全部视频",
            "videos":[{
                "video_id": video.video_id,
                "title": video.title,
                "url": video.url,
                "cover_url": video.cover_url,
                #"svi_raw": [float(i) for i in video_cat.video.svi_raw.split(' ')],
                "created_time": getPubDate(visitor,video.video_id),
                "description": video.description,
                "views":getViewNum(visitor,video.video_id),
            }for video in video_list ]
        })


@require_http_methods(["POST"])
def add_video_tag(request):
    body_dict = json.loads(request.body.decode('utf-8'))
    tag_title = body_dict.get("tag_title")
    video_id = body_dict.get("video_id")
    if(tag_title and video_id):
        try: tag = Tag.objects.get(tag_title=tag_title)
        except:
            tag = Tag()
            tag.tag_title = tag_title
            tag.tag_id = uuid.uuid4()
            tag.save()
        try: video = Video.objects.get(pk=video_id)
        except: return HttpResponse(status=404)
        video_tag = Video_tag()
        video_tag.video_tag_id = uuid.uuid4()
        video_tag.tag = tag
        video_tag.video = video
        video_tag.save()
    return HttpResponse("Save successfully")

def getSuggestion(request):
    video_id = request.GET.get("vid",None)
    # video_list = list(Video.objects.all())
    # for video in video_list:
    #     if str(video.video_id) == video_id:
    #         video_list.remove(video)

    #video_list = random.sample(video_list,4)

    # 获取当前访客身份 visitor:Visitor
    pid = request.GET.get("pid")
    if pid:
        try: visitor = Visitor.objects.get(pid=pid)
        except: return HttpResponse("visitor DNE",status=401)
    else:
        token = request.COOKIES.get("token")
        visitor_id = request.COOKIES.get("visitor_id")
        try: visitor = Visitor.objects.get(pk=visitor_id)
        except: return HttpResponse("visitor DNE",status=401)

    video_list_ids = getConfig(visitor,"video_list")
    if(video_list_ids):
        video_list = [ Video.objects.get(pk=vid) for vid in video_list_ids ]
    else:
        video_list = list(Video.objects.all())
        random.shuffle(video_list)
        video_list_ids = [ video.video_id for video in video_list ]
        setConfig(visitor,{"video_list":video_list_ids})
    for video in video_list:
        if str(video.video_id) == video_id:
            video_list.remove(video)
    result = [{
        "video_id": video.video_id,
        "title": video.title,
        "url": video.url,
        "cover_url": video.cover_url,
        #"svi_raw": [float(i) for i in video_cat.video.svi_raw.split(' ')],
        "created_time": getPubDate(visitor,video.video_id),
        "description": video.description,
        "views":getViewNum(visitor,video.video_id),
    }for video in video_list ]

    return JsonResponse({
        "result":result
    })

def getCategories(request):
    cat_list = Cat.objects.all()
    result = [{
        "cat_id":cat.cat_id,
        "cat_title":cat.cat_title,
    } for cat in cat_list]
    
    return JsonResponse({
        "result":result,
    })

def getHistory(request):
    pid = request.GET.get('pid')
    try:
        visitor = Visitor.objects.get(pid=pid)
    except:
        return JsonResponse({"result":[]})
    sessions = Session.objects.filter(visitor=visitor)
    viewed_ids = [ session.video.video_id for session in sessions]

    result = [{
        "video_id": video.video_id,
        "title":video.title,
        "viewed": 1 if (video.video_id in viewed_ids) else 0,
    } for video in Video.objects.all()]

    response = JsonResponse({"result":result})

    response["Access-Control-Allow-Origin"] = "*"

    return response

def getViewedAds(request):
    pid = request.GET.get('pid')
    try:
        visitor = Visitor.objects.get(pid=pid)
        ads = visitor.ads.all()
    except:
        ads=[]

    if len(list(ads))<= 0:
        ads = [Ad.objects.get(pk=1)]
        
    result = [{
        "ad_id":ad.ad_id,
        "brand": ad.brand,
        "product": ad.product,
        "cp": ad.cp_name,
        "dp":ad.dp_name,
        "cb": ad.cb_name,
        "db":ad.db_name,
        "cb_src": ad.cb,
        "db_src":ad.db,
    } for ad in ads]

    response = JsonResponse({"result":result})

    response["Access-Control-Allow-Origin"] = "*"

    return response

def getAdPlan(request):

    token = request.COOKIES.get("token")
    visitor_id = request.COOKIES.get("visitor_id")
    try: visitor:Visitor = Visitor.objects.get(pk=visitor_id)
    except: return HttpResponse("visitor DNE",status=401)

    ad_to_show:Ad = visitor.ad_to_show
    if not ad_to_show:
        ad_to_show = random.sample(list(Ad.objects.all()),1)[0]
        visitor.ad_to_show = ad_to_show
        visitor.save()
    print({
        "ad_id": ad_to_show.ad_id,
        "src": ad_to_show.src,
        "href": ad_to_show.href,
    })
    return JsonResponse({
        "ad_id": ad_to_show.ad_id,
        "src": ad_to_show.src,
        "href": ad_to_show.href,
    })

def listAllVisitors(request):
    filter = request.GET.get("filter")
    result:QuerySet = Visitor.objects.all()
    if filter == "has_pid":
        result:QuerySet = result.filter(pid__isnull=False)
    return JsonResponse({"result":[
        {
            "visitor_id": visitor.visitor_id,
            "pid": visitor.pid,
            "created_time": visitor.created_time,
        }
    for visitor in result]})

def showVisitorInfo(request, pid):
    try:
        visitor = Visitor.objects.get(pid=pid)
    except:
        return JsonResponse({"error":"Visitor with requested PID not found."})
    else:
        
        config = json.loads(visitor.config)
        ad_config = config.get("ad_config")
        for key in ad_config.keys():
            ads = ad_config[key]
            ads = [{"time":ad["time"]} for ad in ads]
            ad_config[key] = ads
        config["ad_config"] = ad_config

        return JsonResponse({
            "visitor_id": visitor.visitor_id,
            "pid": visitor.pid,
            "created_time": visitor.created_time,
            "config": config,
            # "viewed_ads":[
            #     {
            #         "ad_id":ad.ad_id,
            #         "brand": ad.brand,
            #         "product": ad.product,
            #         "cp": ad.cp_name,
            #         "dp":ad.dp_name,
            #         "cb": ad.cb_name,
            #         "db":ad.db_name,
            #         "cb_src": ad.cb,
            #         "db_src":ad.db,
            #     }
            # for ad in visitor.ads.all()],
            "sessions":[
                {
                    "session_id": session.session_id,
                    "video": {
                        "video_id": session.video.video_id,
                        "title": session.video.title,
                        "created_time": getPubDate(visitor,session.video.video_id),
                    },
                    # "ad_config": json.loads(session.ad_config.replace('\'','\"')),
                    "ads":[{
                        "ad_id":ad.ad_id,
                        "brand": ad.brand,
                        "product": ad.product,
                        "cp": ad.cp_name,
                        "dp":ad.dp_name,
                        "cb": ad.cb_name,
                        "db":ad.db_name,
                        "cb_src": ad.cb,
                        "db_src":ad.db,
                    } for ad in session.ads.all()],
                    "start_time":session.start_time,
                    # "events": [
                    #     {
                    #         "event_id":event.event_id,
                    #         "video_info":event.video_info,
                    #         "description":event.description,
                    #         "timestamp":event.timestamp,
                    #         "video_time":event.video_time,
                    #         "volume":event.volume,
                    #         "buffered":event.buffered,
                    #         "playback_rate":event.playback_rate,
                    #         "full_page":event.full_page,
                    #         "full_screen":event.full_screen,
                    #         "player_height":event.player_height,
                    #         "player_width":event.player_width,
                    #     }
                    # for event in Event.objects.filter(session=session)]
                }
            for session in Session.objects.filter(visitor=visitor)]
        })
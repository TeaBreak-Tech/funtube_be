from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from secrets import token_urlsafe
from django.views.decorators.http import require_http_methods
from .models import *
from django.forms.models import model_to_dict
import datetime
import random
import uuid
import time
import json

TOKEN_LENGTH = 50

def index(request):
    return HttpResponse("Hello, world. You're at the api index.")


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
    desc_col = 2
    video_info_list = []
    #ad_col = 3
    for item in reader:
        if reader.line_num == 1:
            print(item)
            id_col = item.index("id")
            title_col = item.index("title")
            desc_col = item.index("description")
            #ad_col = item.index("ad1")
            continue
        try:
            id = int(item[id_col])
        except: continue
        video_info_list.append({
            "id":id,
            "title":item[title_col],
            "description":item[desc_col],
            #"ad":item[ad_col]
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
            "config":item[config_col],
        })

    # 将视频数据逐个在config中查询，最后取视频文件和视频信息都存在的视频作为最终结果（交集）
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
                #video.cover_url = body_dict.get("cover_url")
                #video.svi_raw = ' '.join([ str(i) for i in body_dict.get("svi_raw")])
                #video.created_time = datetime.datetime.now()
                video.description = video_info["description"]
                #video.ad = video_info["ad"]
                video.save()
                for ad_config_info in ad_config_list:
                    if id==ad_config_info["video_id"]:
                        try: ad_config = AdConfig.objects.get(video = video,config_num = ad_config_info["config_num"])
                        except: ad_config = AdConfig()
                        ad_config.video = video
                        ad_config.config_num = ad_config_info["config_num"]
                        ad_config.config = ad_config_info["config"]
                        ad_config.save()
                print("added video, id =", id,"title =", video.title)
    
    # 加载全部广告信息
    for path,dir_list,file_list in os.walk(r"/home/www/res/ad"):
        #print (file_list)
        for file_name in file_list: 
            #print(os.path.join(path, file_name) )
            id = int(file_name.split(".")[0].replace("ad_",""))
            #print(id)
            ad = Ad()
            ad.ad_id = id
            ad.url = "/ad/"+file_name
            ad.save()

    # 给所有数据库视频抽取封面图
    for video in Video.objects.all():
        video_path = "/home/www/res/video/" + video.url.split("/")[-1]
        #video_capture = cv2.VideoCapture(video_path)
        #success, frame = video_capture.read()
        #save_name = save_path + str(j) + '_' + str(i) + '.jpg'



    return JsonResponse({})

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
        visitor.config_num = visitor.visitor_id%4 + 1
        visitor.token = token
        #visitor.video = video
        visitor.pid = pid
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
            except: return HttpResponse(status=404)
    # 现在确保有了 visitor 对象和 video 对象
    session = Session()
    #session_id = uuid.uuid4()
    #session.session_id = session_id
    session.visitor = visitor
    session.video = video # 给当前 session 赋予同样的 video
    session.pid = pid
    session.player_type = player_type
    session.save()
    print(video,visitor.config_num)
    try:
        ads = AdConfig.objects.get(video=video,config_num=visitor.config_num).config
        print (ads)
    except:
        ads = "[]"
    ads = json.loads(ads)
    for ad_info in ads:
        ad = Ad.objects.get(ad_id=ad_info["ad_id"])
        ad_info.update(url = ad.url)
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
            "created_time": video.created_time,
            "description":video.description,
            "ads":ads,
        } for video in [video] ],
        "config_num":visitor.config_num,
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
        try: visitor = Visitor.objects.get(pk=visitor_id)
        except: return HttpResponse("visitor DNE",status=401)
    event = Event()
    #event_id = uuid.uuid4()
    #event.event_id = event_id
    session_id = body_dict.get("session_id")
    print(session_id)
    try: session = Session.objects.get(pk=session_id)
    except: return HttpResponse("session DNE",status=402)
    event.session = session
    event.label = body_dict.get("label")
    event.description = body_dict.get("description")
    raw_timestamp = body_dict.get("timestamp")
    print(raw_timestamp/1000)
    timestamp = datetime.datetime.fromtimestamp(float(raw_timestamp/1000))
    event.timestamp = timestamp
    event.video_time = float(body_dict.get("video_time"))
    event.volume = float(body_dict.get("volume"))
    event.buffered = int(body_dict.get("buffered"))
    event.playback_rate = float(body_dict.get("playback_rate"))
    event.full_page = bool(body_dict.get("full_page"))
    event.full_screen = bool(body_dict.get("full_screen"))
    event.player_height = int(body_dict.get("player_height"))
    event.player_width = int(body_dict.get("player_width"))
    event.save()
    return HttpResponse("event saved")

@require_http_methods(["GET","POST"])
def get_video_list(request):
    #body_dict = json.loads(request.body.decode('utf-8'))
    #client = body_dict.get("client",0)
    video_list = Video.objects.all()
    print(video_list)
    return JsonResponse({
        "result":[{
            "video_id": video.video_id,
            "title": video.title,
            "url": video.url,
            "cover_url": video.cover_url,
            #"svi_raw": [float(i) for i in video.svi_raw.split(' ')],
            "created_time": video.created_time,
            "description":video.description,
        } for video in video_list ]
    })

@require_http_methods(["GET"])
def get_tagged_video_list(request):
    result = [{
            "tag_id":tag.tag_id,
            "tag_title":tag.tag_title,
            "videos":[{
                "video_id": video_tag.video.video_id,
                "title": video_tag.video.title,
                "url": video_tag.video.url,
                "cover_url": video_tag.video.cover_url,
                #"svi_raw": [float(i) for i in video_tag.video.svi_raw.split(' ')],
                "created_time": video_tag.video.created_time,
                "description": video_tag.video.description,
            }for video_tag in Video_tag.objects.all() ]
        }for tag in list(Tag.objects.all())] 
    
    # 没有任何分类的视频单分一类
    no_tag_videos = []
    for video in Video.objects.all():
        tags = Video_tag.objects.filter(video=video)
        if len(tags) == 0:
            no_tag_videos.append(video)
    no_tag_videos_info = [{
        "video_id": video.video_id,
        "title": video.title,
        "url": video.url,
        "cover_url": video.cover_url,
        #"svi_raw": [float(i) for i in video_tag.video.svi_raw.split(' ')],
        "created_time": video.created_time,
        "description": video.description,
    }for video in no_tag_videos ]

    if len(no_tag_videos_info)>0:
        result.append({
            "tag_id":"none",
            "tag_title":"未分类",
            "videos":no_tag_videos_info,
        })

    return JsonResponse({
        "result":result
    })

@require_http_methods(["GET"])
def get_video_by_tag(request,tag_title):
    return JsonResponse({
        "videos":[{
            "video_id": video_tag.video.video_id,
            "title": video_tag.video.title,
            "url": video_tag.video.url,
            "cover_url": video_tag.video.cover_url,
            "svi_raw": [float(i) for i in video_tag.video.svi_raw.split(' ')],
            "created_time": video_tag.video.created_time,
            "description": video_tag.video.description,
        }for video_tag in list( filter( lambda video_tag:video_tag.tag.tag_title==tag_title, list(Video_tag.objects.all()) ) )]
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


from django.db import models
from itertools import chain

class PrintableModel(models.Model):
    def __repr__(self):
        return str(self.to_dict())

    def to_dict(instance):
        opts = instance._meta
        data = {}
        for f in chain(opts.concrete_fields, opts.private_fields):
            data[f.name] = f.value_from_object(instance)
        for f in opts.many_to_many:
            data[f.name] = [i.id for i in f.value_from_object(instance)]
        return data

    class Meta:
        abstract = True

class Video(PrintableModel):
    video_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=100 )
    url = models.CharField(max_length=200 )
    cover_url = models.CharField(max_length=200 )
    svi_raw = models.TextField()
    created_time = models.DateTimeField(auto_now=True)
    description = models.TextField()
    client = models.IntegerField(default=0) # 0 for webpage, 1 for plugin player
    length = models.FloatField(default=0)
    
class Ad(PrintableModel):
    ad_id = models.IntegerField(primary_key=True)
    src = models.CharField(max_length=200)
    href = models.TextField(null=True)
    brand = models.TextField(null=True)
    product = models.TextField(null=True)
    cb = models.TextField(null=True)
    db = models.TextField(null=True)
    cb_name = models.TextField(null=True)
    db_name = models.TextField(null=True)
    cp_name = models.TextField(null=True)
    dp_name = models.TextField(null=True)


class AdConfig(PrintableModel):
    ad_config_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    config_num = models.IntegerField(default=1)
    config = models.TextField(default="[]")

class Visitor(PrintableModel):
    visitor_id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=100, unique=True)
    created_time = models.DateTimeField(auto_now_add=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    pid = models.CharField(max_length=100, unique=True, null=True)
    #config_num = models.IntegerField(default=1)
    config = models.TextField()
    ads = models.ManyToManyField(Ad)
    ad_to_show = models.ForeignKey(Ad, on_delete=models.SET_NULL, null=True, related_name="current_visitor" )
    ads_candidate = models.ManyToManyField(Ad, related_name="protential_visitor")

class Session(PrintableModel):
    session_id = models.AutoField(primary_key=True)
    visitor = models.ForeignKey(Visitor, on_delete=models.SET_NULL, null=True, db_column="visitor")
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    start_time = models.DateTimeField(auto_now_add=True)
    pid = models.CharField(max_length=100, unique=False, null=True)
    player_type = models.IntegerField(null=True)
    ad_config_num = models.IntegerField(null=True)
    ad_donfig = models.TextField(null=True)
    ads = models.ManyToManyField(Ad)

class Event(PrintableModel):
    event_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, db_column="session")
    label = models.CharField(max_length=30)
    video_info = models.CharField(max_length=30,default=None)
    description = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    video_time = models.DecimalField( max_digits=12, decimal_places=6)
    volume = models.DecimalField( max_digits=3, decimal_places=2)
    buffered = models.IntegerField()
    playback_rate = models.DecimalField( max_digits=3, decimal_places=2)
    full_page = models.BooleanField()
    full_screen = models.BooleanField()
    player_height = models.IntegerField()
    player_width = models.IntegerField()

class Tag(PrintableModel):
    tag_id = models.AutoField(primary_key=True)
    tag_title = models.CharField(max_length=100)

class Video_tag(PrintableModel):
    video_tag_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, db_column="tag")

class Cat(PrintableModel):
    cat_id = models.AutoField(primary_key=True)
    cat_title = models.CharField(max_length=100)

class Video_cat(PrintableModel):
    video_cat_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    cat = models.ForeignKey(Cat, on_delete=models.SET_NULL, null=True, db_column="cat")
    
class Shot(PrintableModel):
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    end_time = models.FloatField()
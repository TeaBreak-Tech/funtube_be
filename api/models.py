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
    video_id = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=100 )
    url = models.CharField(max_length=200 )
    cover_url = models.CharField(max_length=200 )
    svi_raw = models.TextField()
    created_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    client = models.IntegerField()

class Visitor(PrintableModel):
    visitor_id = models.CharField(max_length=100, primary_key=True)
    token = models.CharField(max_length=100, unique=True)
    created_time = models.DateTimeField(auto_now_add=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    pid = models.CharField(max_length=100, unique=True, null=True)

class Session(PrintableModel):
    session_id = models.CharField(max_length=100, primary_key=True)
    visitor = models.ForeignKey(Visitor, on_delete=models.SET_NULL, null=True, db_column="visitor")
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    start_time = models.DateTimeField(auto_now_add=True)
    pid = models.CharField(max_length=100, unique=False, null=True)
    player_type = models.IntegerField(null=True)

class Event(PrintableModel):
    event_id = models.CharField(max_length=100, primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, db_column="session")
    label = models.CharField(max_length=30)
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
    tag_id = models.CharField(max_length=100, primary_key=True)
    tag_title = models.CharField(max_length=100)

class Video_tag(PrintableModel):
    video_tag_id = models.CharField(max_length=100, primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, db_column="video")
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, db_column="tag")
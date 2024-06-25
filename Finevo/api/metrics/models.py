from django.db import models

class Metrics(models.Model):
    cpu = models.FloatField()
    memory = models.FloatField()
    disk_usage = models.FloatField()
    
    read_count = models.IntegerField()
    write_count = models.IntegerField()
    
    read_bytes = models.IntegerField()
    write_bytes = models.IntegerField()
    
    read_time = models.IntegerField()
    write_time = models.IntegerField()
    
    read_merged_count = models.IntegerField()
    write_merged_count = models.IntegerField()
    
    busy_time = models.IntegerField()
    
    bytes_sent = models.IntegerField()
    bytes_recv = models.IntegerField()
    
    packets_sent = models.IntegerField()
    packets_recv = models.IntegerField()
    
    errin = models.IntegerField()
    errout = models.IntegerField()
    
    dropin = models.IntegerField()
    dropout = models.IntegerField()
    
    instance_id = models.CharField(max_length=20)
    instance_type = models.CharField(max_length=25)
    
    public_ipv4 = models.CharField(max_length=15)
    local_ipv4 = models.CharField(max_length=15)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    uuid = models.CharField(max_length=100)

    def __str__(self):
        return self.instance_id
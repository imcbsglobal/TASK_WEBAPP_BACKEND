from django.db import models

class EventLog(models.Model):
    client_id = models.CharField(max_length=50)

    uid = models.CharField(max_length=30)
    edate = models.DateField()
    etime = models.TimeField()
    sevent = models.CharField(max_length=500)

    class Meta:
        db_table = "eventlog"

    def __str__(self):
        return f"{self.uid} - {self.sevent}"

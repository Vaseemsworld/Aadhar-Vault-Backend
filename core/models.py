from django.db import models
from django.conf import settings

class Order(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name='orders', null=True, blank=True)

    orderType = models.CharField(max_length=20, choices=[
        ('mobile', 'Mobile'),
        ('child', 'Child'),
        ('demographics', 'Demographics')
    ], default='mobile')

    # Common fields
    fullName = models.CharField(max_length=30, default="")
    aadhaarNumber = models.CharField(max_length=12, default="")
    mobileNumber = models.CharField(max_length=15, default="")
    fatherName = models.CharField(max_length=30, blank=True,default="")
    fatherAadhaarNumber = models.CharField(max_length=12, default="")
    email = models.EmailField(default="")
    formData = models.JSONField(default=dict)
    dateOfBirth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, choices=[('male','MALE'),('female','FEMALE'),('other','OTHER')], default='male')
    # uploadedFiles = models.JSONField(default=dict)

    village = models.CharField(max_length=100, blank=True, default="")
    post = models.CharField(max_length=100, blank=True, default="")
    landmark = models.CharField(max_length=100, blank=True, default="")
    district = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    pincode = models.CharField(max_length=10, blank=True, default="")

    fingerprints = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.orderType} for {self.fullName}"
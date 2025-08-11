from django.contrib.auth.models import User
from rest_framework import serializers
import json
from .models import Order

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "confirm_password")
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError("Username already exists")
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class OperatorCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User 
        fields = ['username','password']

    def create(self, validated_data):
        user = User(username=validated_data['username'], is_staff=False)
        user.set_password(validated_data['password'])
        user.save()
        return user

class OperatorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username', 'date_joined']
        
class OrderSerializer(serializers.ModelSerializer):
    operator_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']
    

    #common fields
    orderType = serializers.ChoiceField(choices=['mobile','child','demographics'])
    fullName = serializers.CharField(max_length=50)
    aadhaarNumber = serializers.CharField(max_length=12, required=False, allow_blank=True)
    mobileNumber = serializers.CharField(max_length=15)
    fatherName = serializers.CharField(max_length=50, required=False,allow_blank=True)



    #mobile fields
    # email = serializers.EmailField(required=False, allow_blank=True)
    # purpose = serializers.CharField(max_length=100, required=False, allow_blank=True)

    #child fields
    # nameInHindi = serializers.CharField(max_length=50, required=False, allow_blank=True)
    dateOfBirth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'], required=False, allow_blank=True)
    # fatherNameInHindi = serializers.CharField(max_length=50, required=False, allow_blank=True)
    fatherAadhaarNumber = serializers.CharField(max_length=12, required=False, allow_blank=True)
    village = serializers.CharField(max_length=100, required=False, allow_blank=True)
    post = serializers.CharField(max_length=100, required=False, allow_blank=True)
    landmark = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length=10, required=False, allow_blank=True)

    # birthCertificate = serializers.FileField(required=False, allow_empty_file=True)
    # childPhoto = serializers.FileField(required=False, allow_empty_file=True)
    # addressProof = serializers.FileField(required=False, allow_empty_file=True)
    
    #demographics fields
    # document = serializers.FileField(required=False, allow_empty_file=True)
    
    fingerprints = serializers.CharField(required=False, allow_blank=True)

    def validate_fingerprints(self, data):
        if data:
            try:
                fingerprints = json.loads(data)
                return fingerprints
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid fingerprints data")
        return {}
    
    def validate(self, data):
        order_type = data.get('orderType')
        
        if order_type == 'mobile':
            required_fields = ['fullName', 'aadhaarNumber', 'mobileNumber']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(f"{field} is required for mobile/email updates")
        elif order_type in ['child', 'demographics']:
            required_fields = ['fullName','dateOfBirth', 'gender', 'village', 'post', 'district', 'state', 'pincode']
            if order_type == 'child':
                required_fields.append('fatherAadhaarNumber')
            else:
                required_fields.append('aadhaarNumber')

            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(f"{field} is required for {order_type} updates")
            
            fingerprints = data.get('fingerprints', {})
            if not fingerprints or not any(fingerprints.values()):
                raise serializers.ValidationError("Fingerprints must be a valid file.")
        return data
    





from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions,generics
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from django.contrib.auth.models import User
from .serializers import LoginSerializer,RegisterSerializer, OrderSerializer, OperatorCreateSerializer, OperatorListSerializer
import os
from django.core.files.storage import default_storage


from .models import Order
from datetime import date

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'message': 'CSRF cookie set'}, status=status.HTTP_200_OK)

class UserView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return Response({"username": request.user.username,"is_staff": request.user.is_staff})
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
class OperatorCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = OperatorCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
class OperatorListView(generics.ListAPIView):
    queryset = User.objects.filter(is_staff=False)
    serializer_class = OperatorListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_staff:
    #         return User.objects.all()
    #     else:
    #         return User.objects.filter(created_by=user)
        
    # def perform_create(self, serializer):
    #     serializer.save(created_by=self.request.user)
    
class OperatorDeleteView(generics.DestroyAPIView):
    queryset = User.objects.filter(is_staff=False)
    serializer_class = OperatorListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )

        if user is not None:
            login(request, user)
            return Response({"message": f"Welcome, {user.username}"})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logged out"})

class OrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    
    def get(self, request):
        orderType = request.query_params.get('type', None)

        if request.user.is_staff:
            orders = Order.objects.all()
        else:
            orders = Order.objects.filter(created_by=request.user)
        
        if orderType:
            orders = orders.filter(orderType=orderType)
        # else:
        #     orders = Order.objects.all()
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save(created_by=request.user)
            validated_data = serializer.validated_data

            orderType = validated_data['orderType']
            
            def make_json_serializable(data):
                for key, value in data.items():
                    if isinstance(value, date):
                        data[key] = value.isoformat()  # "YYYY-MM-DD"
                return data
            
            validated_data_serializable = make_json_serializable(dict(validated_data))
            
            try:
                # uploaded_files = {}
                # fileFields = ['birthCertificate', 'childPhoto', 'addressProof', 'document']
                # for field in fileFields:
                #     if field in request.FILES:
                #         file = request.FILES[field]
                #         filePath = self.saveUploadedFile(file, orderType,validated_data['fullName'])
                #         uploaded_files[field] = filePath
                fingerprints = validated_data.get('fingerprints', {})

                order_fields = {
                'orderType': orderType,
                'fullName': validated_data.get('fullName', ''),
                'aadhaarNumber': validated_data.get('aadhaarNumber', ''),
                'mobileNumber': validated_data.get('mobileNumber', ''),
                'fatherName': validated_data.get('fatherName', ''),
                'gender': validated_data.get('gender', ''),
                'formData': validated_data_serializable,
                'fingerprints': fingerprints
                }

                if validated_data.get('dateOfBirth'):
                    order_fields['dateOfBirth'] = validated_data['dateOfBirth']

                # order = Order.objects.create(**order_fields)

                response_data = {
                    'message': 'Order submitted successfully',
                    'application_id': f"APP_{orderType.upper()}_{hash(validated_data['fullName'])}",
                    'order_type': orderType,
                    'formData': validated_data,
                    # 'files_uploaded': list(uploaded_files.keys()),
                    'fingerprints_received': list(fingerprints.keys()) if fingerprints else []
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"Failed to process data": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def saveUploadedFile(self, file, orderType, fullName):
        upload_dir = f'aadhaar_vault/{orderType}/{fullName.replace(" ", "_")}'
        filename = f"{file.name}"
        file_path = os.path.join(upload_dir, filename)

        saved_path = default_storage.save(file_path, file)
        return saved_path
    

    def delete(self, request, *args,**kwargs):
        pk = kwargs.get("pk")
        if not pk:
            return Response({'error':'order id not provided'}, status=400)
        try:
            order = Order.objects.get(pk=pk)
            if not request.user.is_staff and order.created_by != request.user:
                return Response({"error":'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
            order.delete()
            return Response({'message':'Order Deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            return Response({'error':f'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}") 
            return Response({'error': f'An internal server error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


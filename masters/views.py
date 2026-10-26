from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import FirmMaster, GroupMaster, LedgerMaster, GroupCategory
from .serializers import (
    FirmMasterSerializer,
    GroupMasterSerializer,
    LedgerMasterSerializer
)
from .signals import SyncGuard


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class DashboardAPIView(APIView):
    """
    APIView that renders the interactive accounts master dashboard.
    """
    def get(self, request):
        return render(request, 'masters/dashboard.html')


class FirmMasterListCreateAPIView(APIView):
    """
    APIView for Firm Master list and create.
    GET /api/firms/ - Supports ?search=...
    POST /api/firms/ - Create a new Firm Master
    """
    def get(self, request):
        queryset = FirmMaster.objects.all().order_by('firm_code')
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(firm_code__icontains=search) | Q(firm_name__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = FirmMasterSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = FirmMasterSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FirmMasterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FirmMasterDetailAPIView(APIView):
    """
    APIView for Firm Master retrieve, update, partial update, and delete.
    GET /api/firms/<pk>/
    PUT /api/firms/<pk>/
    PATCH /api/firms/<pk>/
    DELETE /api/firms/<pk>/
    """
    def get_object(self, pk):
        return get_object_or_404(FirmMaster, firm_code=pk)

    def get(self, request, pk):
        firm = self.get_object(pk)
        serializer = FirmMasterSerializer(firm)
        return Response(serializer.data)

    def _update_firm(self, firm, data, partial=False):
        new_code = data.get('FirmCode') or data.get('firm_code')
        if new_code:
            new_code = str(new_code).strip()
            if new_code != firm.firm_code:
                if FirmMaster.objects.filter(firm_code=new_code).exists():
                    return Response({'FirmCode': ['Firm with this code already exists.']}, status=status.HTTP_400_BAD_REQUEST)
                if LedgerMaster.objects.filter(ledger_code=new_code).exclude(ledger_code=firm.firm_code).exists():
                    return Response({'FirmCode': ['Ledger with this code already exists.']}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FirmMasterSerializer(firm, data=data, partial=partial)
        if serializer.is_valid():
            old_code = firm.firm_code
            target_code = serializer.validated_data.get('firm_code', old_code)
            target_name = serializer.validated_data.get('firm_name', firm.firm_name)

            with transaction.atomic():
                with SyncGuard():
                    if target_code != old_code:
                        # 1. Unlink FK reference from ledger before changing FirmMaster PK
                        LedgerMaster.objects.filter(ledger_code=old_code).update(firm=None)
                        # 2. Update FirmMaster PK and name
                        FirmMaster.objects.filter(firm_code=old_code).update(
                            firm_code=target_code,
                            firm_name=target_name
                        )
                        # 3. Update corresponding LedgerMaster PK and relink to updated firm
                        LedgerMaster.objects.filter(ledger_code=old_code).update(
                            ledger_code=target_code,
                            ledger_name=target_name,
                            firm_id=target_code,
                            is_firm_ledger=True
                        )
                        firm = FirmMaster.objects.get(firm_code=target_code)
                    else:
                        firm.firm_name = target_name
                        firm.save()
                        LedgerMaster.objects.filter(ledger_code=old_code).update(
                            ledger_name=target_name
                        )

            return Response(FirmMasterSerializer(firm).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        firm = self.get_object(pk)
        return self._update_firm(firm, request.data, partial=False)

    def patch(self, request, pk):
        firm = self.get_object(pk)
        return self._update_firm(firm, request.data, partial=True)

    def delete(self, request, pk):
        firm = self.get_object(pk)
        firm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupCategoriesAPIView(APIView):
    """
    APIView to return all valid dropdown categories.
    GET /api/groups/categories/
    """
    def get(self, request):
        return Response([choice[0] for choice in GroupCategory.choices])


class GroupMasterListCreateAPIView(APIView):
    """
    APIView for Group Master list and create.
    GET /api/groups/ - Supports ?category=..., ?Super=..., ?search=...
    POST /api/groups/ - Create a new Group Master
    """
    def get(self, request):
        queryset = GroupMaster.objects.select_related('super_group').all().order_by('grp_code')
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category.upper())

        super_code = request.query_params.get('Super')
        if super_code:
            queryset = queryset.filter(super_group__grp_code=super_code)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(grp_name__icontains=search) | Q(grp_code__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = GroupMasterSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = GroupMasterSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = GroupMasterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupMasterDetailAPIView(APIView):
    """
    APIView for Group Master retrieve, update, partial update, and delete.
    GET /api/groups/<pk>/
    PUT /api/groups/<pk>/
    PATCH /api/groups/<pk>/
    DELETE /api/groups/<pk>/
    """
    def get_object(self, pk):
        return get_object_or_404(GroupMaster, grp_code=pk)

    def get(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupMasterSerializer(group)
        return Response(serializer.data)

    def put(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupMasterSerializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupMasterSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        group = self.get_object(pk)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LedgerMasterListCreateAPIView(APIView):
    """
    APIView for Ledger Master list and create.
    GET /api/ledgers/ - Supports ?Grpcode=..., ?category=..., ?FirmCode=..., ?search=...
    POST /api/ledgers/ - Create a new Ledger Master
    """
    def get(self, request):
        queryset = LedgerMaster.objects.select_related('group', 'firm').all().order_by('ledger_code')
        grp_code = request.query_params.get('Grpcode')
        if grp_code:
            queryset = queryset.filter(group__grp_code=grp_code)

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(group__category=category.upper())

        firm_code = request.query_params.get('FirmCode')
        if firm_code:
            queryset = queryset.filter(firm__firm_code=firm_code)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(ledger_code__icontains=search) |
                Q(ledger_name__icontains=search) |
                Q(add1__icontains=search) |
                Q(add2__icontains=search) |
                Q(add3__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = LedgerMasterSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = LedgerMasterSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LedgerMasterSerializer(data=request.data)
        if serializer.is_valid():
            ledger = serializer.save()
            ledger.refresh_from_db()
            return Response(LedgerMasterSerializer(ledger).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LedgerMasterDetailAPIView(APIView):
    """
    APIView for Ledger Master retrieve, update, partial update, and delete.
    GET /api/ledgers/<pk>/
    PUT /api/ledgers/<pk>/
    PATCH /api/ledgers/<pk>/
    DELETE /api/ledgers/<pk>/
    """
    def get_object(self, pk):
        return get_object_or_404(LedgerMaster, ledger_code=pk)

    def get(self, request, pk):
        ledger = self.get_object(pk)
        serializer = LedgerMasterSerializer(ledger)
        return Response(serializer.data)

    def put(self, request, pk):
        ledger = self.get_object(pk)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if ledger.is_firm_ledger:
            # Ledger code and ledger name are locked to firm master values
            data['Ledgercode'] = ledger.ledger_code
            data['LEDGERNAME'] = ledger.ledger_name
        serializer = LedgerMasterSerializer(ledger, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        ledger = self.get_object(pk)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if ledger.is_firm_ledger:
            # Prevent changing ledger_code or ledger_name
            data.pop('Ledgercode', None)
            data.pop('LEDGERNAME', None)
        serializer = LedgerMasterSerializer(ledger, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ledger = self.get_object(pk)
        ledger.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

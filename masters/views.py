from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Q, Max, ProtectedError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import (
    FirmMaster,
    GroupMaster,
    LedgerMaster,
    GroupCategory,
    Transaction,
    VoucherType,
    TransactionType
)
from .serializers import (
    FirmMasterSerializer,
    GroupMasterSerializer,
    LedgerMasterSerializer,
    TransactionSerializer,
    CashReceiptCreateSerializer,
    CashPaymentCreateSerializer,
    BankPaymentCreateSerializer,
    BankReceiptCreateSerializer,
    JournalVoucherCreateSerializer
)


class StandardPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = 'page_size'
    max_page_size = 1000


class DashboardAPIView(APIView):
    """APIView that renders the interactive accounts master dashboard."""
    def get(self, request):
        return render(request, 'masters/dashboard.html', {'active_page': 'dashboard'})


class FirmMasterPageView(APIView):
    """Page view for Firm Master."""
    def get(self, request):
        return render(request, 'masters/firm_master.html', {'active_page': 'firms'})


class GroupMasterPageView(APIView):
    """Page view for Group Master."""
    def get(self, request):
        return render(request, 'masters/group_master.html', {'active_page': 'groups'})


class LedgerMasterPageView(APIView):
    """Page view for Ledger Master."""
    def get(self, request):
        return render(request, 'masters/ledger_master.html', {'active_page': 'ledgers'})


class CashReceiptPageView(APIView):
    """Page view for Cash Receipt (CR)."""
    def get(self, request):
        return render(request, 'masters/cash_receipt.html', {'active_page': 'cash_receipt'})


class CashPaymentPageView(APIView):
    """Page view for Cash Payment (CP)."""
    def get(self, request):
        return render(request, 'masters/cash_payment.html', {'active_page': 'cash_payment'})


class BankPaymentPageView(APIView):
    """Page view for Bank Payment (BP)."""
    def get(self, request):
        return render(request, 'masters/bank_payment.html', {'active_page': 'bank_payment'})


class BankReceiptPageView(APIView):
    """Page view for Bank Receipt (BR)."""
    def get(self, request):
        return render(request, 'masters/bank_receipt.html', {'active_page': 'bank_receipt'})


class JournalVoucherPageView(APIView):
    """Page view for Journal Voucher (JV)."""
    def get(self, request):
        return render(request, 'masters/journal_voucher.html', {'active_page': 'journal_voucher'})


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

        serializer = FirmMasterSerializer(firm, data=data, partial=partial)
        if serializer.is_valid():
            old_code = firm.firm_code
            target_code = serializer.validated_data.get('firm_code', old_code)
            target_name = serializer.validated_data.get('firm_name', firm.firm_name)

            with transaction.atomic():
                if target_code != old_code:
                    FirmMaster.objects.filter(firm_code=old_code).update(
                        firm_code=target_code,
                        firm_name=target_name
                    )
                    firm = FirmMaster.objects.get(firm_code=target_code)
                else:
                    firm.firm_name = target_name
                    firm.save()

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
        try:
            firm.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response({
                'error': f"Cannot delete Firm '{pk}' because it is linked to existing transactions or records. Please delete its transactions first."
            }, status=status.HTTP_400_BAD_REQUEST)


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
        try:
            group.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response({
                'error': f"Cannot delete Group #{pk} because it has associated ledgers or sub-groups. Please reassign or delete them first."
            }, status=status.HTTP_400_BAD_REQUEST)


class LedgerMasterListCreateAPIView(APIView):
    """
    APIView for Ledger Master list and create.
    GET /api/ledgers/ - Supports ?Grpcode=..., ?category=..., ?FirmCode=..., ?search=...
    POST /api/ledgers/ - Create a new Ledger Master
    """
    def get(self, request):
        queryset = LedgerMaster.objects.select_related('group').all().order_by('ledger_code')
        grp_code = request.query_params.get('Grpcode')
        if grp_code:
            queryset = queryset.filter(group__grp_code=grp_code)

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(group__category=category.upper())

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
        serializer = LedgerMasterSerializer(ledger, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        ledger = self.get_object(pk)
        serializer = LedgerMasterSerializer(ledger, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ledger = self.get_object(pk)
        tx_count = Transaction.objects.filter(Q(ledger=ledger) | Q(ref_code=ledger.ledger_code)).count()
        if tx_count > 0:
            return Response({
                'error': f"Cannot delete Ledger '{pk}' ({ledger.ledger_name}) because {tx_count} transaction record(s) exist with this ledger. Please delete the associated vouchers first."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            ledger.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response({
                'error': f"Cannot delete Ledger '{pk}' ({ledger.ledger_name}) because it is referenced in transactions or other records. Please delete associated vouchers first."
            }, status=status.HTTP_400_BAD_REQUEST)


class NextVoucherNumberAPIView(APIView):
    """
    APIView to fetch the next sequential voucher number for a given firm and voucher type.
    GET /api/transactions/next-vch-no/?firm_code=ACC&vch_type=CR
    """
    def get(self, request):
        firm_code = request.query_params.get('firm_code')
        vch_type = request.query_params.get('vch_type', VoucherType.CASH_RECEIPT)
        if not firm_code:
            return Response(
                {'error': 'firm_code query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        max_num = Transaction.objects.filter(
            firm_id=firm_code,
            vch_type=vch_type
        ).aggregate(Max('vch_number'))['vch_number__max'] or 0
        return Response({
            'firm_code': firm_code,
            'vch_type': vch_type,
            'next_vch_number': max_num + 1
        })


class CashReceiptCreateAPIView(APIView):
    """
    APIView to post Cash Receipt (CR) implementing double-entry:
    - Row 1: CONTRA=0, type='C' (Credit) for the selected Ledger
    - Row 2: CONTRA=1, type='D' (Debit) for CASH ledger
    POST /api/transactions/cash-receipt/
    """
    def post(self, request):
        serializer = CashReceiptCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        firm_code = data['firm_code']
        vch_date = data['vch_date']
        ledger_code = data['ledger_code']
        amount = data['amount']
        remarks = data.get('remarks', '').strip()

        with transaction.atomic():
            firm = FirmMaster.objects.select_for_update().get(firm_code=firm_code)

            # Ensure a standard CASH ledger exists so reports calculate balances properly
            cash_ledger = LedgerMaster.objects.filter(ledger_code='CASH').first()
            if not cash_ledger:
                cash_group = GroupMaster.objects.filter(category=GroupCategory.ASSETS).first()
                if not cash_group:
                    cash_group = GroupMaster.objects.create(
                        grp_name='Cash in Hand',
                        category=GroupCategory.ASSETS
                    )
                LedgerMaster.objects.create(
                    ledger_code='CASH',
                    ledger_name='Cash Account',
                    group=cash_group
                )

            # Auto calculate next voucher number
            max_num = Transaction.objects.filter(
                firm=firm,
                vch_type=VoucherType.CASH_RECEIPT
            ).aggregate(Max('vch_number'))['vch_number__max'] or 0
            vch_number = max_num + 1

            # 1. Primary Line (CONTRA = 0, Credit 'C')
            t1 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.CASH_RECEIPT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=ledger_code,
                ref_code='CASH',
                remarks=remarks,
                chq_no=None,
                amount=amount,
                type=TransactionType.CREDIT,
                contra=0
            )

            # 2. Contra Balancing Line (CONTRA = 1, Debit 'D')
            t2 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.CASH_RECEIPT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code='CASH',
                ref_code=ledger_code,
                remarks=remarks,
                chq_no=None,
                amount=amount,
                type=TransactionType.DEBIT,
                contra=1
            )

        return Response({
            'message': f'Cash Receipt #{vch_number} posted successfully.',
            'vch_number': vch_number,
            'firm_code': firm_code,
            'entries': TransactionSerializer([t1, t2], many=True).data
        }, status=status.HTTP_201_CREATED)


class CashPaymentCreateAPIView(APIView):
    """
    APIView to post Cash Payment (CP) implementing double-entry:
    - Row 1: CONTRA=0, type='D' (Debit) for the selected Ledger (Supplier / Party / Expense)
    - Row 2: CONTRA=1, type='C' (Credit) for CASH ledger (Cash going out)
    POST /api/transactions/cash-payment/
    """
    def post(self, request):
        serializer = CashPaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        firm_code = data['firm_code']
        vch_date = data['vch_date']
        ledger_code = data['ledger_code']
        amount = data['amount']
        remarks = data.get('remarks', '').strip()

        with transaction.atomic():
            firm = FirmMaster.objects.select_for_update().get(firm_code=firm_code)

            # Ensure CASH ledger exists
            cash_ledger = LedgerMaster.objects.filter(ledger_code='CASH').first()
            if not cash_ledger:
                cash_group = GroupMaster.objects.filter(category=GroupCategory.ASSETS).first()
                if not cash_group:
                    cash_group = GroupMaster.objects.create(
                        grp_name='Cash in Hand',
                        category=GroupCategory.ASSETS
                    )
                LedgerMaster.objects.create(
                    ledger_code='CASH',
                    ledger_name='Cash Account',
                    group=cash_group
                )

            # Auto calculate next voucher number for CP
            max_num = Transaction.objects.filter(
                firm=firm,
                vch_type=VoucherType.CASH_PAYMENT
            ).aggregate(Max('vch_number'))['vch_number__max'] or 0
            vch_number = max_num + 1

            # 1. Primary Line (CONTRA = 0, Debit 'D') - Party / Expense receiving money
            t1 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.CASH_PAYMENT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=ledger_code,
                ref_code='CASH',
                remarks=remarks,
                chq_no=None,
                amount=amount,
                type=TransactionType.DEBIT,
                contra=0
            )

            # 2. Contra Balancing Line (CONTRA = 1, Credit 'C') - Cash account decreasing
            t2 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.CASH_PAYMENT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code='CASH',
                ref_code=ledger_code,
                remarks=remarks,
                chq_no=None,
                amount=amount,
                type=TransactionType.CREDIT,
                contra=1
            )

        return Response({
            'message': f'Cash Payment #{vch_number} posted successfully.',
            'vch_number': vch_number,
            'firm_code': firm_code,
            'entries': TransactionSerializer([t1, t2], many=True).data
        }, status=status.HTTP_201_CREATED)


class BankPaymentCreateAPIView(APIView):
    """
    APIView to post Bank Payment (BP) implementing double-entry:
    - Row 1: CONTRA=0, type='D' (Debit) for the selected Ledger (Supplier / Party / Expense), ref_code = bank_ledger_code
    - Row 2: CONTRA=1, type='C' (Credit) for the selected Bank Ledger (Money leaving bank), ref_code = ledger_code
    POST /api/transactions/bank-payment/
    """
    def post(self, request):
        serializer = BankPaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        firm_code = data['firm_code']
        vch_date = data['vch_date']
        bank_ledger_code = data['bank_ledger_code']
        ledger_code = data['ledger_code']
        chq_no = data.get('chq_no', '').strip() or None
        amount = data['amount']
        remarks = data.get('remarks', '').strip()

        with transaction.atomic():
            firm = FirmMaster.objects.select_for_update().get(firm_code=firm_code)

            # Auto calculate next voucher number for BP
            max_num = Transaction.objects.filter(
                firm=firm,
                vch_type=VoucherType.BANK_PAYMENT
            ).aggregate(Max('vch_number'))['vch_number__max'] or 0
            vch_number = max_num + 1

            # 1. Primary Line (CONTRA = 0, Debit 'D') - Party / Expense receiving money
            t1 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.BANK_PAYMENT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=ledger_code,
                ref_code=bank_ledger_code,
                remarks=remarks,
                chq_no=chq_no,
                amount=amount,
                type=TransactionType.DEBIT,
                contra=0
            )

            # 2. Contra Balancing Line (CONTRA = 1, Credit 'C') - Bank account decreasing
            t2 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.BANK_PAYMENT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=bank_ledger_code,
                ref_code=ledger_code,
                remarks=remarks,
                chq_no=chq_no,
                amount=amount,
                type=TransactionType.CREDIT,
                contra=1
            )

        return Response({
            'message': f'Bank Payment #{vch_number} posted successfully.',
            'vch_number': vch_number,
            'firm_code': firm_code,
            'entries': TransactionSerializer([t1, t2], many=True).data
        }, status=status.HTTP_201_CREATED)


class BankReceiptCreateAPIView(APIView):
    """
    APIView to post Bank Receipt (BR) implementing double-entry:
    - Row 1: CONTRA=0, type='C' (Credit) for the selected Ledger (Customer / Party / Income), ref_code = bank_ledger_code
    - Row 2: CONTRA=1, type='D' (Debit) for the selected Bank Ledger (Money entering bank), ref_code = ledger_code
    POST /api/transactions/bank-receipt/
    """
    def post(self, request):
        serializer = BankReceiptCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        firm_code = data['firm_code']
        vch_date = data['vch_date']
        bank_ledger_code = data['bank_ledger_code']
        ledger_code = data['ledger_code']
        chq_no = data.get('chq_no', '').strip() or None
        amount = data['amount']
        remarks = data.get('remarks', '').strip()

        with transaction.atomic():
            firm = FirmMaster.objects.select_for_update().get(firm_code=firm_code)

            # Auto calculate next voucher number for BR
            max_num = Transaction.objects.filter(
                firm=firm,
                vch_type=VoucherType.BANK_RECEIPT
            ).aggregate(Max('vch_number'))['vch_number__max'] or 0
            vch_number = max_num + 1

            # 1. Primary Line (CONTRA = 0, Credit 'C') - Customer / Party / Income giving money
            t1 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.BANK_RECEIPT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=ledger_code,
                ref_code=bank_ledger_code,
                remarks=remarks,
                chq_no=chq_no,
                amount=amount,
                type=TransactionType.CREDIT,
                contra=0
            )

            # 2. Contra Balancing Line (CONTRA = 1, Debit 'D') - Bank account increasing
            t2 = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.BANK_RECEIPT,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=bank_ledger_code,
                ref_code=ledger_code,
                remarks=remarks,
                chq_no=chq_no,
                amount=amount,
                type=TransactionType.DEBIT,
                contra=1
            )

        return Response({
            'message': f'Bank Receipt #{vch_number} posted successfully.',
            'vch_number': vch_number,
            'firm_code': firm_code,
            'entries': TransactionSerializer([t1, t2], many=True).data
        }, status=status.HTTP_201_CREATED)


class JournalVoucherCreateAPIView(APIView):
    """
    APIView to post Journal Voucher (JV) implementing single-entry:
    - Exactly 1 row in 'trans' table
    - type='D' (if dr_amount) or type='C' (if cr_amount)
    - contra=0
    POST /api/transactions/journal-voucher/
    """
    def post(self, request):
        serializer = JournalVoucherCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        firm_code = data['firm_code']
        vch_date = data['vch_date']
        ledger_code = data['ledger_code']
        contra_code = data['contra_code']
        dr_amount = data.get('dr_amount')
        cr_amount = data.get('cr_amount')
        remarks = data.get('remarks', '').strip()

        if dr_amount is not None and dr_amount > 0:
            amount = dr_amount
            txn_type = TransactionType.DEBIT
        else:
            amount = cr_amount
            txn_type = TransactionType.CREDIT

        with transaction.atomic():
            firm = FirmMaster.objects.select_for_update().get(firm_code=firm_code)

            # Auto calculate next voucher number for JV
            max_num = Transaction.objects.filter(
                firm=firm,
                vch_type=VoucherType.JOURNAL_VOUCHER
            ).aggregate(Max('vch_number'))['vch_number__max'] or 0
            vch_number = max_num + 1

            t = Transaction.objects.create(
                firm=firm,
                vch_type=VoucherType.JOURNAL_VOUCHER,
                vch_number=vch_number,
                vch_date=vch_date,
                ledger_code=ledger_code,
                ref_code=contra_code,
                remarks=remarks,
                chq_no=None,
                amount=amount,
                type=txn_type,
                contra=0
            )

        return Response({
            'message': f'Journal Voucher #{vch_number} posted successfully.',
            'vch_number': vch_number,
            'firm_code': firm_code,
            'entries': TransactionSerializer([t], many=True).data
        }, status=status.HTTP_201_CREATED)


class TransactionListAPIView(APIView):
    """
    APIView for listing recorded transactions with filtering.
    GET /api/transactions/ - Supports ?firm_code=..., ?vch_type=..., ?vch_number=..., ?search=...
    """
    def get(self, request):
        queryset = Transaction.objects.select_related('firm', 'ledger').all().order_by('-vch_date', '-vch_number', 'contra')

        firm_code = request.query_params.get('firm_code')
        if firm_code:
            queryset = queryset.filter(firm__firm_code=firm_code)

        vch_type = request.query_params.get('vch_type')
        if vch_type:
            queryset = queryset.filter(vch_type=vch_type.upper())

        vch_number = request.query_params.get('vch_number')
        if vch_number:
            queryset = queryset.filter(vch_number=vch_number)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(ledger__ledger_code__icontains=search) |
                Q(ledger__ledger_name__icontains=search) |
                Q(ref_code__icontains=search) |
                Q(remarks__icontains=search) |
                Q(firm__firm_name__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)


class VoucherDetailAPIView(APIView):
    """
    APIView to retrieve, update, or delete an entire voucher (both primary and contra rows) atomically.
    GET /api/transactions/<firm_code>/<vch_type>/<vch_number>/
    PUT /api/transactions/<firm_code>/<vch_type>/<vch_number>/
    DELETE /api/transactions/<firm_code>/<vch_type>/<vch_number>/
    """
    def get(self, request, firm_code, vch_type, vch_number):
        rows = Transaction.objects.filter(
            firm__firm_code=firm_code,
            vch_type=vch_type.upper(),
            vch_number=vch_number
        ).order_by('contra')
        if not rows.exists():
            return Response({'error': 'Voucher not found.'}, status=status.HTTP_404_NOT_FOUND)

        primary = rows.filter(contra=0).first() or rows.first()
        contra = rows.filter(contra=1).first()

        data = {
            'firm_code': firm_code,
            'vch_type': vch_type.upper(),
            'vch_number': vch_number,
            'vch_date': str(primary.vch_date),
            'amount': str(int(primary.amount)) if primary.amount == int(primary.amount) else str(primary.amount),
            'type': primary.type,
            'remarks': primary.remarks or '',
            'chq_no': primary.chq_no or '',
            'ledger_code': primary.ledger_code,
            'ref_code': primary.ref_code,
            'entries': TransactionSerializer(rows, many=True).data
        }
        return Response(data)

    def put(self, request, firm_code, vch_type, vch_number):
        vch_type_upper = vch_type.upper()
        data = request.data
        vch_date = data.get('vch_date')
        amount = data.get('amount')
        ledger_code = data.get('ledger_code')
        remarks = data.get('remarks', '')
        chq_no = data.get('chq_no', '') or None
        bank_ledger_code = data.get('bank_ledger_code')
        contra_code = data.get('contra_code') or data.get('ref_code')
        txn_type_input = data.get('type')
        dr_amount = data.get('dr_amount')
        cr_amount = data.get('cr_amount')

        if not vch_date:
            return Response({'error': 'Voucher date is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if vch_type_upper == 'JV':
            if not ledger_code:
                return Response({'error': 'Ledger is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if not contra_code:
                return Response({'error': 'Contra ledger is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if ledger_code.strip().upper() == contra_code.strip().upper():
                return Response({'error': 'Same ledger account cannot be selected twice.'}, status=status.HTTP_400_BAD_REQUEST)

            if dr_amount is not None and float(dr_amount or 0) > 0:
                amount = dr_amount
                prim_type = TransactionType.DEBIT
            elif cr_amount is not None and float(cr_amount or 0) > 0:
                amount = cr_amount
                prim_type = TransactionType.CREDIT
            elif txn_type_input in ('D', 'C'):
                prim_type = txn_type_input
            else:
                prim_type = TransactionType.DEBIT

            try:
                amt_val = float(amount)
                if amt_val <= 0:
                    return Response({'error': 'A valid positive amount is required.'}, status=status.HTTP_400_BAD_REQUEST)
            except (TypeError, ValueError):
                return Response({'error': 'A valid numeric amount is required.'}, status=status.HTTP_400_BAD_REQUEST)

            prim_ref = contra_code.strip()
            contra_code_val = None
            contra_ref_val = None
            contra_type = None
        else:
            try:
                amt_val = float(amount)
                if amt_val <= 0:
                    return Response({'error': 'A valid positive amount is required.'}, status=status.HTTP_400_BAD_REQUEST)
            except (TypeError, ValueError):
                return Response({'error': 'A valid numeric amount is required.'}, status=status.HTTP_400_BAD_REQUEST)

            if not ledger_code:
                return Response({'error': 'Party ledger is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if vch_type_upper in ('BP', 'BR'):
                if not bank_ledger_code:
                    return Response({'error': 'Bank ledger is required.'}, status=status.HTTP_400_BAD_REQUEST)
                if bank_ledger_code.strip().upper() == ledger_code.strip().upper():
                    return Response({'error': 'Same bank account cannot be selected twice.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            rows = Transaction.objects.select_for_update().filter(
                firm__firm_code=firm_code,
                vch_type=vch_type_upper,
                vch_number=vch_number
            ).order_by('contra')

            if not rows.exists():
                return Response({'error': 'Voucher not found.'}, status=status.HTTP_404_NOT_FOUND)

            primary = rows.filter(contra=0).first()
            contra = rows.filter(contra=1).first()

            if vch_type_upper == 'CR':
                prim_type = TransactionType.CREDIT
                contra_type = TransactionType.DEBIT
                prim_ref = 'CASH'
                contra_code_val = 'CASH'
                contra_ref_val = ledger_code
            elif vch_type_upper == 'CP':
                prim_type = TransactionType.DEBIT
                contra_type = TransactionType.CREDIT
                prim_ref = 'CASH'
                contra_code_val = 'CASH'
                contra_ref_val = ledger_code
            elif vch_type_upper == 'BP':
                prim_type = TransactionType.DEBIT
                contra_type = TransactionType.CREDIT
                prim_ref = bank_ledger_code
                contra_code_val = bank_ledger_code
                contra_ref_val = ledger_code
            elif vch_type_upper == 'BR':
                prim_type = TransactionType.CREDIT
                contra_type = TransactionType.DEBIT
                prim_ref = bank_ledger_code
                contra_code_val = bank_ledger_code
                contra_ref_val = ledger_code
            elif vch_type_upper == 'JV':
                pass
            else:
                return Response({'error': f'Unsupported voucher type {vch_type}.'}, status=status.HTTP_400_BAD_REQUEST)

            if primary:
                primary.vch_date = vch_date
                primary.amount = amount
                primary.ledger_code = ledger_code
                primary.ref_code = prim_ref
                primary.remarks = remarks
                primary.chq_no = chq_no
                primary.type = prim_type
                primary.save()

            if contra and vch_type_upper != 'JV':
                contra.vch_date = vch_date
                contra.amount = amount
                contra.ledger_code = contra_code_val
                contra.ref_code = contra_ref_val
                contra.remarks = remarks
                contra.chq_no = chq_no
                contra.type = contra_type
                contra.save()

        return Response({
            'message': f'Voucher {vch_type_upper} #{vch_number} updated successfully.',
            'vch_number': vch_number,
            'firm_code': firm_code
        }, status=status.HTTP_200_OK)

    def delete(self, request, firm_code, vch_type, vch_number):
        with transaction.atomic():
            rows = Transaction.objects.filter(
                firm__firm_code=firm_code,
                vch_type=vch_type.upper(),
                vch_number=vch_number
            )
            count = rows.count()
            if count == 0:
                return Response({'error': 'Voucher not found.'}, status=status.HTTP_404_NOT_FOUND)
            rows.delete()
        return Response(
            {'message': f'Voucher {vch_type} #{vch_number} ({count} entries) deleted.'},
            status=status.HTTP_200_OK
        )


VoucherDeleteAPIView = VoucherDetailAPIView


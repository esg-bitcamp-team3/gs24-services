from rest_framework import serializers


class FinancialDataResponseBodyoutputSerializer(serializers.Serializer):
    stac_yymm = serializers.CharField(required=False)
    cras = serializers.CharField(required=False)
    fxas = serializers.CharField(required=False)
    total_aset = serializers.CharField(required=False)
    flow_lblt = serializers.CharField(required=False)
    fix_lblt = serializers.CharField(required=False)
    total_lblt = serializers.CharField(required=False)
    cpfn = serializers.CharField(required=False)
    cfp_surp = serializers.CharField(required=False)
    prfi_surp = serializers.CharField(required=False)
    total_cptl = serializers.CharField(required=False)

class FinancialDataResponseBodySerializer(serializers.Serializer):
    rt_cd = serializers.CharField(required=False)
    msg_cd = serializers.CharField(required=False)
    msg1 = serializers.CharField(required=False)
    output = FinancialDataResponseBodyoutputSerializer(many=True, required=False)
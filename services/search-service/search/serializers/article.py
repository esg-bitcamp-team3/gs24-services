from rest_framework import serializers


class ArticleSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    originallink = serializers.URLField()
    link = serializers.URLField()
    description = serializers.CharField()
    pubDate = serializers.DateTimeField()
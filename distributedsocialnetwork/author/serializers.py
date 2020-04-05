# Serializer for Author

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers, fields
from rest_framework.relations import PKOnlyObject
from collections import OrderedDict
from rest_framework.fields import SkipField

from .models import Author


class AuthorSerializer(ModelSerializer):
    id = serializers.CharField(max_length=100)
    host = serializers.CharField(max_length=100)
    url = serializers.CharField(max_length=100)
    github = serializers.URLField(
        max_length=255, required=False, allow_blank=True)
    firstName = serializers.CharField(
        max_length=30, required=False, allow_blank=True, source='first_name')
    lastName = serializers.CharField(
        max_length=150, required=False, allow_blank=True, source="last_name")
    email = serializers.EmailField(
        max_length=255, required=False, allow_blank=True)
    bio = serializers.CharField(
        max_length=160, required=False, allow_blank=True)

    class Meta:
        model = Author
        fields = [
            'id', 'host', 'displayName', 'url', 'github', 'firstName', 'lastName', 'email', 'bio',
        ]

    # following is thanks to users Ali Tou and CubeRZ on StackOverflow: https://stackoverflow.com/a/27016674
    # From Dev Rishi Khare's question: https://stackoverflow.com/q/27015931
    # It ensures we don't render fields with have blank strings, or fields that are set to None. Neat!
    def to_representation(self, instance):
        ret = OrderedDict()
        fields = self._readable_fields
        for field in fields:
            attribute = field.get_attribute(instance)
            if attribute in [None, '']:
                continue
            check_for_none = attribute.pk if isinstance(
                attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Asset(models.Model):
    """
    OER Asset.
    """
    id = models.IntegerField()
    name = models.CharField(max_length=128)
    version = models.CharField(max_length=128)
    description = models.TextField()
    assettype_name = models.CharField(max_length=250)
    assettype_id = models.IntegerField()
    categorization_name = models.CharField(max_length=256)
    
    def __str__(self):
        """
        String for representing the Model object.
        """
        return str(self.id) + ": " + self.name
    
    
    def get_absolute_url(self):
        """
        Returns the url to access a detail record for this book.
        """
        return reverse('asset-detail', args=[str(self.id)])

class AssetType(models.Model):
    """
    OER Asset.
    """
    id = models.IntegerField()
    name = models.CharField(max_length=128)
    version = models.CharField(max_length=128)
    description = models.TextField()
    assettype_name = models.CharField(max_length=250)
    assettype_id = models.IntegerField()
    categorization_name = models.CharField(max_length=256)
    
    def __str__(self):
        """
        String for representing the Model object.
        """
        return str(self.id) + ": " + self.name
    
    
    def get_absolute_url(self):
        """
        Returns the url to access a detail record for this book.
        """
        return reverse('asset-detail', args=[str(self.id)])

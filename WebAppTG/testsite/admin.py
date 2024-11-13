from django.contrib import admin
from .models import *


class UsersAdmin(admin.ModelAdmin):
    list_display = ('TG_Contact', 'registeredDate')
    list_display_links = ('TG_Contact',)
admin.site.register(Users, UsersAdmin)


class PCCNTRAdmin(admin.ModelAdmin):
    list_display = ('PCCNTR_code', 'PCCNTR_name')
    list_display_links = ('PCCNTR_code',)
admin.site.register(PCCNTR, PCCNTRAdmin)


class Users_PCCNTRAdmin(admin.ModelAdmin):
    list_display = ('TG_Contact', 'PCCNTR', 'ExchangePointID')
    list_display_links = ('TG_Contact',)
admin.site.register(Users_PCCNTR, Users_PCCNTRAdmin)


class GenderAdmin(admin.ModelAdmin):
    list_display = ('Gender_code', 'Name_RUS')
    list_display_links = ('Gender_code',)
admin.site.register(Gender, GenderAdmin)

class CitiesAdmin(admin.ModelAdmin):
    list_display = ('City_code', 'Name_RUS')
    list_display_links = ('City_code',)
admin.site.register(Cities, CitiesAdmin)

class CountriesAdmin(admin.ModelAdmin):
    list_display = ('Country_code', 'Name_RUS')
    list_display_links = ('Country_code',)
admin.site.register(Countries, CountriesAdmin)

class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('Currency_code', 'Name_RUS')
    list_display_links = ('Currency_code',)
admin.site.register(Currency, CurrencyAdmin)

class ContactTypeAdmin(admin.ModelAdmin):
    list_display = ('ContactType_code', 'Name_RUS')
    list_display_links = ('ContactType_code',)
admin.site.register(ContactType, ContactTypeAdmin)